"""
Customer Module models.

Covers:
  - DigitizedDocument  : uploaded handwritten file → PDF output
  - Feedback           : customer writes feedback on a produced document
  - Complaint          : customer submits a complaint via the complaint box
"""

import os
from django.db import models
from django.conf import settings


def upload_path(instance, filename):
    return f"uploads/{instance.customer_id}/{filename}"


def output_path(instance, filename):
    return f"outputs/{instance.customer_id}/{filename}"


class DigitizedDocument(models.Model):
    """
    Represents one end-to-end OCR pipeline run:
      upload → OCR → layout analysis → PDF generation.
    """

    class Status(models.TextChoices):
        PENDING    = "pending",    "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED  = "completed",  "Completed"
        FAILED     = "failed",     "Failed"

    class StyleTemplate(models.TextChoices):
        DEFAULT  = "default",  "Default"
        ACADEMIC = "academic", "Academic"
        NOTION   = "notion",   "Notion-Style"
        MINIMAL  = "minimal",  "Minimal"

    customer       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title          = models.CharField(max_length=255, blank=True)
    uploaded_file  = models.FileField(upload_to=upload_path)
    output_pdf     = models.FileField(upload_to=output_path, null=True, blank=True)
    style_template = models.CharField(
        max_length=20,
        choices=StyleTemplate.choices,
        default=StyleTemplate.DEFAULT,
    )
    status         = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message  = models.TextField(blank=True)

    # OCR / layout metadata stored as raw text for audit
    raw_ocr_text   = models.TextField(blank=True)
    page_count     = models.PositiveIntegerField(default=0)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    completed_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering     = ["-created_at"]
        verbose_name = "Digitized Document"

    def __str__(self):
        return f"Doc#{self.pk} — {self.customer.email} [{self.status}]"

    @property
    def filename(self):
        return os.path.basename(self.uploaded_file.name) if self.uploaded_file else ""

    @property
    def output_filename(self):
        return os.path.basename(self.output_pdf.name) if self.output_pdf else ""


class Feedback(models.Model):
    """
    Customer writes feedback / a review on a completed DigitizedDocument.
    Admin can reply; the reply is delivered via the customer's inbox.
    """

    class Rating(models.IntegerChoices):
        ONE   = 1, "★"
        TWO   = 2, "★★"
        THREE = 3, "★★★"
        FOUR  = 4, "★★★★"
        FIVE  = 5, "★★★★★"

    customer   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    document   = models.ForeignKey(
        DigitizedDocument,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    rating     = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("customer", "document")
        ordering        = ["-created_at"]
        verbose_name    = "Feedback"

    def __str__(self):
        return f"Feedback by {self.customer.email} on Doc#{self.document_id}"


class Complaint(models.Model):
    """
    Customer files a complaint via the complaint box.
    Admin replies via the ComplaintReply model; reply is also sent to inbox.
    """

    class Status(models.TextChoices):
        OPEN     = "open",     "Open"
        RESOLVED = "resolved", "Resolved"
        CLOSED   = "closed",   "Closed"

    customer   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    subject    = models.CharField(max_length=255)
    body       = models.TextField()
    status     = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering     = ["-created_at"]
        verbose_name = "Complaint"

    def __str__(self):
        return f"Complaint#{self.pk} — {self.customer.email} [{self.status}]"
