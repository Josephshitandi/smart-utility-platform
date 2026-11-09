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
    )

    search_fields = (
        "subject",
        "customer__email",
        "assigned_to__email",
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ticket",
        "sender",
        "is_internal",
        "created_at",
    )

    list_filter = ("is_internal",)
    search_fields = ("message",)