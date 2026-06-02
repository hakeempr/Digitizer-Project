"""Serializer for the Notification model."""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = [
            "id", "subject", "body",
            "category", "is_read", "created_at",
        ]
        read_only_fields = fields
