"""OCR Engine views — manual trigger and raw OCR result inspection."""

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from utils.permissions import IsApprovedCustomer, IsAdmin
from apps.customer_module.models import DigitizedDocument


class TriggerOCRView(APIView):
    """
    POST /api/v1/ocr/trigger/<document_id>/
    Re-triggers the OCR pipeline for a FAILED document.
    Useful for admin retries without re-uploading.
    """

    permission_classes = [IsAdmin]

    def post(self, request, document_id):
        try:
            document = DigitizedDocument.objects.get(pk=document_id)
        except DigitizedDocument.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        if document.status == DigitizedDocument.Status.PROCESSING:
            return Response(
                {"detail": "Document is already being processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status        = DigitizedDocument.Status.PENDING
        document.error_message = ""
        document.save(update_fields=["status", "error_message"])

        from apps.ocr_engine.tasks import process_document_task
        process_document_task.delay(document.pk)

        return Response({"message": f"OCR re-triggered for document #{document_id}."})


class RawOCRResultView(APIView):
    """
    GET /api/v1/ocr/result/<document_id>/
    Returns the stored raw OCR text for inspection (admin or owner).
    """

    permission_classes = [IsApprovedCustomer]

    def get(self, request, document_id):
        qs = DigitizedDocument.objects.filter(pk=document_id)
        if not request.user.is_admin:
            qs = qs.filter(customer=request.user)

        try:
            document = qs.get()
        except DigitizedDocument.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "document_id":  document.pk,
                "status":       document.status,
                "raw_ocr_text": document.raw_ocr_text,
                "page_count":   document.page_count,
            }
        )
