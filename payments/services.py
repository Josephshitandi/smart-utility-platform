
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from billing.models import Bill
from .models import Payment, LedgerEntry
from django.db import models


def get_bill_outstanding_amount(bill):
    successful_payments = Payment.objects.filter(
        bill=bill,
        status=Payment.Status.SUCCESSFUL,
    ).aggregate(
        total=models.Sum("amount")
    )["total"] or Decimal("0.00")

    outstanding = bill.amount - successful_payments

    return max(outstanding, Decimal("0.00"))


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
        raise ValidationError("Payment amount must be greater than zero.")

    if not idempotency_key:
        raise ValidationError("An idempotency key is required.")

    with transaction.atomic():
        try:
            bill = Bill.objects.select_for_update().get(
                pk=bill_id
            )
        except Bill.DoesNotExist:
            raise ValidationError("The specified bill does not exist.")

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
        )["total"] or Decimal("0.00")

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
        )["total"] or Decimal("0.00")

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

        total_paid = (
            successful_payments + payment.amount
        )

        if total_paid >= bill.amount:
            bill.status = Bill.Status.PAID
            bill.save(update_fields=["status", "updated_at"])

        return payment
