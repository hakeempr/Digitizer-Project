"""
Notifications app — in-app inbox for customers.

A Notification is created whenever an admin replies to a complaint or feedback.
The customer reads it via GET /api/v1/customer/inbox/.
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):

    class Category(models.TextChoices):
        COMPLAINT_REPLY = "complaint_reply", "Complaint Reply"
        FEEDBACK_REPLY  = "feedback_reply",  "Feedback Reply"
        SYSTEM          = "system",          "System Message"

    recipient  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    subject    = models.CharField(max_length=255)
    body       = models.TextField()
    category   = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SYSTEM,
    )
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ["-created_at"]
        verbose_name = "Notification"

    def __str__(self):
        return f"Notification → {self.recipient.email}: {self.subject}"
