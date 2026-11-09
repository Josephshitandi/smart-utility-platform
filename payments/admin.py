
from django.contrib import admin

from .models import Payment, LedgerEntry


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "bill",
        "customer",
        "amount",
        "payment_method",
        "provider",
        "status",
        "initiated_at",
    )

    list_filter = (
        "status",
        "payment_method",
        "provider",
        "initiated_at",
    )

    search_fields = (
        "provider_reference",
        "idempotency_key",
        "customer__email",
        "bill__id",
    )

    readonly_fields = (
        "bill",
        "customer",
        "amount",
        "payment_method",
        "provider",
        "provider_reference",
        "idempotency_key",
        "status",
        "initiated_at",
        "processed_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "payment",
        "bill",
        "customer",
        "entry_type",
        "amount",
        "created_at",
    )

    list_filter = (
        "entry_type",
        "created_at",
    )

    search_fields = (
        "payment__id",
        "bill__id",
        "customer__email",
        "description",
    )

    readonly_fields = (
        "payment",
        "bill",
        "customer",
        "entry_type",
        "amount",
        "description",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
