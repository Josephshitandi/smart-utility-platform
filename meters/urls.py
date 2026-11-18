from django.urls import path

from .views import (
    MeterListCreateView,
    MeterDetailView,
    MeterReadingListCreateView,
    MeterReadingDetailView,
    ApproveMeterReadingView,
    RejectMeterReadingView,
)

urlpatterns = [
    path("", MeterListCreateView.as_view(), name="meter-list-create"),
    path("<int:pk>/", MeterDetailView.as_view(), name="meter-detail"),

    path(
        "readings/",
        MeterReadingListCreateView.as_view(),
        name="reading-list-create",
    ),
    path(
        "readings/<int:pk>/approve/",
        ApproveMeterReadingView.as_view(),
        name="reading-approve",
    ),
    path(
        "readings/<int:pk>/reject/",
        RejectMeterReadingView.as_view(),
        name="reading-reject",
    ),
    path(
        "readings/<int:pk>/",
        MeterReadingDetailView.as_view(),
        name="reading-detail",
    ),
]