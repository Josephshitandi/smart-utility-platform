from django.urls import path

from .views import (
    UserRegistrationView,
    UserProfileView,
    RoleDashboardView,
    TechnicianDashboardView,
    SupportDashboardView,
    AdministratorDashboardView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),

    path("dashboard/", RoleDashboardView.as_view(), name="dashboard"),
    path("technician/", TechnicianDashboardView.as_view(), name="technician-dashboard"),
    path("support/", SupportDashboardView.as_view(), name="support-dashboard"),
    path("administrator/", AdministratorDashboardView.as_view(), name="administrator-dashboard"),
]