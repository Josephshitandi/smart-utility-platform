
"""
Django settings for smart_utility project.
"""

import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------
# SECURITY
# --------------------------------------------------

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY is missing from the environment."
    )

DEBUG = True

ALLOWED_HOSTS = []


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "drf_spectacular",

    "accounts",
    "meters",
    "billing",
    "payments",
    "support",
]


# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "smart_utility.urls"


# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "smart_utility.wsgi.application"


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "smart_utility"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# CUSTOM USER MODEL
# --------------------------------------------------

AUTH_USER_MODEL = "accounts.User"


# --------------------------------------------------
# DJANGO REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],

    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),

    "PAGE_SIZE": 20,

    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    "DEFAULT_SCHEMA_CLASS": (
        "drf_spectacular.openapi.AutoSchema"
    ),
}


# --------------------------------------------------
# JWT AUTHENTICATION
# --------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# --------------------------------------------------
# OPENAPI / SWAGGER DOCUMENTATION
# --------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "Smart Utility Platform API",
    "DESCRIPTION": """
    API documentation for the Smart Utility Management Platform.

    The API provides functionality for:
    - User and account management
    - Meter management
    - Meter readings
    - Billing and tariffs
    - Payments and financial ledger
    - Customer support and tickets

    Authentication uses JWT Bearer tokens.
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --------------------------------------------------
# METER CONSUMPTION THRESHOLDS
# --------------------------------------------------

METER_CONSUMPTION_THRESHOLDS = {
    "electricity": "50",
    "water": "2",
}


# --------------------------------------------------
# UNFOLD ADMIN DASHBOARD
# --------------------------------------------------

UNFOLD = {
    "SITE_TITLE": "Smart Utility Platform",
    "SITE_HEADER": "Smart Utility Management",
    "SITE_SUBHEADER": "Administration Portal",
    "SITE_SYMBOL": "electric_bolt",

    "DASHBOARD_CALLBACK": (
        "smart_utility.dashboard.dashboard_callback"
    ),

    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_UI_WARNINGS": True,

    "BORDER_RADIUS": "8px",

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,

        "navigation": [
            {
                "title": _("Overview"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("User Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy(
                            "admin:accounts_user_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Meter Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Meters"),
                        "icon": "electric_meter",
                        "link": reverse_lazy(
                            "admin:meters_meter_changelist"
                        ),
                    },
                    {
                        "title": _("Meter Readings"),
                        "icon": "monitoring",
                        "link": reverse_lazy(
                            "admin:meters_meterreading_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Billing"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Tariffs"),
                        "icon": "price_change",
                        "link": reverse_lazy(
                            "admin:billing_tariff_changelist"
                        ),
                    },
                    {
                        "title": _("Bills"),
                        "icon": "receipt_long",
                        "link": reverse_lazy(
                            "admin:billing_bill_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Payments"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Payments"),
                        "icon": "payments",
                        "link": reverse_lazy(
                            "admin:payments_payment_changelist"
                        ),
                    },
                    {
                        "title": _("Financial Ledger"),
                        "icon": "account_balance",
                        "link": reverse_lazy(
                            "admin:payments_ledgerentry_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Customer Support"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Support Tickets"),
                        "icon": "support_agent",
                        "link": reverse_lazy(
                            "admin:support_supportticket_changelist"
                        ),
                    },
                    {
                        "title": _("Ticket Messages"),
                        "icon": "forum",
                        "link": reverse_lazy(
                            "admin:support_ticketmessage_changelist"
                        ),
                    },
                ],
            },
        ],
    },
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

