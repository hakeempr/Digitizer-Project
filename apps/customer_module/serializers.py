"""Serializers for the Customer Module."""

from rest_framework import serializers
from .models import DigitizedDocument, Feedback, Complaint


# ─── Document ─────────────────────────────────────────────────────────────────

class DocumentUploadSerializer(serializers.ModelSerializer):
    """Used when a customer uploads a new handwritten file."""

    class Meta:
        model  = DigitizedDocument
        fields = ["id", "title", "uploaded_file", "style_template"]

    def validate_uploaded_file(self, value):
        from django.conf import settings
        import os

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(
                f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB."
            )
        return value

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Full detail view of a document, including output URL."""

    output_pdf_url = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()

    class Meta:
        model  = DigitizedDocument
        fields = [
            "id", "title", "filename", "output_filename",
            "output_pdf_url", "style_template",
            "status", "error_message", "raw_ocr_text",
            "page_count", "feedback_count",
            "created_at", "updated_at", "completed_at",
        ]
        read_only_fields = fields

    def get_output_pdf_url(self, obj):
        request = self.context.get("request")
        if obj.output_pdf and request:
            return request.build_absolute_uri(obj.output_pdf.url)
        return None

    def get_feedback_count(self, obj):
        return obj.feedbacks.count()


class DocumentListSerializer(serializers.ModelSerializer):
    """Compact list view."""

    class Meta:
        model  = DigitizedDocument
        fields = [
            "id", "title", "filename", "style_template",
            "status", "page_count", "created_at",
        ]
        read_only_fields = fields


# ─── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    admin_replied  = serializers.SerializerMethodField()
    admin_reply    = serializers.SerializerMethodField()

    class Meta:
        model  = Feedback
        fields = [
            "id", "customer", "customer_email",
            "document", "rating", "body",
            "admin_replied", "admin_reply", "created_at",
        ]
        read_only_fields = ["id", "customer", "created_at"]

    def get_admin_replied(self, obj):
        return hasattr(obj, "admin_reply")

    def get_admin_reply(self, obj):
        if hasattr(obj, "admin_reply"):
            return {
                "body":       obj.admin_reply.body,
                "created_at": obj.admin_reply.created_at,
            }
        return None

    def validate(self, attrs):
        request  = self.context["request"]
        document = attrs.get("document")
        if document and document.customer != request.user:
            raise serializers.ValidationError(
                {"document": "You can only leave feedback on your own documents."}
            )
        if document and document.status != DigitizedDocument.Status.COMPLETED:
            raise serializers.ValidationError(
                {"document": "Feedback can only be left on completed documents."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


# ─── Complaint ────────────────────────────────────────────────────────────────

class ComplaintSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    admin_replied  = serializers.SerializerMethodField()
    admin_reply    = serializers.SerializerMethodField()

    class Meta:
        model  = Complaint
        fields = [
            "id", "customer", "customer_email",
            "subject", "body", "status",
            "admin_replied", "admin_reply",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "customer", "status", "created_at", "updated_at"]

    def get_admin_replied(self, obj):
        return hasattr(obj, "admin_reply")

    def get_admin_reply(self, obj):
        if hasattr(obj, "admin_reply"):
            return {
                "body":       obj.admin_reply.body,
                "created_at": obj.admin_reply.created_at,
            }
        return None

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)
