
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Meter, MeterReading


SECONDS_PER_DAY = Decimal("86400")


def get_previous_reading(reading):
    """
    Retrieve the most recent reading before the supplied reading.
    """
    return (
        MeterReading.objects.filter(
            meter=reading.meter,
            reading_date__lt=reading.reading_date,
        )
        .order_by("-reading_date")
        .first()
    )


def get_next_reading(reading):
    """
    Retrieve the earliest reading after the supplied reading.
    """
    return (
        MeterReading.objects.filter(
            meter=reading.meter,
            reading_date__gt=reading.reading_date,
        )
        .order_by("reading_date")
        .first()
    )


def calculate_consumption(reading):
    """
    Calculate consumption and average daily consumption
    between two consecutive readings.
    """
    previous_reading = get_previous_reading(reading)

    if previous_reading is None:
        return None

    consumption = (
        reading.reading_value - previous_reading.reading_value
    )

    elapsed_seconds = Decimal(
        str(
            (
                reading.reading_date - previous_reading.reading_date
            ).total_seconds()
        )
    )

    if elapsed_seconds <= 0:
        return None

    elapsed_days = elapsed_seconds / SECONDS_PER_DAY
    daily_average = consumption / elapsed_days

    return {
        "consumption": consumption,
        "elapsed_days": elapsed_days,
        "daily_average": daily_average,
    }


def is_abnormal_consumption(reading):
    """
    Compare average daily consumption against the configured
    threshold for the meter type.
    """
    result = calculate_consumption(reading)

    if result is None:
        return False

    thresholds = getattr(
        settings,
        "METER_CONSUMPTION_THRESHOLDS",
        {
            "electricity": "50",
            "water": "2",
        },
    )

    threshold = thresholds.get(reading.meter.meter_type)

    if threshold is None:
        return False

    return result["daily_average"] > Decimal(str(threshold))


def validate_reading_sequence(meter, reading_value, reading_date):
    """
    Validate a reading against the meter's existing reading history.

    This validation is repeated inside the transaction to protect
    against concurrent submissions.
    """
    if meter.status != Meter.Status.ACTIVE:
        raise DjangoValidationError({
            "meter": "Readings can only be recorded for active meters."
        })

    if reading_date.date() < meter.installation_date:
        raise DjangoValidationError({
            "reading_date": "Reading date cannot be before installation."
        })

    if reading_date > timezone.now():
        raise DjangoValidationError({
            "reading_date": "Future readings are not allowed."
        })

    if MeterReading.objects.filter(
        meter=meter,
        reading_date=reading_date,
    ).exists():
        raise DjangoValidationError({
            "reading_date": (
                "A reading already exists for this meter at this time."
            )
        })

    previous_reading = (
        MeterReading.objects.filter(
            meter=meter,
            reading_date__lt=reading_date,
        )
        .order_by("-reading_date")
        .first()
    )

    if (
        previous_reading
        and reading_value < previous_reading.reading_value
    ):
        raise DjangoValidationError({
            "reading_value": (
                "Reading cannot be lower than the previous "
                "recorded reading."
            )
        })

    next_reading = (
        MeterReading.objects.filter(
            meter=meter,
            reading_date__gt=reading_date,
        )
        .order_by("reading_date")
        .first()
    )

    if (
        next_reading
        and reading_value > next_reading.reading_value
    ):
        raise DjangoValidationError({
            "reading_value": (
                "Reading cannot be higher than a later "
                "recorded reading."
            )
        })


def recalculate_reading_status(reading):
    """
    Recalculate and persist the abnormal-consumption status
    of a reading.
    """
    if is_abnormal_consumption(reading):
        new_status = MeterReading.ReadingStatus.FLAGGED
    else:
        new_status = MeterReading.ReadingStatus.NORMAL

    if reading.status != new_status:
        reading.status = new_status
        reading.save(update_fields=["status"])

    return reading


def create_meter_reading(validated_data):
    """
    Create a meter reading safely and recalculate the affected
    consumption intervals.

    The meter row is locked to serialize concurrent submissions
    for the same meter.
    """
    try:
        with transaction.atomic():
            data = validated_data.copy()

            meter = Meter.objects.select_for_update().get(
                pk=data["meter"].pk
            )

            data["meter"] = meter

            validate_reading_sequence(
                meter=meter,
                reading_value=data["reading_value"],
                reading_date=data["reading_date"],
            )

            reading = MeterReading(**data)
            reading.status = MeterReading.ReadingStatus.NORMAL
            reading.save()

            # Inserting a historical reading changes its own
            # consumption interval and the next reading's interval.
            affected_readings = [reading]

            next_reading = get_next_reading(reading)

            if next_reading is not None:
                affected_readings.append(next_reading)

            for affected_reading in affected_readings:
                recalculate_reading_status(affected_reading)

            return reading

    except IntegrityError:
        raise DjangoValidationError({
            "reading_date": (
                "A reading already exists for this meter "
                "at this timestamp."
            )
        })
