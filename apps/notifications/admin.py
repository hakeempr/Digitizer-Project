"""
Django admin configuration for the notifications app.
"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ("id", "recipient_email", "subject", "category", "is_read", "created_at")
    list_filter   = ("category", "is_read")
    search_fields = ("recipient__email", "subject", "body")
    readonly_fields = ("created_at",)
    raw_id_fields   = ("recipient",)
    ordering        = ("-created_at",)

    actions = ["mark_as_read", "mark_as_unread"]

    @admin.display(description="Recipient")
    def recipient_email(self, obj):
        return obj.recipient.email

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected notifications as unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
