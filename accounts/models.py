
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        TECHNICIAN = "technician", "Technician"
        SUPPORT = "support", "Support"

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    def __str__(self):
        return self.username
