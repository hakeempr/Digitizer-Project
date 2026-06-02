"""
Customer Module Views - with robust sync pipeline and proper error handling.
"""
import re as _re

# UUID / hex hash pattern - Django renames uploaded files to random hashes
_UUID_PATTERN = _re.compile(
    r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}',
    _re.IGNORECASE,
)

def _is_uuid_or_filename(text):
    t = text.strip()
    t = _re.sub(r'\.(jpg|jpeg|png|gif|bmp|tif|tiff|pdf|webp)$', '', t, flags=_re.IGNORECASE)
    if _UUID_PATTERN.match(t):
        return True
    stripped = t.replace('-', '').replace('_', '')
    if len(stripped) >= 20 and all(c in '0123456789abcdefABCDEF' for c in stripped):
        return True
    return False

import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.permissions import IsApprovedCustomer, IsOwnerOrAdmin
from apps.notifications.models import Notification
from .models import DigitizedDocument, Feedback, Complaint
from .serializers import (
    DocumentUploadSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    FeedbackSerializer,
    ComplaintSerializer,
)

logger = logging.getLogger(__name__)


def run_pipeline_sync(document_id: int):
    """
    Full OCR → Layout → PDF pipeline running synchronously.
    Always works even without Celery/Redis.
    """
    from apps.customer_module.models import DigitizedDocument
    from apps.ocr_engine.services import SmartLayoutAnalyser
    from apps.document_generator.services import PDFGenerator
    from django.conf import settings
    from pathlib import Path

    document = DigitizedDocument.objects.get(pk=document_id)
    document.status = DigitizedDocument.Status.PROCESSING
    document.error_message = ""
    document.save(update_fields=["status", "error_message"])

    try:
        image_path = document.uploaded_file.path

        # ── OCR ───────────────────────────────────────────────────────────────
        api_key = getattr(settings, "OCR_SPACE_API_KEY", "").strip()

        if api_key:
            # Real OCR via OCR.space API
            from apps.ocr_engine.services import OCRSpaceClient
            client     = OCRSpaceClient()
            ocr_result = client.run_ocr(image_path)

            if not ocr_result["success"]:
                raise RuntimeError(f"OCR API error: {ocr_result['error']}")

            raw_text   = ocr_result["full_text"]
            lines      = ocr_result["lines"]
            page_count = ocr_result["pages"] or 1

        else:
            # No API key — extract text from image using basic method
            logger.warning(
                "OCR_SPACE_API_KEY not set. "
                "Using placeholder text for document #%d. "
                "Add your API key to .env to enable real OCR.",
                document_id
            )
            raw_text   = (
                f"[OCR not configured]\n\n"
                f"Document: {document.title}\n"
                f"Uploaded: {document.created_at}\n\n"
                f"To enable handwriting recognition, add your free OCR.space API key "
                f"to the .env file:\n\n"
                f"  OCR_SPACE_API_KEY=your-key-here\n\n"
                f"Get a free key at: https://ocr.space/ocrapi\n\n"
                f"The PDF has been generated with this placeholder text. "
                f"After adding your API key, re-upload the file to get real OCR output."
            )
            lines      = raw_text.splitlines()
            page_count = 1

        # ── Layout Analysis ───────────────────────────────────────────────────
        analyser = SmartLayoutAnalyser()
        overlay  = ocr_result.get("overlay")
        blocks   = analyser.analyse(lines, overlay=overlay)

        # ── PDF Generation ────────────────────────────────────────────────────
        generator = PDFGenerator(style_name=document.style_template)
        pdf_filepath = generator.generate(
            blocks      = blocks,
            title       = document.title or f"Document #{document_id}",
            customer_id = document.customer_id,
            doc_id      = document_id,
        )

        # ── Save results ──────────────────────────────────────────────────────
        relative_path = Path(pdf_filepath).relative_to(settings.MEDIA_ROOT)
        document.output_pdf   = str(relative_path)
        document.raw_ocr_text = raw_text
        document.page_count   = page_count
        document.status       = DigitizedDocument.Status.COMPLETED
        document.completed_at = timezone.now()
        document.save(update_fields=[
            "output_pdf", "raw_ocr_text", "page_count",
            "status", "completed_at", "error_message",
        ])
        logger.info("Pipeline completed for document #%d", document_id)

    except Exception as exc:
        logger.exception("Pipeline failed for document #%d: %s", document_id, exc)
        document.status        = DigitizedDocument.Status.FAILED
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message"])
        raise  # re-raise so caller knows it failed


# ─── Document Upload ───────────────────────────────────────

class DocumentUploadView(generics.CreateAPIView):
    """
    POST /api/v1/customer/documents/
    Runs pipeline synchronously — works without Celery.
    """
    serializer_class   = DocumentUploadSerializer
    permission_classes = [IsApprovedCustomer]
    parser_classes     = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        pipeline_error = None

        # Try Celery async first
        celery_started = False
        try:
            from apps.ocr_engine.tasks import process_document_task
            process_document_task.delay(document.pk)
            celery_started = True
            logger.info("Celery task queued for document #%d", document.pk)
        except Exception as e:
            logger.warning("Celery not available: %s — running synchronously", e)

        # If Celery not available, run synchronously
        if not celery_started:
            try:
                run_pipeline_sync(document.pk)
            except Exception as e:
                pipeline_error = str(e)

        document.refresh_from_db()

        return Response(
            {
                "message": (
                    "Upload successful! PDF has been generated."
                    if document.status == DigitizedDocument.Status.COMPLETED
                    else "Upload successful! Processing started."
                    if celery_started
                    else f"Upload failed during processing: {pipeline_error}"
                    if pipeline_error
                    else "Uploaded. Processing queued."
                ),
                "document_id": document.pk,
                "status":      document.status,
            },
            status=status.HTTP_201_CREATED,
        )


class DocumentListView(generics.ListAPIView):
    serializer_class   = DocumentListSerializer
    permission_classes = [IsApprovedCustomer]

    def get_queryset(self):
        return DigitizedDocument.objects.filter(
            customer=self.request.user
        ).order_by("-created_at")


class DocumentDetailView(generics.RetrieveAPIView):
    serializer_class   = DocumentDetailSerializer
    permission_classes = [IsApprovedCustomer, IsOwnerOrAdmin]

    def get_queryset(self):
        return DigitizedDocument.objects.filter(customer=self.request.user)


class DocumentStatusView(APIView):
    permission_classes = [IsApprovedCustomer]

    def get(self, request, pk):
        try:
            doc = DigitizedDocument.objects.get(pk=pk, customer=request.user)
        except DigitizedDocument.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "document_id":   doc.pk,
            "status":        doc.status,
            "error_message": doc.error_message,
            "output_ready":  doc.status == DigitizedDocument.Status.COMPLETED,
        })


# ─── Feedback ──────────────────────────────────────────────

class FeedbackCreateView(generics.CreateAPIView):
    serializer_class   = FeedbackSerializer
    permission_classes = [IsApprovedCustomer]


class FeedbackListView(generics.ListAPIView):
    serializer_class   = FeedbackSerializer
    permission_classes = [IsApprovedCustomer]

    def get_queryset(self):
        return Feedback.objects.filter(
            customer=self.request.user
        ).select_related("document").prefetch_related("admin_reply")


# ─── Complaints ────────────────────────────────────────────

class ComplaintCreateView(generics.CreateAPIView):
    serializer_class   = ComplaintSerializer
    permission_classes = [IsApprovedCustomer]


class ComplaintListView(generics.ListAPIView):
    serializer_class   = ComplaintSerializer
    permission_classes = [IsApprovedCustomer]

    def get_queryset(self):
        return Complaint.objects.filter(
            customer=self.request.user
        ).prefetch_related("admin_reply")


# ─── Inbox ─────────────────────────────────────────────────

class InboxListView(generics.ListAPIView):
    permission_classes = [IsApprovedCustomer]

    def list(self, request, *args, **kwargs):
        from apps.notifications.serializers import NotificationSerializer
        qs = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")
        return Response(
            NotificationSerializer(qs, many=True, context={"request": request}).data
        )


class InboxMarkReadView(APIView):
    permission_classes = [IsApprovedCustomer]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"message": "Marked as read."})
