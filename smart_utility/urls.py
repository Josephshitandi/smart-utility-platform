
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path("admin/", admin.site.urls),

    # Meters
    path("api/v1/meters/", include("meters.urls")),

    # Billing
    path("api/v1/billing/", include("billing.urls")),

    # Payments
    path("api/v1/payments/", include("payments.urls")),

    # Accounts
    path("api/v1/auth/", include("accounts.urls")),

    # Support
    path("api/v1/support/", include("support.urls")),

    # JWT Authentication
    path(
        "api/v1/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/v1/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
