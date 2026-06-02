"""
Django admin configuration for the customer_module app.
Registers DigitizedDocument, Feedback, and Complaint with
inline support for related records.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import DigitizedDocument, Feedback, Complaint


class FeedbackInline(admin.TabularInline):
    """Show feedbacks inline inside a DigitizedDocument admin page."""

    model       = Feedback
    extra       = 0
    readonly_fields = ("customer", "rating", "body", "created_at")
    can_delete  = False
    show_change_link = True


@admin.register(DigitizedDocument)
class DigitizedDocumentAdmin(admin.ModelAdmin):
    list_display  = (
        "id", "title", "customer_email", "style_template",
        "status", "page_count", "created_at", "has_output",
    )
    list_filter   = ("status", "style_template")
    search_fields = ("title", "customer__email")
    readonly_fields = (
        "raw_ocr_text", "page_count", "created_at",
        "updated_at", "completed_at", "output_pdf",
    )
    raw_id_fields = ("customer",)
    ordering      = ("-created_at",)
    inlines       = [FeedbackInline]

    fieldsets = (
        (None, {
            "fields": ("customer", "title", "uploaded_file", "style_template"),
        }),
        ("Processing status", {
            "fields": ("status", "error_message", "page_count"),
        }),
        ("Output", {
            "fields": ("output_pdf",),
        }),
        ("OCR text", {
            "fields": ("raw_ocr_text",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "completed_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Customer")
    def customer_email(self, obj):
        return obj.customer.email

    @admin.display(description="PDF ready", boolean=True)
    def has_output(self, obj):
        return bool(obj.output_pdf)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display  = ("id", "customer_email", "document", "rating", "created_at")
    list_filter   = ("rating",)
    search_fields = ("customer__email", "body")
    readonly_fields = ("created_at",)
    raw_id_fields   = ("customer", "document")
    ordering        = ("-created_at",)

    @admin.display(description="Customer")
    def customer_email(self, obj):
        return obj.customer.email


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display  = ("id", "customer_email", "subject", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("subject", "body", "customer__email")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields   = ("customer",)
    ordering        = ("-created_at",)

    @admin.display(description="Customer")
    def customer_email(self, obj):
        return obj.customer.email
