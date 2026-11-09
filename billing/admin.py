
from django.contrib import admin

from .models import Bill, Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "meter_type",
        "rate_per_unit",
        "fixed_charge",
        "effective_from",
        "effective_to",
        "is_active",
        "created_by",
    )

    list_filter = (
        "meter_type",
        "is_active",
        "effective_from",
    )

    search_fields = (
        "name",
        "created_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "meter",
        "tariff",
        "billing_period_start",
        "billing_period_end",
        "units_consumed",
        "amount",
        "due_date",
        "status",
        "created_by",
    )

    list_filter = (
        "status",
        "billing_period_start",
        "billing_period_end",
        "due_date",
    )

    search_fields = (
        "meter__meter_number",
        "created_by__email",
    )

    readonly_fields = (
        "meter",
        "tariff",
        "previous_reading",
        "current_reading",
        "billing_period_start",
        "billing_period_end",
        "units_consumed",
        "rate_per_unit",
        "fixed_charge",
        "subtotal",
        "amount",
        "due_date",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
