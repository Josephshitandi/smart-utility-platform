
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from rest_framework import serializers

from meters.models import Meter, MeterReading

from .models import Tariff, Bill
from .services import create_bill


class TariffSerializer(serializers.ModelSerializer):

    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
    )

    class Meta:
        model = Tariff
        fields = [
            "id",
            "name",
            "meter_type",
            "rate_per_unit",
            "fixed_charge",
            "effective_from",
            "effective_to",
            "is_active",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        meter_type = attrs.get(
            "meter_type",
            getattr(self.instance, "meter_type", None),
        )

        effective_from = attrs.get(
            "effective_from",
            getattr(self.instance, "effective_from", None),
        )

        effective_to = attrs.get(
            "effective_to",
            getattr(self.instance, "effective_to", None),
        )

        is_active = attrs.get(
            "is_active",
            getattr(self.instance, "is_active", True),
        )

        if (
            effective_to is not None
            and effective_from is not None
            and effective_to < effective_from
        ):
            raise serializers.ValidationError({
                "effective_to": (
                    "The expiry date cannot be before "
                    "the effective start date."
                )
            })

        if is_active:
            overlapping_tariffs = Tariff.objects.filter(
                meter_type=meter_type,
                is_active=True,
            )

            if self.instance:
                overlapping_tariffs = overlapping_tariffs.exclude(
                    pk=self.instance.pk
                )

            overlapping_tariffs = overlapping_tariffs.filter(
                Q(effective_to__isnull=True)
                | Q(effective_to__gte=effective_from)
            ).filter(
                Q(effective_from__lte=effective_to)
                if effective_to is not None
                else Q()
            )

            if overlapping_tariffs.exists():
                raise serializers.ValidationError({
                    "effective_from": (
                        "This tariff overlaps an existing active "
                        "tariff for the same utility type."
                    )
                })

        return attrs


class BillSerializer(serializers.ModelSerializer):

    meter_number = serializers.CharField(
        source="meter.meter_number",
        read_only=True,
    )

    customer_email = serializers.EmailField(
        source="meter.customer.email",
        read_only=True,
    )

    tariff_name = serializers.CharField(
        source="tariff.name",
        read_only=True,
    )

    meter_id = serializers.PrimaryKeyRelatedField(
        queryset=Meter.objects.all(),
        source="meter",
        write_only=True,
    )

    previous_reading_id = serializers.PrimaryKeyRelatedField(
        queryset=MeterReading.objects.all(),
        source="previous_reading",
        write_only=True,
    )

    current_reading_id = serializers.PrimaryKeyRelatedField(
        queryset=MeterReading.objects.all(),
        source="current_reading",
        write_only=True,
    )

    class Meta:
        model = Bill

        fields = [
            "id",
            "meter",
            "meter_id",
            "meter_number",
            "customer_email",
            "tariff",
            "tariff_name",
            "previous_reading",
            "previous_reading_id",
            "current_reading",
            "current_reading_id",
            "billing_period_start",
            "billing_period_end",
            "units_consumed",
            "rate_per_unit",
            "fixed_charge",
            "subtotal",
            "amount",
            "due_date",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "meter",
            "meter_number",
            "customer_email",
            "tariff",
            "tariff_name",
            "previous_reading",
            "current_reading",
            "billing_period_start",
            "billing_period_end",
            "units_consumed",
            "rate_per_unit",
            "fixed_charge",
            "subtotal",
            "amount",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        meter = attrs["meter"]
        previous_reading = attrs["previous_reading"]
        current_reading = attrs["current_reading"]

        if previous_reading.meter_id != meter.pk:
            raise serializers.ValidationError({
                "previous_reading_id": (
                    "The previous reading does not belong to this meter."
                )
            })

        if current_reading.meter_id != meter.pk:
            raise serializers.ValidationError({
                "current_reading_id": (
                    "The current reading does not belong to this meter."
                )
            })

        return attrs

    def create(self, validated_data):
        try:
            return create_bill(
                meter_id=validated_data["meter"].pk,
                previous_reading_id=validated_data["previous_reading"].pk,
                current_reading_id=validated_data["current_reading"].pk,
                due_date=validated_data["due_date"],
                created_by=self.context["request"].user,
            )

        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)

            raise serializers.ValidationError(exc.messages)
