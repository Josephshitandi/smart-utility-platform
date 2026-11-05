
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from meters.models import Meter, MeterReading
from billing.models import Bill, Tariff
from .models import Payment, LedgerEntry
from .services import (
    initiate_payment,
    process_payment_callback,
)


class PaymentServiceTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="paymentcustomer",
            email="paymentcustomer@example.com",
            password="TestPassword123!",
            role="customer",
        )

        self.admin = User.objects.create_superuser(
            username="paymentadmin",
            email="paymentadmin@example.com",
            password="TestPassword123!",
        )

        self.meter = Meter.objects.create(
            meter_number="PAY-TEST-001",
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
            name="Payment Test Tariff",
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
            status=Bill.Status.PENDING,
            created_by=self.admin,
        )

    def create_payment(self, amount="100.00", key="PAYMENT-001"):
        return initiate_payment(
            bill_id=self.bill.pk,
            customer=self.customer,
            amount=Decimal(amount),
            payment_method=Payment.PaymentMethod.MOBILE_MONEY,
            idempotency_key=key,
        )

    def test_customer_can_initiate_payment(self):
        payment = self.create_payment()

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, Decimal("100.00"))

    def test_duplicate_idempotency_key_returns_existing_payment(self):
        first = self.create_payment()
        second = self.create_payment()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Payment.objects.count(), 1)

    def test_same_idempotency_key_cannot_be_reused_with_different_amount(self):
        self.create_payment()

        with self.assertRaises(ValidationError):
            self.create_payment(amount="50.00")

    def test_customer_cannot_pay_another_customers_bill(self):
        another_customer = User.objects.create_user(
            username="anothercustomer",
            email="anothercustomer@example.com",
            password="TestPassword123!",
            role="customer",
        )

        with self.assertRaises(ValidationError):
            initiate_payment(
                bill_id=self.bill.pk,
                customer=another_customer,
                amount=Decimal("100.00"),
                payment_method=Payment.PaymentMethod.MOBILE_MONEY,
                idempotency_key="UNAUTHORIZED-001",
            )

    def test_payment_cannot_exceed_bill_amount(self):
        with self.assertRaises(ValidationError):
            self.create_payment(amount="150.00")

    def test_successful_callback_creates_ledger_entry(self):
        payment = self.create_payment()

        processed = process_payment_callback(
            payment_id=payment.pk,
            successful=True,
            provider_reference="DEMO-REF-001",
        )

        self.assertEqual(processed.status, Payment.Status.SUCCESSFUL)
        self.assertEqual(LedgerEntry.objects.count(), 1)

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PAID)

    def test_repeated_successful_callback_does_not_duplicate_ledger(self):
        payment = self.create_payment()

        process_payment_callback(
            payment_id=payment.pk,
            successful=True,
            provider_reference="DEMO-REF-002",
        )

        process_payment_callback(
            payment_id=payment.pk,
            successful=True,
            provider_reference="DEMO-REF-002",
        )

        self.assertEqual(LedgerEntry.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)

    def test_failed_callback_does_not_create_ledger_entry(self):
        payment = self.create_payment()

        processed = process_payment_callback(
            payment_id=payment.pk,
            successful=False,
            provider_reference="DEMO-REF-003",
        )

        self.assertEqual(processed.status, Payment.Status.FAILED)
        self.assertEqual(LedgerEntry.objects.count(), 0)

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PENDING)

    def test_partial_payment_does_not_mark_bill_as_paid(self):
        payment = self.create_payment(amount="40.00")

        process_payment_callback(
            payment_id=payment.pk,
            successful=True,
            provider_reference="DEMO-REF-004",
        )

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PENDING)

    def test_second_payment_completes_bill(self):
        first = self.create_payment(
            amount="40.00",
            key="PARTIAL-001",
        )

        process_payment_callback(
            payment_id=first.pk,
            successful=True,
            provider_reference="DEMO-REF-005",
        )

        second = self.create_payment(
            amount="60.00",
            key="PARTIAL-002",
        )

        process_payment_callback(
            payment_id=second.pk,
            successful=True,
            provider_reference="DEMO-REF-006",
        )

        self.bill.refresh_from_db()
        self.assertEqual(self.bill.status, Bill.Status.PAID)
        self.assertEqual(LedgerEntry.objects.count(), 2)
