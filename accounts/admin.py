from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "id",
        "email",
        "username",
        "phone_number",
        "role",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
        "is_superuser",
    )

    search_fields = (
        "email",
        "username",
        "phone_number",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "email",
                "password",
            )
        }),
        ("Personal Information", {
            "fields": (
                "username",
                "first_name",
                "last_name",
                "phone_number",
                "role",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
                "created_at",
                "updated_at",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "username",
                "password1",
                "password2",
                "phone_number",
                "role",
                "is_staff",
                "is_active",
            ),
        }),
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "created_at",
        "updated_at",
    )