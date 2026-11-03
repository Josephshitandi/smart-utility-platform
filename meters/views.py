
from rest_framework import generics, permissions

from .models import Meter, MeterReading
from .serializers import MeterSerializer, MeterReadingSerializer
from .permissions import IsMeterAdministrator, IsMeterStaff, IsReadingSubmitter


class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Meter.objects.select_related("customer").all()

        if user.role == "customer":
            return Meter.objects.select_related("customer").filter(
                customer=user
            )

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
            return Meter.objects.select_related("customer").filter(
                customer=user
            )

        if user.role in ["technician", "support"]:
            return Meter.objects.select_related("customer").all()

        return Meter.objects.none()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsMeterAdministrator()]

        return [permissions.IsAuthenticated()]


class MeterReadingListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterReadingSerializer

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

