
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Meter, MeterReading
from .permissions import (
    IsMeterAdministrator,
    IsMeterStaff,
    IsReadingSubmitter,
)
from .serializers import MeterSerializer, MeterReadingSerializer
from .services import (
    approve_meter_reading,
    reject_meter_reading,
)


class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Meter.objects.select_related("customer").all()

        if user.role == "customer":
            return Meter.objects.select_related("customer").filter(
                customer=user
            )

        return Meter.objects.select_related("customer").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMeterAdministrator()]

        return [IsAuthenticated()]


class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Meter.objects.select_related("customer").all()

        if user.role == "customer":
            return Meter.objects.select_related("customer").filter(
                customer=user
            )

        return Meter.objects.select_related("customer").all()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsMeterAdministrator()]

        return [IsAuthenticated()]


class MeterReadingListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterReadingSerializer
    permission_classes = [IsAuthenticated]

    search_fields = ["meter__meter_number"]
    ordering_fields = [
        "reading_date",
        "reading_value",
        "created_at",
    ]
    ordering = ["-reading_date"]

    def get_queryset(self):
        user = self.request.user

        queryset = MeterReading.objects.select_related(
            "meter",
            "meter__customer",
            "recorded_by",
            "reviewed_by",
        )

        if user.is_superuser:
            pass

        elif user.role == "customer":
            queryset = queryset.filter(meter__customer=user)

        else:
            queryset = queryset.all()

        meter_id = self.request.query_params.get("meter")
        if meter_id and meter_id.isdigit():
            queryset = queryset.filter(meter_id=meter_id)

        source = self.request.query_params.get("source")
        if source in MeterReading.ReadingSource.values:
            queryset = queryset.filter(source=source)

        reading_status = self.request.query_params.get("status")
        if reading_status in MeterReading.ReadingStatus.values:
            queryset = queryset.filter(status=reading_status)

        review_status = self.request.query_params.get("review_status")
        if review_status in MeterReading.ReviewStatus.values:
            queryset = queryset.filter(review_status=review_status)

        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsReadingSubmitter()]

        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(
            recorded_by=self.request.user,
            source=MeterReading.ReadingSource.MANUAL,
        )


class MeterReadingDetailView(generics.RetrieveAPIView):
    serializer_class = MeterReadingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = MeterReading.objects.select_related(
            "meter",
            "meter__customer",
            "recorded_by",
            "reviewed_by",
        )

        if user.is_superuser:
            return queryset

        if user.role == "customer":
            return queryset.filter(meter__customer=user)

        return queryset


class ReadingReviewSerializer(serializers.Serializer):
    review_notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class ApproveMeterReadingView(generics.GenericAPIView):
    serializer_class = ReadingReviewSerializer
    permission_classes = [IsMeterAdministrator]

    @extend_schema(
        request=ReadingReviewSerializer,
        responses={200: MeterReadingSerializer},
        description="Approve a meter reading after administrative review.",
    )
    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        get_object_or_404(MeterReading, pk=pk)

        try:
            reading = approve_meter_reading(
                reading_id=pk,
                reviewed_by=request.user,
                review_notes=serializer.validated_data.get(
                    "review_notes", ""
                ),
            )

        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                detail = exc.message_dict
            else:
                detail = exc.messages

            raise serializers.ValidationError(detail)

        return Response(
            MeterReadingSerializer(reading).data,
            status=status.HTTP_200_OK,
        )


class RejectMeterReadingView(generics.GenericAPIView):
    serializer_class = ReadingReviewSerializer
    permission_classes = [IsMeterAdministrator]

    @extend_schema(
        request=ReadingReviewSerializer,
        responses={200: MeterReadingSerializer},
        description="Reject a meter reading after administrative review.",
    )
    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        get_object_or_404(MeterReading, pk=pk)

        try:
            reading = reject_meter_reading(
                reading_id=pk,
                reviewed_by=request.user,
                review_notes=serializer.validated_data.get(
                    "review_notes", ""
                ),
            )

        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                detail = exc.message_dict
            else:
                detail = exc.messages

            raise serializers.ValidationError(detail)

        return Response(
            MeterReadingSerializer(reading).data,
            status=status.HTTP_200_OK,
        )
