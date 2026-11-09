
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import SupportTicket, TicketMessage
from .serializers import (
    SupportTicketSerializer,
    TicketMessageSerializer,
)


def get_user_tickets(user):
    """Return tickets accessible to the authenticated user."""

    if user.is_superuser:
        return SupportTicket.objects.all()

    if getattr(user, "role", None) == "support":
        return SupportTicket.objects.filter(assigned_to=user)

    if getattr(user, "role", None) == "customer":
        return SupportTicket.objects.filter(customer=user)

    return SupportTicket.objects.none()


class SupportTicketListCreateView(generics.ListCreateAPIView):

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_tickets(self.request.user)

    def perform_create(self, serializer):
        if getattr(self.request.user, "role", None) != "customer":
            raise PermissionDenied(
                "Only customers can create support tickets."
            )

        serializer.save(customer=self.request.user)


class SupportTicketDetailView(generics.RetrieveUpdateAPIView):

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_tickets(self.request.user)

    def update(self, request, *args, **kwargs):
        if not (
            request.user.is_superuser
            or getattr(request.user, "role", None) == "support"
        ):
            raise PermissionDenied(
                "Only support agents and administrators "
                "can update tickets."
            )

        if "assigned_to" in request.data and not request.user.is_superuser:
            raise PermissionDenied(
                "Only administrators can assign support tickets."
            )

        return super().update(request, *args, **kwargs)


class TicketMessageListCreateView(generics.ListCreateAPIView):

    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_ticket(self):
        return get_object_or_404(
            get_user_tickets(self.request.user),
            pk=self.kwargs["ticket_id"],
        )

    def get_queryset(self):
        ticket = self.get_ticket()

        messages = TicketMessage.objects.filter(ticket=ticket)

        if (
            not self.request.user.is_superuser
            and getattr(self.request.user, "role", None) == "customer"
        ):
            messages = messages.filter(is_internal=False)

        return messages

    def perform_create(self, serializer):
        ticket = self.get_ticket()
        user = self.request.user

        is_customer = (
            getattr(user, "role", None) == "customer"
        )

        if is_customer and ticket.customer_id != user.id:
            raise PermissionDenied(
                "You cannot reply to another customer's ticket."
            )

        if (
            not is_customer
            and not user.is_superuser
            and getattr(user, "role", None) != "support"
        ):
            raise PermissionDenied(
                "You are not authorized to send ticket messages."
            )

        if (
            is_customer
            and self.request.data.get("is_internal", False)
        ):
            raise ValidationError(
                "Customers cannot create internal notes."
            )

        serializer.save(
            ticket=ticket,
            sender=user,
        )
