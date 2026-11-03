
from django.urls import path

from .views import MeterListCreateView, MeterDetailView


urlpatterns = [
    path("", MeterListCreateView.as_view(), name="meter-list-create"),
    path("<int:pk>/", MeterDetailView.as_view(), name="meter-detail"),
]
