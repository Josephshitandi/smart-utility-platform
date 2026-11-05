from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from meters.models import Meter, MeterReading
from .models import Tariff, Bill
from .services import calculate_bill_amount


class BillingServiceTests(TestCase):

    def test_calculate_bill_amount(self):
        result = calculate_bill_amount(
            units_consumed=Decimal("2"),
            rate_per_unit=Decimal("25"),
            fixed_charge=Decimal("50"),
        )

        self.assertEqual(result["subtotal"], Decimal("50.00"))
        self.assertEqual(result["amount"], Decimal("100.00"))

    def test_negative_consumption_is_rejected(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            calculate_bill_amount(
                units_consumed=Decimal("-2"),
                rate_per_unit=Decimal("25"),
                fixed_charge=Decimal("50"),
            )


class BillingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            username="billingadmin",
            email="billingadmin@example.com",
            password="TestPassword123!",
        )

        self.customer = User.objects.create_user(
            username="billingcustomer",
            email="billingcustomer@example.com",
            password="TestPassword123!",
            role="customer",
        )

        self.other_customer = User.objects.create_user(
            username="othercustomer",
            email="othercustomer@example.com",
            password="TestPassword123!",
            role="customer",
        )

        self.meter = Meter.objects.create(
            meter_number="TEST-EL-001",
            meter_type="electricity",
            customer=self.customer,
            status="active",
            installation_date=timezone.localdate() - timedelta(days=10),
        )

        now = timezone.now()

        self.previous_reading = MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("1000"),
            reading_date=now - timedelta(hours=3),
            source="manual",
            status="normal",
            recorded_by=self.admin,
        )

        self.current_reading = MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("1002"),
            reading_date=now,
            source="manual",
            status="normal",
            recorded_by=self.admin,
        )

        self.tariff = Tariff.objects.create(
            name="Test Electricity Tariff",
            meter_type="electricity",
            rate_per_unit=Decimal("25.0000"),
            fixed_charge=Decimal("50.00"),
            effective_from=timezone.localdate() - timedelta(days=10),
            is_active=True,
            created_by=self.admin,
        )

        self.bill = Bill.objects.create(
            meter=self.meter,
            tariff=self.tariff,
            previous_reading=self.previous_reading,
            current_reading=self.current_reading,
            billing_period_start=self.previous_reading.reading_date.date(),
            billing_period_end=self.current_reading.reading_date.date(),
            units_consumed=Decimal("2.000"),
            rate_per_unit=Decimal("25.0000"),
            fixed_charge=Decimal("50.00"),
            subtotal=Decimal("50.00"),
            amount=Decimal("100.00"),
            due_date=timezone.localdate() + timedelta(days=15),
            status="pending",
            created_by=self.admin,
        )

    def test_customer_can_view_own_bill(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get("/api/v1/billing/bills/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_customer_cannot_view_another_customers_bill(self):
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get("/api/v1/billing/bills/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_customer_cannot_retrieve_another_customers_bill(self):
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get(
            f"/api/v1/billing/bills/{self.bill.pk}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_administrator_can_view_all_bills(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/v1/billing/bills/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_customer_cannot_create_bill(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/v1/billing/bills/",
            {
                "meter_id": self.meter.pk,
                "previous_reading_id": self.previous_reading.pk,
                "current_reading_id": self.current_reading.pk,
                "due_date": str(timezone.localdate() + timedelta(days=15)),
            },
        )

        self.assertEqual(response.status_code, 403)