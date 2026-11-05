from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, models
from django.utils import timezone

from billing.models import Bill
from .models import Payment, LedgerEntry


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
    )

    ledger_total = ledger_entries.aggregate(
        total=models.Sum("amount")
    )["total"] or ZERO

    successful_payment_count = successful_payments.count()
    ledger_entry_count = ledger_entries.count()

    missing_ledger_entries = successful_payment_count - ledger_entry_count

    missing_ledger_payments = successful_payments.exclude(
        ledger_entries__entry_type=LedgerEntry.EntryType.PAYMENT_CREDIT
    )

    unmatched_ledger_entries = ledger_entries.exclude(
        payment__status=Payment.Status.SUCCESSFUL
    )

    duplicate_ledger_payments = (
        ledger_entries.values("payment_id")
        .annotate(entry_count=models.Count("id"))
        .filter(entry_count__gt=1)
    )

    amount_difference = payment_total - ledger_total
    outstanding_amount = bill.amount - payment_total

    issues = []

    if amount_difference != ZERO:
        issues.append("Payment total does not match ledger total.")

    if missing_ledger_entries > 0:
        issues.append("One or more successful payments have no ledger entry.")

    if unmatched_ledger_entries.exists():
        issues.append("Ledger contains entries without successful payments.")

    if duplicate_ledger_payments.exists():
        issues.append("Duplicate ledger entries detected.")

    if payment_total > bill.amount:
        issues.append("Successful payments exceed the bill amount.")

    if bill.status == Bill.Status.PAID and outstanding_amount > ZERO:
        issues.append("Bill is marked paid but has an outstanding balance.")

    if bill.status != Bill.Status.PAID and outstanding_amount <= ZERO:
        issues.append("Bill has been fully paid but is not marked paid.")

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
        "missing_ledger_payments": list(
            missing_ledger_payments.values_list("id", flat=True)
        ),
        "unmatched_ledger_entry_ids": list(
            unmatched_ledger_entries.values_list("id", flat=True)
        ),
        "duplicate_ledger_payment_ids": [
            item["payment_id"]
            for item in duplicate_ledger_payments
        ],
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

    for bill in Bill.objects.filter(pk__in=bill_ids).order_by("id"):
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