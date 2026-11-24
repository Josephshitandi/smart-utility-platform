from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, models
from django.utils import timezone

from billing.models import Bill
from .models import Payment, LedgerEntry

from .daraja import (
    DarajaError,
    initiate_stk_push,
    normalize_mpesa_phone,
)


ZERO = Decimal("0.00")


def get_bill_outstanding_amount(bill):
    successful_payments = Payment.objects.filter(
        bill=bill,
        status=Payment.Status.SUCCESSFUL,
    ).aggregate(
        total=models.Sum("amount")
    )["total"] or ZERO

    outstanding = bill.amount - successful_payments

    return max(outstanding, ZERO)


def initiate_payment(
    *,
    bill_id,
    customer,
    amount,
    payment_method,
    idempotency_key,
):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValidationError(
            "Payment amount must be greater than zero."
        )

    if not idempotency_key:
        raise ValidationError(
            "An idempotency key is required."
        )

    with transaction.atomic():
        try:
            bill = Bill.objects.select_for_update().get(
                pk=bill_id
            )
        except Bill.DoesNotExist:
            raise ValidationError(
                "The specified bill does not exist."
            )

        if bill.meter.customer_id != customer.pk:
            raise ValidationError(
                "You cannot pay another customer's bill."
            )

        if bill.status != Bill.Status.PENDING:
            raise ValidationError(
                "Only pending bills can receive payments."
            )

        existing_payment = Payment.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        if existing_payment:
            if (
                existing_payment.customer_id != customer.pk
                or existing_payment.bill_id != bill.pk
                or existing_payment.amount != amount
                or existing_payment.payment_method != payment_method
            ):
                raise ValidationError(
                    "This idempotency key has already been used "
                    "for a different payment request."
                )

            return existing_payment

        outstanding = get_bill_outstanding_amount(bill)

        pending_payments = Payment.objects.filter(
            bill=bill,
            status=Payment.Status.PENDING,
        ).aggregate(
            total=models.Sum("amount")
        )["total"] or ZERO

        available_amount = outstanding - pending_payments

        if amount > available_amount:
            raise ValidationError(
                "Payment amount exceeds the available bill balance."
            )

        try:
            return Payment.objects.create(
                bill=bill,
                customer=customer,
                amount=amount,
                payment_method=payment_method,
                idempotency_key=idempotency_key,
                provider="demo",
                status=Payment.Status.PENDING,
            )
        except IntegrityError:
            raise ValidationError(
                "A payment with this idempotency key already exists."
            )


def process_payment_callback(
    *,
    payment_id,
    successful,
    provider_reference,
):
    if not provider_reference:
        raise ValidationError(
            "A provider reference is required."
        )

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                pk=payment_id
            )
        except Payment.DoesNotExist:
            raise ValidationError(
                "The specified payment does not exist."
            )

        if payment.status != Payment.Status.PENDING:
            if (
                payment.status == Payment.Status.SUCCESSFUL
                and payment.provider_reference == provider_reference
                and successful
            ):
                return payment

            raise ValidationError(
                "This payment has already been processed."
            )

        if Payment.objects.filter(
            provider_reference=provider_reference
        ).exclude(pk=payment.pk).exists():
            raise ValidationError(
                "This provider reference has already been used."
            )

        bill = Bill.objects.select_for_update().get(
            pk=payment.bill_id
        )

        payment.provider_reference = provider_reference
        payment.processed_at = timezone.now()

        if not successful:
            payment.status = Payment.Status.FAILED
            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                    "processed_at",
                    "updated_at",
                ]
            )
            return payment

        if bill.status != Bill.Status.PENDING:
            raise ValidationError(
                "This bill is no longer available for payment."
            )

        successful_payments = Payment.objects.filter(
            bill=bill,
            status=Payment.Status.SUCCESSFUL,
        ).exclude(
            pk=payment.pk
        ).aggregate(
            total=models.Sum("amount")
        )["total"] or ZERO

        if successful_payments + payment.amount > bill.amount:
            raise ValidationError(
                "Successful payment would exceed the bill amount."
            )

        payment.status = Payment.Status.SUCCESSFUL

        payment.save(
            update_fields=[
                "status",
                "provider_reference",
                "processed_at",
                "updated_at",
            ]
        )

        LedgerEntry.objects.create(
            payment=payment,
            bill=bill,
            customer=payment.customer,
            entry_type=LedgerEntry.EntryType.PAYMENT_CREDIT,
            amount=payment.amount,
            description=(
                f"Payment received for bill #{bill.pk}"
            ),
        )

        total_paid = successful_payments + payment.amount

        if total_paid >= bill.amount:
            bill.status = Bill.Status.PAID
            bill.save(
                update_fields=["status", "updated_at"]
            )

        return payment


def reconcile_bill(bill):
    """
    Compare successful payments, ledger credits and bill amount.

    This service is read-only. It never modifies financial records.
    """

    # Reload the bill to avoid using stale status or amount data.
    bill = Bill.objects.get(pk=bill.pk)

    successful_payments = Payment.objects.filter(
        bill=bill,
        status=Payment.Status.SUCCESSFUL,
    )

    payment_total = successful_payments.aggregate(
        total=models.Sum("amount")
    )["total"] or ZERO

    ledger_entries = LedgerEntry.objects.filter(
        bill=bill,
        entry_type=LedgerEntry.EntryType.PAYMENT_CREDIT,
    ).select_related("payment")

    ledger_total = ledger_entries.aggregate(
        total=models.Sum("amount")
    )["total"] or ZERO

    successful_payment_count = successful_payments.count()
    ledger_entry_count = ledger_entries.count()

    # Match ledger credits to individual successful payments.
    ledger_by_payment = {}

    for entry in ledger_entries:
        payment_id = entry.payment_id

        if payment_id not in ledger_by_payment:
            ledger_by_payment[payment_id] = {
                "count": 0,
                "total": ZERO,
            }

        ledger_by_payment[payment_id]["count"] += 1
        ledger_by_payment[payment_id]["total"] += entry.amount

    successful_payment_ids = set(
        successful_payments.values_list("id", flat=True)
    )

    ledger_payment_ids = set(ledger_by_payment.keys())

    missing_ledger_payments = sorted(
        successful_payment_ids - ledger_payment_ids
    )

    # Find ledger entries that do not match successful payments.
    unmatched_ledger_entries = []

    for entry in ledger_entries:
        if (
            entry.payment.status != Payment.Status.SUCCESSFUL
            or entry.payment.bill_id != bill.pk
            or entry.payment.customer_id != entry.customer_id
        ):
            unmatched_ledger_entries.append(entry.pk)

    # Detect duplicate ledger credits for a payment.
    duplicate_ledger_payment_ids = sorted(
        payment_id
        for payment_id, data in ledger_by_payment.items()
        if data["count"] > 1
    )

    # Detect amounts that do not match individual payments.
    ledger_payment_mismatch_ids = []

    for payment in successful_payments:
        ledger_data = ledger_by_payment.get(payment.pk)

        if (
            ledger_data is not None
            and ledger_data["total"] != payment.amount
        ):
            ledger_payment_mismatch_ids.append(payment.pk)

    amount_difference = payment_total - ledger_total
    outstanding_amount = bill.amount - payment_total

    issues = []

    if amount_difference != ZERO:
        issues.append(
            "Payment total does not match ledger total."
        )

    if missing_ledger_payments:
        issues.append(
            "One or more successful payments have no ledger entry."
        )

    if unmatched_ledger_entries:
        issues.append(
            "Ledger contains entries without matching successful payments."
        )

    if duplicate_ledger_payment_ids:
        issues.append(
            "Duplicate ledger entries detected."
        )

    if ledger_payment_mismatch_ids:
        issues.append(
            "One or more ledger amounts do not match their payments."
        )

    if payment_total > bill.amount:
        issues.append(
            "Successful payments exceed the bill amount."
        )

    if (
        bill.status == Bill.Status.PAID
        and outstanding_amount > ZERO
    ):
        issues.append(
            "Bill is marked paid but has an outstanding balance."
        )

    if (
        bill.status != Bill.Status.PAID
        and outstanding_amount <= ZERO
    ):
        issues.append(
            "Bill has been fully paid but is not marked paid."
        )

    if outstanding_amount < ZERO:
        outstanding_amount = ZERO

    return {
        "bill_id": bill.pk,
        "bill_amount": bill.amount,
        "successful_payment_count": successful_payment_count,
        "ledger_entry_count": ledger_entry_count,
        "payment_total": payment_total,
        "ledger_total": ledger_total,
        "amount_difference": amount_difference,
        "outstanding_amount": outstanding_amount,
        "missing_ledger_payments": missing_ledger_payments,
        "unmatched_ledger_entry_ids": unmatched_ledger_entries,
        "duplicate_ledger_payment_ids": duplicate_ledger_payment_ids,
        "ledger_payment_mismatch_ids": ledger_payment_mismatch_ids,
        "is_reconciled": not issues,
        "issues": issues,
    }


def reconcile_payments():
    """
    Reconcile all bills that have payment or ledger activity.
    """

    bill_ids = set(
        Payment.objects.filter(
            status=Payment.Status.SUCCESSFUL
        ).values_list("bill_id", flat=True)
    )

    bill_ids.update(
        LedgerEntry.objects.values_list("bill_id", flat=True)
    )

    results = []

    for bill in Bill.objects.filter(
        pk__in=bill_ids
    ).order_by("id"):
        results.append(reconcile_bill(bill))

    return {
        "total_bills_checked": len(results),
        "reconciled_count": sum(
            1 for result in results if result["is_reconciled"]
        ),
        "discrepancy_count": sum(
            1 for result in results if not result["is_reconciled"]
        ),
        "results": results,
    }


def initiate_daraja_payment(
    *,
    bill_id,
    customer,
    amount,
    phone_number,
    idempotency_key,
):
        """
        Create a pending Daraja payment and initiate an M-Pesa STK Push.

        The payment remains pending until its callback and transaction
        verification have been completed.
        """

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Invalid payment amount.")

        if not amount.is_finite() or amount <= ZERO:
            raise ValidationError(
                "Payment amount must be greater than zero."
            )

        if amount != amount.to_integral_value():
            raise ValidationError(
                "M-Pesa payments must use whole Kenya shillings."
            )

        if not idempotency_key:
            raise ValidationError(
                "An idempotency key is required."
            )

        try:
            phone_number = normalize_mpesa_phone(phone_number)
        except DarajaError as exc:
            raise ValidationError(str(exc)) from exc

        # Create and reserve the payment inside a database transaction.
        with transaction.atomic():
            try:
                bill = Bill.objects.select_for_update().get(
                    pk=bill_id
                )
            except Bill.DoesNotExist:
                raise ValidationError(
                    "The specified bill does not exist."
                )

            if bill.meter.customer_id != customer.pk:
                raise ValidationError(
                    "You cannot pay another customer's bill."
                )

            if bill.status != Bill.Status.PENDING:
                raise ValidationError(
                    "Only pending bills can receive payments."
                )

            existing_payment = Payment.objects.filter(
                idempotency_key=idempotency_key
            ).first()

            if existing_payment:
                if (
                    existing_payment.customer_id != customer.pk
                    or existing_payment.bill_id != bill.pk
                    or existing_payment.amount != amount
                    or existing_payment.provider != "daraja"
                    or existing_payment.phone_number != phone_number
                ):
                    raise ValidationError(
                        "This idempotency key has already been used "
                        "for a different payment request."
                    )

                if existing_payment.checkout_request_id:
                    return existing_payment

                raise ValidationError(
                    "This payment request is already being processed. "
                    "Please check its status before retrying."
                )

            outstanding = get_bill_outstanding_amount(bill)

            pending_payments = Payment.objects.filter(
                bill=bill,
                status=Payment.Status.PENDING,
            ).aggregate(
                total=models.Sum("amount")
            )["total"] or ZERO

            available_amount = outstanding - pending_payments

            if amount > available_amount:
                raise ValidationError(
                    "Payment amount exceeds the available bill balance."
                )

            try:
                payment = Payment.objects.create(
                    bill=bill,
                    customer=customer,
                    amount=amount,
                    payment_method=Payment.PaymentMethod.MOBILE_MONEY,
                    provider="daraja",
                    phone_number=phone_number,
                    idempotency_key=idempotency_key,
                    status=Payment.Status.PENDING,
                )
            except IntegrityError as exc:
                raise ValidationError(
                    "A payment with this idempotency key already exists."
                ) from exc

        # Call Safaricom outside the database transaction.
        # A timeout leaves the payment pending because Safaricom
        # may have received the request even if we did not receive
        # its response.
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=f"BILL{bill.pk}",
            transaction_description="Utility payment",
        )

        # Store the identifiers returned by Safaricom.
        payment.merchant_request_id = response["merchant_request_id"]
        payment.checkout_request_id = response["checkout_request_id"]

        payment.save(
            update_fields=[
                "merchant_request_id",
                "checkout_request_id",
                "updated_at",
            ]
        )

        return payment

def process_verified_daraja_payment(
    *,
    checkout_request_id,
    provider_reference,
    amount,
    phone_number,
    result_code="0",
    result_description="Payment completed successfully.",
):
    """
    Finalize a Daraja payment after STK Query confirms success.

    This function:
    - Matches the Safaricom CheckoutRequestID.
    - Validates the receipt, amount and phone number.
    - Prevents duplicate payment processing.
    - Creates exactly one ledger credit.
    - Marks the bill paid when its balance is fully settled.
    """

    if not checkout_request_id:
        raise ValidationError("CheckoutRequestID is required.")

    if not provider_reference:
        raise ValidationError("M-Pesa receipt number is required.")

    if str(result_code) != "0":
        raise ValidationError(
            "Cannot finalize a payment that Daraja has not confirmed."
        )

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("Invalid callback payment amount.") from exc

    if not amount.is_finite() or amount <= ZERO:
        raise ValidationError("Invalid callback payment amount.")

    try:
        phone_number = normalize_mpesa_phone(phone_number)
    except DarajaError as exc:
        raise ValidationError(str(exc)) from exc

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(
                checkout_request_id=checkout_request_id,
                provider="daraja",
            )
        except Payment.DoesNotExist:
            raise ValidationError(
                "No matching Daraja payment was found."
            )

        # Validate callback details against our original request.
        if payment.amount != amount:
            raise ValidationError(
                "Callback amount does not match the initiated payment."
            )

        if payment.phone_number != phone_number:
            raise ValidationError(
                "Callback phone number does not match the initiated payment."
            )

        # Safely handle repeated callbacks.
        if payment.status == Payment.Status.SUCCESSFUL:
            if payment.provider_reference == provider_reference:
                return payment

            raise ValidationError(
                "This payment was already completed with a different receipt."
            )

        if payment.status != Payment.Status.PENDING:
            raise ValidationError(
                "This payment has already been processed."
            )

        if Payment.objects.filter(
            provider_reference=provider_reference
        ).exclude(pk=payment.pk).exists():
            raise ValidationError(
                "This M-Pesa receipt has already been used."
            )

        bill = Bill.objects.select_for_update().get(
            pk=payment.bill_id
        )

        if bill.status != Bill.Status.PENDING:
            raise ValidationError(
                "This bill is no longer available for payment."
            )

        successful_payments = Payment.objects.filter(
            bill=bill,
            status=Payment.Status.SUCCESSFUL,
        ).exclude(
            pk=payment.pk
        ).aggregate(
            total=models.Sum("amount")
        )["total"] or ZERO

        if successful_payments + payment.amount > bill.amount:
            raise ValidationError(
                "Successful payment would exceed the bill amount."
            )

        payment.status = Payment.Status.SUCCESSFUL
        payment.provider_reference = provider_reference
        payment.result_code = str(result_code)
        payment.result_description = result_description
        payment.processed_at = timezone.now()

        payment.save(
            update_fields=[
                "status",
                "provider_reference",
                "result_code",
                "result_description",
                "processed_at",
                "updated_at",
            ]
        )

        LedgerEntry.objects.create(
            payment=payment,
            bill=bill,
            customer=payment.customer,
            entry_type=LedgerEntry.EntryType.PAYMENT_CREDIT,
            amount=payment.amount,
            description=f"M-Pesa payment received for bill #{bill.pk}",
        )

        total_paid = successful_payments + payment.amount

        if total_paid >= bill.amount:
            bill.status = Bill.Status.PAID
            bill.save(
                update_fields=["status", "updated_at"]
            )

        return payment

