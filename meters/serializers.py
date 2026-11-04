
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Meter, MeterReading
from .services import create_meter_reading


class MeterSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )

    class Meta:
        model = Meter
        fields = [
            "id",
            "meter_number",
            "meter_type",
            "customer",
            "customer_email",
            "status",
            "installation_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_email",
            "created_at",
            "updated_at",
        ]


class MeterReadingSerializer(serializers.ModelSerializer):
    meter_number = serializers.CharField(
        source="meter.meter_number",
        read_only=True,
    )

    status = serializers.CharField(read_only=True)

    recorded_by = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    class Meta:
        model = MeterReading
        fields = [
            "id",
            "meter",
            "meter_number",
            "reading_value",
            "reading_date",
            "source",
            "status",
            "recorded_by",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "meter_number",
            "source",
            "status",
            "recorded_by",
            "created_at",
        ]

    def validate(self, attrs):
        meter = attrs["meter"]
        reading_value = attrs["reading_value"]
        reading_date = attrs["reading_date"]

        if meter.status != Meter.Status.ACTIVE:
            raise serializers.ValidationError({
                "meter": (
                    "Readings can only be recorded "
                    "for active meters."
                )
            })

        if reading_date.date() < meter.installation_date:
            raise serializers.ValidationError({
                "reading_date": (
                    "Reading date cannot be before installation."
                )
            })

        if reading_date > timezone.now():
            raise serializers.ValidationError({
                "reading_date": "Future readings are not allowed."
            })

        existing_reading = MeterReading.objects.filter(
            meter=meter,
            reading_date=reading_date,
        )

        if existing_reading.exists():
            raise serializers.ValidationError({
                "reading_date": (
                    "A reading already exists for this meter "
                    "at this time."
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
            raise serializers.ValidationError({
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
            raise serializers.ValidationError({
                "reading_value": (
                    "Reading cannot be higher than a later "
                    "recorded reading."
                )
            })

        return attrs

    def create(self, validated_data):
        try:
            return create_meter_reading(validated_data)

        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)

            raise serializers.ValidationError(exc.messages)
