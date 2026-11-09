
from rest_framework import serializers

from .models import SupportTicket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):

    sender_email = serializers.EmailField(
        source="sender.email",
        read_only=True,
    )

    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "ticket",
            "sender",
            "sender_email",
            "message",
            "is_internal",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "sender",
            "sender_email",
            "created_at",
        ]


class SupportTicketSerializer(serializers.ModelSerializer):

    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )

    assigned_to_email = serializers.EmailField(
        source="assigned_to.email",
        read_only=True,
    )

    messages = TicketMessageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "customer",
            "customer_email",
            "assigned_to",
            "assigned_to_email",
            "subject",
            "description",
            "category",
            "priority",
            "status",
            "messages",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "customer_email",
            "assigned_to_email",
            "messages",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
