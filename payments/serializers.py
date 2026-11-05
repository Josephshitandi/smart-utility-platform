
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from billing.models import Bill
from .models import Payment, LedgerEntry
from .services import initiate_payment, process_payment_callback


class PaymentInitiationSerializer(serializers.Serializer):

    bill_id = serializers.PrimaryKeyRelatedField(
        queryset=Bill.objects.all(),
        source="bill",
    )

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0.01,
    )

    payment_method = serializers.ChoiceField(
        choices=Payment.PaymentMethod.choices,
        default=Payment.PaymentMethod.MOBILE_MONEY,
    )

    idempotency_key = serializers.CharField(
        max_length=100,
        trim_whitespace=True,
    )

    def validate_idempotency_key(self, value):
        if not value:
            raise serializers.ValidationError(
                "An idempotency key is required."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]

        try:
            return initiate_payment(
                bill_id=validated_data["bill"].pk,
                customer=request.user,
                amount=validated_data["amount"],
                payment_method=validated_data["payment_method"],
                idempotency_key=validated_data["idempotency_key"],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"payment": exc.messages}
            )


class PaymentSerializer(serializers.ModelSerializer):

    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )

    bill_id = serializers.IntegerField(
        source="bill.pk",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "bill_id",
            "customer",
            "customer_email",
            "amount",
            "payment_method",
            "provider",
            "provider_reference",
            "idempotency_key",
            "status",
            "initiated_at",
            "processed_at",
            "updated_at",
        ]

        read_only_fields = fields


class PaymentCallbackSerializer(serializers.Serializer):

    payment_id = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(),
        source="payment",
    )

    successful = serializers.BooleanField()

    provider_reference = serializers.CharField(
        max_length=100,
    )

    def create(self, validated_data):
        try:
            return process_payment_callback(
                payment_id=validated_data["payment"].pk,
                successful=validated_data["successful"],
                provider_reference=validated_data["provider_reference"],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"callback": exc.messages}
            )


class LedgerEntrySerializer(serializers.ModelSerializer):

    payment_id = serializers.IntegerField(read_only=True)

    bill_id = serializers.IntegerField(read_only=True)

    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "payment_id",
            "bill_id",
            "customer",
            "customer_email",
            "entry_type",
            "amount",
            "description",
            "created_at",
        ]

        read_only_fields = fields
