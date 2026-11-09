from django.contrib import admin

from .models import SupportTicket, TicketMessage


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "customer",
        "assigned_to",
        "category",
        "priority",
        "status",
        "created_at",
    )

    list_filter = (
        "category",
        "priority",
        "status",
        "created_at",
    )

    search_fields = (
        "subject",
        "description",
        "customer__email",
        "assigned_to__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "resolved_at",
    )

    ordering = ("-created_at",)


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket",
        "sender",
        "is_internal",
        "created_at",
    )

    list_filter = (
        "is_internal",
        "created_at",
    )

    search_fields = (
        "message",
        "sender__email",
        "ticket__subject",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)