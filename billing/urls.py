from django.urls import path

from .views import (
    TariffListCreateView,
    TariffDetailView,
    BillListCreateView,
    BillDetailView,
)

urlpatterns = [
    # Tariffs
    path("tariffs/", TariffListCreateView.as_view(), name="tariff-list-create"),
    path("tariffs/<int:pk>/", TariffDetailView.as_view(), name="tariff-detail"),

    # Bills
    path("", BillListCreateView.as_view(), name="bill-list-create"),
    path("<int:pk>/", BillDetailView.as_view(), name="bill-detail"),
]