
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdministrator
from .models import Payment, LedgerEntry
from .serializers import (
    PaymentInitiationSerializer,
    PaymentSerializer,
    PaymentCallbackSerializer,
    LedgerEntrySerializer,
)


class PaymentListCreateView(generics.ListCreateAPIView):

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

    permission_classes = [IsAuthenticated]


class PaymentDetailView(generics.RetrieveAPIView):

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

    serializer_class = PaymentCallbackSerializer
    permission_classes = [IsAdministrator]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        return_response = PaymentSerializer(payment)

        from rest_framework.response import Response
        from rest_framework import status

        return Response(
            return_response.data,
            status=status.HTTP_200_OK,
        )


class LedgerEntryListView(generics.ListAPIView):

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
