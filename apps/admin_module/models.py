"""
Admin module models.

The Admin Module is responsible for:
  - Approving / rejecting new customer account requests
  - Reading and replying to customer complaints
  - Reading and replying to customer feedback / reviews
"""

from django.db import models
from django.conf import settings


class AccountRequest(models.Model):
    """
    Shadow record created whenever a new CUSTOMER registers.
    Admins use this queue to approve or reject accounts.
    """

    class Decision(models.TextChoices):
        PENDING  = "pending",  "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    customer   = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_request",
    )
    decision   = models.CharField(
        max_length=10, choices=Decision.choices, default=Decision.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_requests",
    )
    admin_notes = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Account Request"

    def __str__(self):
        return f"AccountRequest({self.customer.email}) → {self.decision}"


class ComplaintReply(models.Model):
    """Admin reply to a customer complaint (see customer_module.Complaint)."""

    complaint  = models.OneToOneField(
        "customer_module.Complaint",
        on_delete=models.CASCADE,
        related_name="admin_reply",
    )
    admin      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="complaint_replies",
    )
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Complaint Reply"

    def __str__(self):
        return f"Reply to Complaint#{self.complaint_id} by {self.admin}"


class FeedbackReply(models.Model):
    """Admin reply to a customer feedback / review entry."""

    feedback   = models.OneToOneField(
        "customer_module.Feedback",
        on_delete=models.CASCADE,
        related_name="admin_reply",
    )
    admin      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="feedback_replies",
    )
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback Reply"

    def __str__(self):
        return f"Reply to Feedback#{self.feedback_id} by {self.admin}"
