"""
Django admin configuration for the accounts app.
Registers the custom User model with full field visibility and filters.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Extends Django's built-in UserAdmin to handle the custom User model.
    Replaces username-based fields with email-based ones.
    """

    # ── List view ─────────────────────────────────────────────────────────────
    list_display = (
        "email", "get_full_name", "role", "account_status",
        "is_staff", "is_active", "date_joined",
    )
    list_filter  = ("role", "account_status", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering      = ("-date_joined",)

    # ── Detail view field sets ────────────────────────────────────────────────
    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
        (_("Personal info"), {
            "fields": ("first_name", "last_name", "phone", "profile_picture"),
        }),
        (_("Role & status"), {
            "fields": ("role", "account_status", "admin_notes"),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),
        }),
    )

    # ── Add user form field sets ───────────────────────────────────────────────
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "first_name", "last_name",
                "role", "account_status",
                "password1", "password2",
            ),
        }),
    )

    readonly_fields = ("last_login", "date_joined")

    # Use email as the username field
    USERNAME_FIELD = "email"

    @admin.display(description="Full name")
    def get_full_name(self, obj):
        return obj.get_full_name()
