from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsAdministrator

from .models import Payment, LedgerEntry
from .serializers import (
    PaymentInitiationSerializer,
    PaymentSerializer,
    PaymentCallbackSerializer,
    LedgerEntrySerializer,
)
from .services import reconcile_payments


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


# --------------------------------------------------
# PAYMENT RECONCILIATION RESPONSE SERIALIZERS
# --------------------------------------------------

class BillReconciliationSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField()
    bill_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    successful_payment_count = serializers.IntegerField()
    ledger_entry_count = serializers.IntegerField()

    payment_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    ledger_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    amount_difference = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    outstanding_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    missing_ledger_payments = serializers.ListField(
        child=serializers.IntegerField(),
    )

    unmatched_ledger_entry_ids = serializers.ListField(
        child=serializers.IntegerField(),
    )

    duplicate_ledger_payment_ids = serializers.ListField(
        child=serializers.IntegerField(),
    )

    ledger_payment_mismatch_ids = serializers.ListField(
        child=serializers.IntegerField(),
    )

    is_reconciled = serializers.BooleanField()

    issues = serializers.ListField(
        child=serializers.CharField(),
    )


class PaymentReconciliationReportSerializer(serializers.Serializer):
    total_bills_checked = serializers.IntegerField()
    reconciled_count = serializers.IntegerField()
    discrepancy_count = serializers.IntegerField()

    results = BillReconciliationSerializer(many=True)


class PaymentReconciliationView(generics.GenericAPIView):
    """
    Administrator-only financial reconciliation report.

    Compares successful payments against ledger entries
    and identifies financial inconsistencies.

    This endpoint is read-only.
    """

    serializer_class = PaymentReconciliationReportSerializer
    permission_classes = [IsAdministrator]

    @extend_schema(
        responses={
            200: PaymentReconciliationReportSerializer,
        },
        description=(
            "Administrator-only read-only report comparing "
            "successful payments against financial ledger entries."
        ),
    )
    def get(self, request, *args, **kwargs):
        report = reconcile_payments()

        return Response(
            report,
            status=status.HTTP_200_OK,
        )