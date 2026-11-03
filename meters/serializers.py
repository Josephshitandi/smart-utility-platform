
from rest_framework import serializers
from .models import Meter


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
