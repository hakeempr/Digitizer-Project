"""
Django admin configuration for the admin_module app.
Registers AccountRequest, ComplaintReply, and FeedbackReply.
"""

from django.contrib import admin
from .models import AccountRequest, ComplaintReply, FeedbackReply


@admin.register(AccountRequest)
class AccountRequestAdmin(admin.ModelAdmin):
    list_display  = ("customer", "decision", "reviewed_by", "created_at", "reviewed_at")
    list_filter   = ("decision",)
    search_fields = ("customer__email", "customer__first_name", "customer__last_name")
    readonly_fields = ("created_at", "reviewed_at")
    raw_id_fields   = ("customer", "reviewed_by")
    ordering        = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": ("customer", "decision", "admin_notes"),
        }),
        ("Review metadata", {
            "fields": ("reviewed_by", "reviewed_at", "created_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ComplaintReply)
class ComplaintReplyAdmin(admin.ModelAdmin):
    list_display  = ("complaint", "admin", "created_at")
    search_fields = ("complaint__subject", "admin__email")
    readonly_fields = ("created_at",)
    raw_id_fields   = ("complaint", "admin")
    ordering        = ("-created_at",)


@admin.register(FeedbackReply)
class FeedbackReplyAdmin(admin.ModelAdmin):
    list_display  = ("feedback", "admin", "created_at")
    search_fields = ("admin__email",)
    readonly_fields = ("created_at",)
    raw_id_fields   = ("feedback", "admin")
    ordering        = ("-created_at",)
