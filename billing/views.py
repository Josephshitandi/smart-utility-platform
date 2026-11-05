from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdministrator
from .models import Tariff, Bill
from .serializers import TariffSerializer, BillSerializer


class TariffListCreateView(generics.ListCreateAPIView):
    """
    List available tariffs.
    Only administrators can create tariffs.
    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdministrator()]

        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TariffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a tariff.
    Only administrators can update or delete tariffs.
    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdministrator()]

        return [IsAuthenticated()]


class BillListCreateView(generics.ListCreateAPIView):
    """
    List bills according to the user's role.
    Only administrators can generate bills.
    """

    serializer_class = BillSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdministrator()]

        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        queryset = Bill.objects.select_related(
            "meter",
            "meter__customer",
            "tariff",
            "previous_reading",
            "current_reading",
            "created_by",
        )

        if user.is_superuser:
            pass
        elif user.role in ["technician", "support"]:
            pass
        elif user.role == "customer":
            queryset = queryset.filter(meter__customer=user)
        else:
            return Bill.objects.none()

        # Filter by meter ID.
        meter_id = self.request.query_params.get("meter")
        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)

        # Filter by bill status.
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search by meter number or customer email.
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                meter__meter_number__icontains=search
            ) | queryset.filter(
                meter__customer__email__icontains=search
            )

        return queryset.order_by("-billing_period_end", "-created_at")


class BillDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single bill.
    Customers can only retrieve bills for their own meters.
    """

    serializer_class = BillSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Bill.objects.select_related(
            "meter",
            "meter__customer",
            "tariff",
            "previous_reading",
            "current_reading",
            "created_by",
        )

        if user.is_superuser:
            return queryset

        if user.role in ["technician", "support"]:
            return queryset

        if user.role == "customer":
            return queryset.filter(meter__customer=user)

        return Bill.objects.none()