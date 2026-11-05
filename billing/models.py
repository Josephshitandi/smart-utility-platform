
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Tariff(models.Model):
    """
    Defines the charges applicable to electricity or water consumption.
    """

    class MeterType(models.TextChoices):
        ELECTRICITY = "electricity", "Electricity"
        WATER = "water", "Water"

    name = models.CharField(max_length=100)

    meter_type = models.CharField(
        max_length=20,
        choices=MeterType.choices,
    )

    rate_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )

    fixed_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tariffs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_from", "name"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(effective_to__isnull=True)
                    | models.Q(effective_to__gte=models.F("effective_from"))
                ),
                name="tariff_valid_effective_dates",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_meter_type_display()})"


class Bill(models.Model):
    """
    Stores a customer's bill for a specific meter and billing period.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    meter = models.ForeignKey(
        "meters.Meter",
        on_delete=models.PROTECT,
        related_name="bills",
    )

    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name="bills",
    )

    previous_reading = models.ForeignKey(
        "meters.MeterReading",
        on_delete=models.PROTECT,
        related_name="bills_as_previous_reading",
    )

    current_reading = models.ForeignKey(
        "meters.MeterReading",
        on_delete=models.PROTECT,
        related_name="bills_as_current_reading",
    )

    billing_period_start = models.DateField()

    billing_period_end = models.DateField()

    units_consumed = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(0)],
    )

    # Snapshot of tariff values at bill creation.
    rate_per_unit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )

    fixed_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_bills",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-billing_period_end", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    billing_period_end__gte=models.F("billing_period_start")
                ),
                name="bill_valid_billing_period",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="bill_amount_non_negative",
            ),
            models.UniqueConstraint(
                fields=["meter", "billing_period_start", "billing_period_end"],
                name="unique_meter_billing_period",
            ),
        ]

    def __str__(self):
        return (
            f"Bill #{self.pk} - {self.meter.meter_number} "
            f"({self.billing_period_start} to {self.billing_period_end})"
        )
