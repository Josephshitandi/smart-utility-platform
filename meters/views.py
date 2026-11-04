
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from .models import Meter, MeterReading
from .serializers import MeterSerializer, MeterReadingSerializer
from .permissions import (
    IsMeterAdministrator,
    IsReadingSubmitter,
)


class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Meter.objects.select_related("customer").all()

        if user.role == "customer":
            return Meter.objects.select_related(
                "customer"
            ).filter(customer=user)

        if user.role in ["technician", "support"]:
            return Meter.objects.select_related("customer").all()

        return Meter.objects.none()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsMeterAdministrator()]

        return [permissions.IsAuthenticated()]


class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Meter.objects.select_related("customer").all()

        if user.role == "customer":
            return Meter.objects.select_related(
                "customer"
            ).filter(customer=user)

        if user.role in ["technician", "support"]:
            return Meter.objects.select_related("customer").all()

        return Meter.objects.none()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsMeterAdministrator()]

        return [permissions.IsAuthenticated()]


class MeterReadingListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterReadingSerializer

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
        )

        # Apply role-based access restrictions first.
        if user.is_superuser:
            pass

        elif user.role == "customer":
            queryset = queryset.filter(meter__customer=user)

        elif user.role in ["technician", "support"]:
            pass

        else:
            return queryset.none()

        # Filter by meter ID.
        meter_id = self.request.query_params.get("meter")

        if meter_id:
            if not meter_id.isdigit():
                raise ValidationError({
                    "meter": "Meter must be a valid numeric ID."
                })

            queryset = queryset.filter(meter_id=meter_id)

        # Filter by reading source.
        source = self.request.query_params.get("source")

        if source:
            if source not in MeterReading.ReadingSource.values:
                raise ValidationError({
                    "source": "Invalid reading source."
                })

            queryset = queryset.filter(source=source)

        # Filter by reading status.
        reading_status = self.request.query_params.get("status")

        if reading_status:
            if reading_status not in MeterReading.ReadingStatus.values:
                raise ValidationError({
                    "status": "Invalid reading status."
                })

            queryset = queryset.filter(status=reading_status)

        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsReadingSubmitter()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(
            recorded_by=self.request.user,
            source=MeterReading.ReadingSource.MANUAL,
        )


class MeterReadingDetailView(generics.RetrieveAPIView):
    serializer_class = MeterReadingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = MeterReading.objects.select_related(
            "meter",
            "meter__customer",
            "recorded_by",
        )

        if user.is_superuser:
            return queryset.all()

        if user.role == "customer":
            return queryset.filter(meter__customer=user)

        if user.role in ["technician", "support"]:
            return queryset.all()

        return queryset.none()
