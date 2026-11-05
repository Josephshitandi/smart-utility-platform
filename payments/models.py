
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Payment(models.Model):

    class PaymentMethod(models.TextChoices):
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        CARD = "card", "Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CASH = "cash", "Cash"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    bill = models.ForeignKey(
        "billing.Bill",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MOBILE_MONEY,
    )

    provider = models.CharField(
        max_length=50,
        default="demo",
    )

    provider_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    initiated_at = models.DateTimeField(auto_now_add=True)

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-initiated_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["customer", "status"],
                name="payment_customer_status_idx",
            ),
            models.Index(
                fields=["bill", "status"],
                name="payment_bill_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Payment #{self.pk} - "
            f"{self.amount} - {self.status}"
        )


class LedgerEntry(models.Model):

    class EntryType(models.TextChoices):
        PAYMENT_CREDIT = "payment_credit", "Payment Credit"
        REFUND_DEBIT = "refund_debit", "Refund Debit"

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )

    bill = models.ForeignKey(
        "billing.Bill",
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )

    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="ledger_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["payment", "entry_type"],
                name="unique_payment_ledger_entry_type",
            ),
        ]
        indexes = [
            models.Index(
                fields=["customer", "created_at"],
                name="ledger_customer_date_idx",
            ),
            models.Index(
                fields=["bill", "created_at"],
                name="ledger_bill_date_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and LedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValidationError(
                "Ledger entries are immutable and cannot be modified."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Ledger entries cannot be deleted."
        )

    def __str__(self):
        return (
            f"{self.get_entry_type_display()} - "
            f"{self.amount} - Payment #{self.payment_id}"
        )
