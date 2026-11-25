from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from drf_spectacular.utils import extend_schema

from accounts.permissions import IsAdministrator

from .models import Payment, LedgerEntry
from .serializers import (
    PaymentInitiationSerializer,
    DarajaPaymentInitiationSerializer,
    PaymentSerializer,
    PaymentCallbackSerializer,
    LedgerEntrySerializer,
)
from .services import reconcile_payments
import logging

from rest_framework.permissions import AllowAny

from .daraja import DarajaError, query_stk_push
from .services import process_verified_daraja_payment

logger = logging.getLogger(__name__)


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


# --------------------------------------------------
# DARAJA M-PESA STK PUSH INITIATION
# --------------------------------------------------

class DarajaPaymentInitiationView(generics.GenericAPIView):
    """
    Initiate a real Safaricom Daraja M-Pesa STK Push.

    Authenticated customers can initiate payments
    for their own pending bills.
    """

    serializer_class = DarajaPaymentInitiationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )

# --------------------------------------------------
# SAFARICOM DARAJA CALLBACK
# --------------------------------------------------

class DarajaCallbackView(generics.GenericAPIView):
    """
    Receive Daraja STK Push callbacks.

    Payment finalization is only attempted after STK Query
    confirms successful transaction status.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            callback = (
                request.data.get("Body", {})
                .get("stkCallback", {})
            )

            checkout_request_id = callback.get(
                "CheckoutRequestID"
            )

            callback_result_code = callback.get(
                "ResultCode"
            )

            callback_result_description = callback.get(
                "ResultDesc", ""
            )

            if not checkout_request_id:
                logger.warning(
                    "Daraja callback missing CheckoutRequestID."
                )
                return Response(
                    {"Result": "Accepted"},
                    status=status.HTTP_200_OK,
                )

            # Only query transactions reported as successful.
            if str(callback_result_code) != "0":
                logger.info(
                    "Daraja transaction unsuccessful: %s",
                    checkout_request_id,
                )
                return Response(
                    {"Result": "Accepted"},
                    status=status.HTTP_200_OK,
                )

            metadata = (
                callback.get("CallbackMetadata", {})
                .get("Item", [])
            )

            metadata_values = {
                item.get("Name"): item.get("Value")
                for item in metadata
                if isinstance(item, dict)
            }

            receipt = metadata_values.get("MpesaReceiptNumber")
            callback_amount = metadata_values.get("Amount")
            callback_phone = metadata_values.get("PhoneNumber")

            if (
                receipt is None
                or callback_amount is None
                or callback_phone is None
            ):
                logger.warning(
                    "Daraja callback metadata incomplete: %s",
                    checkout_request_id,
                )
                return Response(
                    {"Result": "Accepted"},
                    status=status.HTTP_200_OK,
                )

            # Verify the transaction directly with Safaricom.
            query_result = query_stk_push(
                checkout_request_id
            )

            if str(query_result.get("ResponseCode")) != "0":
                logger.warning(
                    "Daraja STK Query was not accepted: %s",
                    checkout_request_id,
                )
                return Response(
                    {"Result": "Accepted"},
                    status=status.HTTP_200_OK,
                )

            if str(query_result.get("ResultCode")) != "0":
                logger.info(
                    "Daraja query did not confirm success: %s",
                    checkout_request_id,
                )
                return Response(
                    {"Result": "Accepted"},
                    status=status.HTTP_200_OK,
                )

            payment = process_verified_daraja_payment(
                checkout_request_id=checkout_request_id,
                provider_reference=str(receipt),
                amount=callback_amount,
                phone_number=str(callback_phone),
                result_code=query_result.get("ResultCode"),
                result_description=query_result.get(
                    "ResultDesc",
                    callback_result_description,
                ),
            )

            logger.info(
                "Daraja payment finalized: payment_id=%s",
                payment.pk,
            )

        except (ValidationError, DarajaError, KeyError, TypeError, ValueError):
            logger.exception(
                "Daraja callback processing failed."
            )

        except Exception:
            logger.exception(
                "Unexpected error while processing Daraja callback."
            )

        # Acknowledge the callback to avoid endless retries.
        return Response(
            {"Result": "Accepted"},
            status=status.HTTP_200_OK,
        )