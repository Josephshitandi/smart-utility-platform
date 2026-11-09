
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    # --------------------------------------------------
    # DJANGO ADMIN
    # --------------------------------------------------

    path("admin/", admin.site.urls),

    # --------------------------------------------------
    # API DOCUMENTATION
    # --------------------------------------------------

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # --------------------------------------------------
    # METERS
    # --------------------------------------------------

    path(
        "api/v1/meters/",
        include("meters.urls"),
    ),

    # --------------------------------------------------
    # BILLING
    # --------------------------------------------------

    path(
        "api/v1/billing/",
        include("billing.urls"),
    ),

    # --------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------

    path(
        "api/v1/payments/",
        include("payments.urls"),
    ),

    # --------------------------------------------------
    # ACCOUNTS
    # --------------------------------------------------

    path(
        "api/v1/auth/",
        include("accounts.urls"),
    ),

    # --------------------------------------------------
    # CUSTOMER SUPPORT
    # --------------------------------------------------

    path(
        "api/v1/support/",
        include("support.urls"),
    ),

    # --------------------------------------------------
    # JWT AUTHENTICATION
    # --------------------------------------------------

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
