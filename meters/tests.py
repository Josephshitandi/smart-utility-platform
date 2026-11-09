from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from meters.models import Meter, MeterReading
from meters.services import (
    calculate_consumption,
    is_abnormal_consumption,
)


User = get_user_model()


class MeterConsumptionServiceTests(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="testcustomer",
            email="customer@example.com",
            password="TestPassword123!",
        )

        self.meter = Meter.objects.create(
            meter_number="TEST-METER-001",
            meter_type=Meter.MeterType.ELECTRICITY,
            customer=self.customer,
            status=Meter.Status.ACTIVE,
            installation_date=timezone.localdate() - timedelta(days=30),
        )

        self.previous_reading_date = timezone.now() - timedelta(days=1)

        self.previous_reading = MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("100.000"),
            reading_date=self.previous_reading_date,
            source=MeterReading.ReadingSource.MANUAL,
            recorded_by=self.customer,
        )

    def test_calculates_consumption_correctly(self):
        new_reading = MeterReading(
            meter=self.meter,
            reading_value=Decimal("120.000"),
            reading_date=timezone.now(),
        )

        result = calculate_consumption(new_reading)

        self.assertIsNotNone(result)
        self.assertEqual(
            result["consumption"],
            Decimal("20.000"),
        )

    def test_first_reading_has_no_consumption(self):
        new_meter = Meter.objects.create(
            meter_number="TEST-METER-002",
            meter_type=Meter.MeterType.ELECTRICITY,
            customer=self.customer,
            status=Meter.Status.ACTIVE,
            installation_date=timezone.localdate() - timedelta(days=5),
        )

        first_reading = MeterReading(
            meter=new_meter,
            reading_value=Decimal("50.000"),
            reading_date=timezone.now(),
        )

        result = calculate_consumption(first_reading)

        self.assertIsNone(result)

    @override_settings(
        METER_CONSUMPTION_THRESHOLDS={
            "electricity": "50",
            "water": "2",
        }
    )
    def test_detects_abnormal_electricity_consumption(self):
        new_reading = MeterReading(
            meter=self.meter,
            reading_value=Decimal("160.000"),
            reading_date=timezone.now(),
        )

        result = is_abnormal_consumption(new_reading)

        self.assertTrue(result)

    @override_settings(
        METER_CONSUMPTION_THRESHOLDS={
            "electricity": "50",
            "water": "2",
        }
    )
    def test_normal_consumption_is_not_flagged(self):
        new_reading = MeterReading(
            meter=self.meter,
            reading_value=Decimal("110.000"),
            reading_date=timezone.now(),
        )

        result = is_abnormal_consumption(new_reading)

        self.assertFalse(result)

class MeterReadingAPITests(APITestCase):

    def setUp(self):
        self.technician = User.objects.create_user(
            username="technician",
            email="technician@example.com",
            password="TestPassword123!",
            role=User.Role.TECHNICIAN,
        )

        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="TestPassword123!",
        )

        self.other_customer = User.objects.create_user(
            username="othercustomer",
            email="other@example.com",
            password="TestPassword123!",
        )

        self.meter = Meter.objects.create(
            meter_number="API-METER-001",
            meter_type=Meter.MeterType.ELECTRICITY,
            customer=self.customer,
            status=Meter.Status.ACTIVE,
            installation_date=timezone.localdate() - timedelta(days=30),
        )

        self.other_meter = Meter.objects.create(
            meter_number="API-METER-002",
            meter_type=Meter.MeterType.ELECTRICITY,
            customer=self.other_customer,
            status=Meter.Status.ACTIVE,
            installation_date=timezone.localdate() - timedelta(days=30),
        )

        self.url = reverse("reading-list-create")

    def test_technician_can_submit_reading(self):
        self.client.force_authenticate(user=self.technician)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "100.000",
                "reading_date": timezone.now().isoformat(),
                "notes": "Routine meter reading",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_customer_cannot_submit_reading(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "100.000",
                "reading_date": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_only_sees_own_readings(self):
        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("100.000"),
            reading_date=timezone.now() - timedelta(hours=1),
            recorded_by=self.technician,
        )

        MeterReading.objects.create(
            meter=self.other_meter,
            reading_value=Decimal("200.000"),
            reading_date=timezone.now() - timedelta(hours=1),
            recorded_by=self.technician,
        )

        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        self.assertEqual(
            response.data["results"][0]["meter"],
            self.meter.id,
        )

    def test_inactive_meter_rejects_reading(self):
        self.meter.status = Meter.Status.INACTIVE
        self.meter.save()

        self.client.force_authenticate(user=self.technician)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "100.000",
                "reading_date": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_reading_is_rejected(self):
        reading_date = timezone.now() - timedelta(hours=1)

        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("100.000"),
            reading_date=reading_date,
            recorded_by=self.technician,
        )

        self.client.force_authenticate(user=self.technician)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "110.000",
                "reading_date": reading_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reading_cannot_be_lower_than_previous_reading(self):
        previous_date = timezone.now() - timedelta(days=2)

        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("150.000"),
            reading_date=previous_date,
            recorded_by=self.technician,
        )

        self.client.force_authenticate(user=self.technician)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "120.000",
                "reading_date": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_historical_reading_cannot_exceed_next_reading(self):
        future_date = timezone.now() - timedelta(days=1)

        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("150.000"),
            reading_date=future_date,
            recorded_by=self.technician,
        )

        self.client.force_authenticate(user=self.technician)

        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "180.000",
                "reading_date": (
                    timezone.now() - timedelta(days=2)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @override_settings(
    METER_CONSUMPTION_THRESHOLDS={
        "electricity": "50",
        "water": "2",
    }
    )

    def test_historical_reading_recalculates_next_reading_status(self):
        first_date = timezone.now() - timedelta(days=4)
        second_date = timezone.now() - timedelta(days=2)

        # Existing first reading.
        MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("100.000"),
            reading_date=first_date,
            recorded_by=self.technician,
        )

        # Existing second reading.
        next_reading = MeterReading.objects.create(
            meter=self.meter,
            reading_value=Decimal("160.000"),
            reading_date=second_date,
            recorded_by=self.technician,
            status=MeterReading.ReadingStatus.FLAGGED,
        )

        self.client.force_authenticate(user=self.technician)

        # Insert a historical reading between the two.
        response = self.client.post(
            self.url,
            {
                "meter": self.meter.id,
                "reading_value": "150.000",
                "reading_date": (
                    timezone.now() - timedelta(days=3)
                ).isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        next_reading.refresh_from_db()

        self.assertEqual(
            next_reading.status,
            MeterReading.ReadingStatus.NORMAL,
        )

    
