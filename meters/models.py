
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
