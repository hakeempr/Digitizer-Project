"""Notification views — unread count and mark-all-read."""

from rest_framework.response import Response
from rest_framework.views import APIView

from utils.permissions import IsApprovedCustomer
from .models import Notification


class UnreadCountView(APIView):
    """GET /api/v1/notify/unread-count/ — badge count for the UI."""

    permission_classes = [IsApprovedCustomer]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"unread_count": count})


class MarkAllReadView(APIView):
    """POST /api/v1/notify/mark-all-read/ — bulk mark as read."""

    permission_classes = [IsApprovedCustomer]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({"marked_read": updated})
