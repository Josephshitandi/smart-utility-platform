
from decimal import Decimal

from django.conf import settings

from .models import MeterReading


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
