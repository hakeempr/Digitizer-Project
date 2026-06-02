"""URL routes for the Notifications app."""

from django.urls import path
from .views import UnreadCountView, MarkAllReadView

urlpatterns = [
    path("unread-count/",  UnreadCountView.as_view(), name="notify-unread-count"),
    path("mark-all-read/", MarkAllReadView.as_view(), name="notify-mark-all-read"),
]
