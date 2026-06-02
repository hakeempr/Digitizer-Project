"""
Document Generator Views.

Covers:
  - PDF download (serve file)
  - Notion-style HTML export
  - Re-generate with a different style template
  - List available style templates
"""

import os
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.permissions import IsApprovedCustomer, IsAdmin
from apps.customer_module.models import DigitizedDocument


class DownloadPDFView(APIView):
    """
    GET /api/v1/documents/<doc_id>/download/
    Streams the generated PDF to the client.
    """

    permission_classes = [IsApprovedCustomer]

    def get(self, request, doc_id):
        qs = DigitizedDocument.objects.filter(pk=doc_id)
        if not request.user.is_admin:
            qs = qs.filter(customer=request.user)

        try:
            doc = qs.get()
        except DigitizedDocument.DoesNotExist:
            raise Http404

        if doc.status != DigitizedDocument.Status.COMPLETED or not doc.output_pdf:
            return Response(
                {"detail": "PDF is not yet available. Check the document status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pdf_path = doc.output_pdf.path
        if not os.path.exists(pdf_path):
            return Response(
                {"detail": "PDF file not found on disk. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f"digitized_document_{doc_id}.pdf"
        response = FileResponse(
            open(pdf_path, "rb"),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ExportHTMLView(APIView):
    """
    GET /api/v1/documents/<doc_id>/export/html/
    Returns a Notion-style HTML rendering of the document.
    """

    permission_classes = [IsApprovedCustomer]

    def get(self, request, doc_id):
        qs = DigitizedDocument.objects.filter(pk=doc_id)
        if not request.user.is_admin:
            qs = qs.filter(customer=request.user)

        try:
            doc = qs.get()
        except DigitizedDocument.DoesNotExist:
            raise Http404

        if doc.status != DigitizedDocument.Status.COMPLETED:
            return Response(
                {"detail": "Document processing is not complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.ocr_engine.services import LayoutAnalyser
        from apps.document_generator.services import NotionHTMLExporter

        lines    = [l for l in doc.raw_ocr_text.splitlines() if l]
        blocks   = LayoutAnalyser().analyse(lines)
        exporter = NotionHTMLExporter()
        html     = exporter.export(
            blocks     = blocks,
            title      = doc.title or f"Document #{doc_id}",
            created_at = doc.created_at.strftime("%B %d, %Y"),
        )

        from django.http import HttpResponse
        return HttpResponse(html, content_type="text/html")


class RegenerateDocumentView(APIView):
    """
    POST /api/v1/documents/<doc_id>/regenerate/
    Body: { "style_template": "academic" | "notion" | "minimal" | "default" }

    Re-runs PDF generation (skipping OCR) with a new style template.
    The existing raw_ocr_text is re-used to save API quota.
    """

    permission_classes = [IsApprovedCustomer]

    def post(self, request, doc_id):
        from django.conf import settings

        qs = DigitizedDocument.objects.filter(pk=doc_id)
        if not request.user.is_admin:
            qs = qs.filter(customer=request.user)

        try:
            doc = qs.get()
        except DigitizedDocument.DoesNotExist:
            raise Http404

        if doc.status != DigitizedDocument.Status.COMPLETED:
            return Response(
                {"detail": "Can only regenerate completed documents."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_style = request.data.get("style_template", "default")
        valid_styles = list(settings.DOCUMENT_STYLE_TEMPLATES.keys())
        if new_style not in valid_styles:
            return Response(
                {"detail": f"Invalid style. Choose from: {', '.join(valid_styles)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.ocr_engine.services import LayoutAnalyser
        from apps.document_generator.services import PDFGenerator

        lines     = [l for l in doc.raw_ocr_text.splitlines() if l]
        blocks    = LayoutAnalyser().analyse(lines)
        generator = PDFGenerator(style_name=new_style)
        pdf_path  = generator.generate(
            blocks      = blocks,
            title       = doc.title or f"Document #{doc_id}",
            customer_id = doc.customer_id,
            doc_id      = doc_id,
        )

        from django.conf import settings as s
        from pathlib import Path

        relative_path      = Path(pdf_path).relative_to(s.MEDIA_ROOT)
        doc.output_pdf     = str(relative_path)
        doc.style_template = new_style
        doc.save(update_fields=["output_pdf", "style_template"])

        return Response(
            {
                "message":        f"Document re-generated with '{new_style}' template.",
                "style_template": new_style,
                "document_id":    doc_id,
            }
        )


class StyleTemplateListView(APIView):
    """
    GET /api/v1/documents/styles/
    Returns available style templates and their configuration.
    """

    permission_classes = [IsApprovedCustomer]

    def get(self, request):
        from django.conf import settings
        templates = settings.DOCUMENT_STYLE_TEMPLATES
        return Response(
            {
                "available_styles": list(templates.keys()),
                "details": {
                    name: {
                        "font_family": cfg["font_family"],
                        "font_size":   cfg["font_size"],
                        "line_spacing": cfg["line_spacing"],
                    }
                    for name, cfg in templates.items()
                },
            }
        )
