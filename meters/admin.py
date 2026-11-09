
from django.contrib import admin

from .models import Meter, MeterReading


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "meter_number",
        "meter_type",
        "customer",
        "status",
        "installation_date",
        "created_at",
    )

    list_filter = (
        "meter_type",
        "status",
        "installation_date",
    )

    search_fields = (
        "meter_number",
        "customer__email",
        "customer__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "meter",
        "reading_value",
        "reading_date",
        "source",
        "status",
        "recorded_by",
    )

    list_filter = (
        "source",
        "status",
        "reading_date",
    )

    search_fields = (
        "meter__meter_number",
        "recorded_by__email",
        "notes",
    )

    readonly_fields = (
        "meter",
        "reading_value",
        "reading_date",
        "source",
        "status",
        "recorded_by",
        "notes",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
