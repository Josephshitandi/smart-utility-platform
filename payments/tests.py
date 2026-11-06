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
    reconcile_bill,
    reconcile_payments,
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

    # --------------------------------------------------
    # Helper methods
    # --------------------------------------------------

    def create_payment(self, amount="100.00", key="PAYMENT-001"):
        return initiate_payment(
            bill_id=self.bill.pk,
            customer=self.customer,
            amount=Decimal(amount),
            payment_method=Payment.PaymentMethod.MOBILE_MONEY,
            idempotency_key=key,
        )

    def complete_payment(
        self,
        amount="100.00",
        key="PAYMENT-001",
        reference="DEMO-REF-001",
    ):
        payment = self.create_payment(
            amount=amount,
            key=key,
        )

        return process_payment_callback(
            payment_id=payment.pk,
            successful=True,
            provider_reference=reference,
        )

    def create_second_bill(self):
        now = timezone.now()

        second_meter = Meter.objects.create(
            meter_number="PAY-TEST-002",
            meter_type="electricity",
            customer=self.customer,
            status="active",
            installation_date=timezone.localdate() - timedelta(days=10),
        )

        previous_reading = MeterReading.objects.create(
            meter=second_meter,
            reading_value=Decimal("2000"),
            reading_date=now - timedelta(hours=3),
            source="manual",
            status="normal",
            recorded_by=self.admin,
        )

        current_reading = MeterReading.objects.create(
            meter=second_meter,
            reading_value=Decimal("2002"),
            reading_date=now,
            source="manual",
            status="normal",
            recorded_by=self.admin,
        )

        return Bill.objects.create(
            meter=second_meter,
            tariff=self.tariff,
            previous_reading=previous_reading,
            current_reading=current_reading,
            billing_period_start=previous_reading.reading_date.date(),
            billing_period_end=current_reading.reading_date.date(),
            units_consumed=Decimal("2.000"),
            rate_per_unit=Decimal("25.0000"),
            fixed_charge=Decimal("50.00"),
            subtotal=Decimal("50.00"),
            amount=Decimal("100.00"),
            due_date=timezone.localdate() + timedelta(days=15),
            status=Bill.Status.PENDING,
            created_by=self.admin,
        )

    # --------------------------------------------------
    # Payment initiation tests
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Payment callback tests
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Reconciliation tests
    # --------------------------------------------------

    def test_reconcile_bill_with_matching_payment_and_ledger(self):
        self.complete_payment(
            reference="RECON-REF-001",
        )

        result = reconcile_bill(self.bill)

        self.assertTrue(result["is_reconciled"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["payment_total"], Decimal("100.00"))
        self.assertEqual(result["ledger_total"], Decimal("100.00"))
        self.assertEqual(result["amount_difference"], Decimal("0.00"))
        self.assertEqual(result["outstanding_amount"], Decimal("0.00"))

    def test_reconcile_bill_detects_missing_ledger_entry(self):
        payment = self.create_payment()

        # Simulate a successful payment whose ledger entry is missing.
        Payment.objects.filter(pk=payment.pk).update(
            status=Payment.Status.SUCCESSFUL
        )

        Bill.objects.filter(pk=self.bill.pk).update(
            status=Bill.Status.PAID
        )

        result = reconcile_bill(self.bill)

        self.assertFalse(result["is_reconciled"])
        self.assertIn(payment.pk, result["missing_ledger_payments"])

    def test_reconcile_bill_detects_payment_ledger_amount_mismatch(self):
        payment = self.create_payment()

        # Simulate a successful payment.
        Payment.objects.filter(pk=payment.pk).update(
            status=Payment.Status.SUCCESSFUL
        )

        Bill.objects.filter(pk=self.bill.pk).update(
            status=Bill.Status.PAID
        )

        # Simulate an incorrect ledger amount.
        LedgerEntry.objects.create(
            payment=payment,
            bill=self.bill,
            customer=self.customer,
            entry_type=LedgerEntry.EntryType.PAYMENT_CREDIT,
            amount=Decimal("90.00"),
            description="Test reconciliation amount mismatch",
        )

        result = reconcile_bill(self.bill)

        self.assertFalse(result["is_reconciled"])
        self.assertEqual(result["payment_total"], Decimal("100.00"))
        self.assertEqual(result["ledger_total"], Decimal("90.00"))
        self.assertEqual(result["amount_difference"], Decimal("10.00"))

    def test_reconcile_bill_detects_incorrect_bill_status(self):
        self.complete_payment(
            reference="RECON-REF-002",
        )

        # Simulate an incorrect bill status.
        Bill.objects.filter(pk=self.bill.pk).update(
            status=Bill.Status.PENDING
        )

        result = reconcile_bill(self.bill)

        self.assertFalse(result["is_reconciled"])
        self.assertGreater(
            result["outstanding_amount"],
            Decimal("0.00"),
        )
        self.assertTrue(result["issues"])

    def test_reconcile_payments_checks_multiple_bills(self):
        # Complete payment for the first bill.
        self.complete_payment(
            reference="RECON-REF-003",
        )

        # Create and pay a second bill.
        second_bill = self.create_second_bill()

        second_payment = initiate_payment(
            bill_id=second_bill.pk,
            customer=self.customer,
            amount=Decimal("100.00"),
            payment_method=Payment.PaymentMethod.MOBILE_MONEY,
            idempotency_key="RECON-PAYMENT-002",
        )

        process_payment_callback(
            payment_id=second_payment.pk,
            successful=True,
            provider_reference="RECON-REF-004",
        )

        result = reconcile_payments()

        self.assertEqual(result["total_bills_checked"], 2)
        self.assertEqual(result["reconciled_count"], 2)
        self.assertEqual(result["discrepancy_count"], 0)