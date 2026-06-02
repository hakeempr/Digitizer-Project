"""Serializers for the Admin Module."""

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import AdminUserListSerializer
from .models import AccountRequest, ComplaintReply, FeedbackReply


# ─── Account Requests ─────────────────────────────────────────────────────────

class AccountRequestSerializer(serializers.ModelSerializer):
    customer_detail = AdminUserListSerializer(source="customer", read_only=True)

    class Meta:
        model  = AccountRequest
        fields = [
            "id", "customer", "customer_detail",
            "decision", "admin_notes", "created_at", "reviewed_at",
        ]
        read_only_fields = ["id", "customer", "created_at", "reviewed_at"]


class AccountDecisionSerializer(serializers.Serializer):
    """Body for POST approve / reject endpoints."""

    decision    = serializers.ChoiceField(choices=["approved", "rejected"])
    admin_notes = serializers.CharField(required=False, allow_blank=True, default="")


# ─── Complaint Replies ────────────────────────────────────────────────────────

class ComplaintReplySerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin.email", read_only=True)
    complaint_subject = serializers.CharField(
        source="complaint.subject", read_only=True
    )

    class Meta:
        model  = ComplaintReply
        fields = [
            "id", "complaint", "complaint_subject",
            "admin", "admin_email", "body", "created_at",
        ]
        read_only_fields = ["id", "admin", "created_at"]

    def create(self, validated_data):
        validated_data["admin"] = self.context["request"].user
        return super().create(validated_data)


# ─── Feedback Replies ─────────────────────────────────────────────────────────

class FeedbackReplySerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin.email", read_only=True)

    class Meta:
        model  = FeedbackReply
        fields = [
            "id", "feedback", "admin", "admin_email", "body", "created_at",
        ]
        read_only_fields = ["id", "admin", "created_at"]

    def create(self, validated_data):
        validated_data["admin"] = self.context["request"].user
        return super().create(validated_data)


# ─── Dashboard Summary ────────────────────────────────────────────────────────

class AdminDashboardSerializer(serializers.Serializer):
    """Read-only summary stats for the admin dashboard."""

    total_customers       = serializers.IntegerField()
    pending_requests      = serializers.IntegerField()
    approved_customers    = serializers.IntegerField()
    rejected_customers    = serializers.IntegerField()
    total_documents       = serializers.IntegerField()
    open_complaints       = serializers.IntegerField()
    unanswered_feedbacks  = serializers.IntegerField()
