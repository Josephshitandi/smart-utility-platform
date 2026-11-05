
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q

from meters.models import Meter, MeterReading
from .models import Tariff, Bill


MONEY_PLACES = Decimal("0.01")


def get_applicable_tariff(meter_type, period_start, period_end):
    """
    Find exactly one active tariff covering the entire billing period.
    """

    tariffs = Tariff.objects.filter(
        meter_type=meter_type,
        is_active=True,
        effective_from__lte=period_start,
    ).filter(
        Q(effective_to__isnull=True)
        | Q(effective_to__gte=period_end)
    ).order_by("-effective_from", "-created_at")

    matching_tariffs = list(tariffs[:2])

    if not matching_tariffs:
        raise ValidationError(
            "No active tariff covers the entire billing period."
        )

    if len(matching_tariffs) > 1:
        raise ValidationError(
            "Multiple tariffs cover this billing period. "
            "Resolve overlapping tariff dates first."
        )

    return matching_tariffs[0]


def calculate_bill_amount(units_consumed, rate_per_unit, fixed_charge):
    """
    Calculate consumption charges and the final bill amount.
    """

    units_consumed = Decimal(str(units_consumed))
    rate_per_unit = Decimal(str(rate_per_unit))
    fixed_charge = Decimal(str(fixed_charge))

    if units_consumed < 0:
        raise ValidationError(
            "Units consumed cannot be negative."
        )

    if rate_per_unit < 0 or fixed_charge < 0:
        raise ValidationError(
            "Tariff charges cannot be negative."
        )

    subtotal = (
        units_consumed * rate_per_unit
    ).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )

    amount = (
        subtotal + fixed_charge
    ).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )

    return {
        "subtotal": subtotal,
        "amount": amount,
    }


def validate_reading_pair(meter, previous_reading, current_reading):
    """
    Validate that readings belong to the meter, are chronological,
    are not flagged, and are consecutive.
    """

    if (
        previous_reading.meter_id != meter.pk
        or current_reading.meter_id != meter.pk
    ):
        raise ValidationError(
            "Both readings must belong to the specified meter."
        )

    if current_reading.reading_date <= previous_reading.reading_date:
        raise ValidationError(
            "The current reading must be later than the previous reading."
        )

    if current_reading.reading_value < previous_reading.reading_value:
        raise ValidationError(
            "Current reading cannot be lower than the previous reading."
        )

    if (
        previous_reading.status == MeterReading.ReadingStatus.FLAGGED
        or current_reading.status == MeterReading.ReadingStatus.FLAGGED
    ):
        raise ValidationError(
            "Flagged readings must be reviewed before generating a bill."
        )

    # Do not allow intermediate readings to be skipped.
    intermediate_reading_exists = MeterReading.objects.filter(
        meter=meter,
        reading_date__gt=previous_reading.reading_date,
        reading_date__lt=current_reading.reading_date,
    ).exists()

    if intermediate_reading_exists:
        raise ValidationError(
            "These readings are not consecutive. "
            "An intermediate meter reading exists."
        )


def create_bill(
    *,
    meter_id,
    previous_reading_id,
    current_reading_id,
    due_date,
    created_by,
):
    """
    Generate a bill from two consecutive meter readings.

    All financial values are calculated on the server.
    """

    try:
        with transaction.atomic():

            # Lock the meter to serialize billing operations.
            meter = Meter.objects.select_for_update().get(
                pk=meter_id
            )

            if meter.status != Meter.Status.ACTIVE:
                raise ValidationError(
                    "Bills cannot be generated for inactive or faulty meters."
                )

            previous_reading = (
                MeterReading.objects.select_for_update().get(
                    pk=previous_reading_id
                )
            )

            current_reading = (
                MeterReading.objects.select_for_update().get(
                    pk=current_reading_id
                )
            )

            # Validate reading ownership, sequence and status.
            validate_reading_pair(
                meter,
                previous_reading,
                current_reading,
            )

            billing_period_start = previous_reading.reading_date.date()
            billing_period_end = current_reading.reading_date.date()

            if due_date < billing_period_end:
                raise ValidationError(
                    "Bill due date cannot be before the billing period ends."
                )

            # Find the applicable tariff.
            tariff = get_applicable_tariff(
                meter.meter_type,
                billing_period_start,
                billing_period_end,
            )

            # Calculate actual consumption.
            units_consumed = (
                current_reading.reading_value
                - previous_reading.reading_value
            )

            charges = calculate_bill_amount(
                units_consumed,
                tariff.rate_per_unit,
                tariff.fixed_charge,
            )

            # Create the bill with immutable tariff price snapshots.
            bill = Bill.objects.create(
                meter=meter,
                tariff=tariff,
                previous_reading=previous_reading,
                current_reading=current_reading,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                units_consumed=units_consumed,
                rate_per_unit=tariff.rate_per_unit,
                fixed_charge=tariff.fixed_charge,
                subtotal=charges["subtotal"],
                amount=charges["amount"],
                due_date=due_date,
                created_by=created_by,
                status=Bill.Status.PENDING,
            )

            return bill

    except Meter.DoesNotExist:
        raise ValidationError(
            "The specified meter does not exist."
        )

    except MeterReading.DoesNotExist:
        raise ValidationError(
            "One or both specified meter readings do not exist."
        )

    except IntegrityError:
        raise ValidationError(
            "A bill already exists for this meter and billing period."
        )
