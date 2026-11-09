
from django.contrib import admin

from .models import Payment, LedgerEntry


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "bill",
        "amount",
        "method",
        "provider",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "method",
        "provider",
    )

    search_fields = (
        "provider_reference",
        "idempotency_key",
        "bill__id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "processed_at",
    )


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "payment",
        "entry_type",
        "amount",
        "created_at",
    )

    list_filter = (
        "entry_type",
    )

    search_fields = (
        "payment__id",
        "description",
    )

    readonly_fields = (
        "payment",
        "entry_type",
        "amount",
        "description",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
