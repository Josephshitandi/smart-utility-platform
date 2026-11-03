
from django.conf import settings
from django.db import models


class Meter(models.Model):

    class MeterType(models.TextChoices):
        ELECTRICITY = "electricity", "Electricity"
        WATER = "water", "Water"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        FAULTY = "faulty", "Faulty"

    meter_number = models.CharField(
        max_length=50,
        unique=True,
    )

    meter_type = models.CharField(
        max_length=20,
        choices=MeterType.choices,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="meters",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    installation_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.meter_number


class MeterReading(models.Model):

    class ReadingSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        IOT = "iot", "IoT Device"

    class ReadingStatus(models.TextChoices):
        NORMAL = "normal", "Normal"
        FLAGGED = "flagged", "Flagged"

    meter = models.ForeignKey(
        Meter,
        on_delete=models.PROTECT,
        related_name="readings",
    )

    reading_value = models.DecimalField(
        max_digits=14,
        decimal_places=3,
    )

    reading_date = models.DateTimeField()

    source = models.CharField(
        max_length=20,
        choices=ReadingSource.choices,
        default=ReadingSource.MANUAL,
    )

    status = models.CharField(
        max_length=20,
        choices=ReadingStatus.choices,
        default=ReadingStatus.NORMAL,
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_meter_readings",
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reading_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["meter", "reading_date"],
                name="unique_meter_reading_datetime",
            ),
            models.CheckConstraint(
                condition=models.Q(reading_value__gte=0),
                name="reading_value_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.meter.meter_number} - {self.reading_value}"


    def calculate_consumption(self):
        previous_reading = (
            MeterReading.objects.filter(
                meter=self.meter,
                reading_date__lt=self.reading_date,
            )
            .order_by("-reading_date")
            .first()
        )

        if previous_reading is None:
            return None

        return self.reading_value - previous_reading.reading_value

    def detect_abnormal_consumption(self):
        consumption = self.calculate_consumption()

        if consumption is None:
            return False

        # Initial demonstration threshold.
        # We'll replace this with configurable rules later.
        threshold = 50

        return consumption > threshold



