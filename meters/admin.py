
from django.contrib import admin
from .models import Meter


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = (
        "meter_number",
        "meter_type",
        "customer",
        "status",
        "installation_date",
    )

    list_filter = ("meter_type", "status")
    search_fields = (
        "meter_number",
        "customer__email",
    )
