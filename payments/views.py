from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdministrator

from .models import Payment, LedgerEntry
from .serializers import (
    PaymentInitiationSerializer,
    PaymentSerializer,
    PaymentCallbackSerializer,
    LedgerEntrySerializer,
)


class PaymentListCreateView(generics.ListCreateAPIView):
    """
    Customers can initiate payments and view their own payment history.
    Support agents and administrators can view all payments.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Payment.objects.select_related(
            "bill",
            "customer",
        )

        if user.is_superuser or user.role == "support":
            return queryset

        if user.role == "customer":
            return queryset.filter(customer=user)

        return queryset.none()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PaymentInitiationSerializer

        return PaymentSerializer


class PaymentDetailView(generics.RetrieveAPIView):
    """
    Retrieve a payment while enforcing customer data isolation.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Payment.objects.select_related(
            "bill",
            "customer",
        )

        if user.is_superuser or user.role == "support":
            return queryset

        if user.role == "customer":
            return queryset.filter(customer=user)

        return queryset.none()


class PaymentCallbackView(generics.GenericAPIView):
    """
    Simulated payment-provider callback.

    Restricted to administrators for demonstration purposes.
    Real provider integration must use verified provider signatures
    or another authenticated provider-to-server mechanism.
    """

    serializer_class = PaymentCallbackSerializer
    permission_classes = [IsAdministrator]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


class LedgerEntryListView(generics.ListAPIView):
    """
    Read-only financial ledger.

    Customers can view their own ledger entries.
    Support agents and administrators can view all entries.

    No API endpoint is provided for creating, modifying,
    or deleting ledger entries.
    """

    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = LedgerEntry.objects.select_related(
            "payment",
            "bill",
            "customer",
        )

        if user.is_superuser or user.role == "support":
            return queryset

        if user.role == "customer":
            return queryset.filter(customer=user)

        return queryset.none()