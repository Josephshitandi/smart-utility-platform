
from django.urls import path

from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    PaymentCallbackView,
    LedgerEntryListView,
)

urlpatterns = [
    path(
        "",
        PaymentListCreateView.as_view(),
        name="payment-list-create",
    ),
    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
    path(
        "callback/",
        PaymentCallbackView.as_view(),
        name="payment-callback",
    ),
    path(
        "ledger/",
        LedgerEntryListView.as_view(),
        name="ledger-list",
    ),
]
