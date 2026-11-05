
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
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

    def test_duplicate_billing_period_is_rejected(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/billing/bills/",
            {
                "meter_id": self.meter.pk,
                "previous_reading_id": self.previous_reading.pk,
                "current_reading_id": self.current_reading.pk,
                "due_date": str(timezone.localdate() + timedelta(days=15)),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Bill.objects.count(), 1)

    def test_bill_rejected_when_meter_is_inactive(self):
        self.meter.status = Meter.Status.INACTIVE
        self.meter.save()

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/billing/bills/",
            {
                "meter_id": self.meter.pk,
                "previous_reading_id": self.previous_reading.pk,
                "current_reading_id": self.current_reading.pk,
                "due_date": str(timezone.localdate() + timedelta(days=15)),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Bill.objects.count(), 1)

    def test_bill_rejected_when_reading_is_flagged(self):
        self.current_reading.status = MeterReading.ReadingStatus.FLAGGED
        self.current_reading.save()

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/billing/bills/",
            {
                "meter_id": self.meter.pk,
                "previous_reading_id": self.previous_reading.pk,
                "current_reading_id": self.current_reading.pk,
                "due_date": str(timezone.localdate() + timedelta(days=15)),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Bill.objects.count(), 1)

    def test_bill_rejected_when_intermediate_reading_exists(self):
        intermediate_date = (
            self.previous_reading.reading_date
            + timedelta(minutes=90)
        )

        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("1001"),
            reading_date=intermediate_date,
            source="manual",
            status=MeterReading.ReadingStatus.NORMAL,
            recorded_by=self.admin,
        )

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/billing/bills/",
            {
                "meter_id": self.meter.pk,
                "previous_reading_id": self.previous_reading.pk,
                "current_reading_id": self.current_reading.pk,
                "due_date": str(timezone.localdate() + timedelta(days=15)),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Bill.objects.count(), 1)

    def test_customer_cannot_create_tariff(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            "/api/v1/billing/tariffs/",
            {
                "name": "Unauthorized Tariff",
                "meter_type": "electricity",
                "rate_per_unit": "20.0000",
                "fixed_charge": "30.00",
                "effective_from": str(timezone.localdate()),
                "is_active": True,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_overlapping_active_tariff_is_rejected(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/v1/billing/tariffs/",
            {
                "name": "Overlapping Electricity Tariff",
                "meter_type": "electricity",
                "rate_per_unit": "30.0000",
                "fixed_charge": "40.00",
                "effective_from": str(timezone.localdate()),
                "is_active": True,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Tariff.objects.count(), 1)

    def test_tariff_with_invalid_effective_dates_is_rejected(self):
        self.client.force_authenticate(user=self.admin)

        today = timezone.localdate()

        response = self.client.post(
            "/api/v1/billing/tariffs/",
            {
                "name": "Invalid Date Tariff",
                "meter_type": "water",
                "rate_per_unit": "10.0000",
                "fixed_charge": "20.00",
                "effective_from": str(today),
                "effective_to": str(today - timedelta(days=1)),
                "is_active": True,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Tariff.objects.count(), 1)

    def test_customer_cannot_modify_tariff(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            f"/api/v1/billing/tariffs/{self.tariff.pk}/",
            {"rate_per_unit": "30.0000"},
        )

        self.assertEqual(response.status_code, 403)
        self.tariff.refresh_from_db()
        self.assertEqual(self.tariff.rate_per_unit, Decimal("25.0000"))
