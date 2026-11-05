from django.urls import path

from .views import (
    TariffListCreateView,
    TariffDetailView,
    BillListCreateView,
    BillDetailView,
)

urlpatterns = [
    # Tariff management
    path("tariffs/", TariffListCreateView.as_view(), name="tariff-list-create"),
    path("tariffs/<int:pk>/", TariffDetailView.as_view(), name="tariff-detail"),

    # Bill management
    path("bills/", BillListCreateView.as_view(), name="bill-list-create"),
    path("bills/<int:pk>/", BillDetailView.as_view(), name="bill-detail"),
]