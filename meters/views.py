
from rest_framework import generics, permissions

from .models import Meter
from .serializers import MeterSerializer
from .permissions import IsMeterAdministrator, IsMeterStaff


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
