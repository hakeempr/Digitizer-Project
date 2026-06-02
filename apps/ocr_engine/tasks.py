"""
Celery tasks for the OCR Engine.

process_document_task:
  1. Load DigitizedDocument
  2. Pre-process image (OpenCV)
  3. Run OCR via OCR.space API — with bounding box overlay
  4. Smart layout analysis (word heights + position + content)
  5. Generate styled PDF
  6. Save output, mark document COMPLETED
"""

import logging
from django.utils import timezone
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_document_task(self, document_id: int):
    """Full pipeline: OCR → Smart Layout → PDF"""
    from apps.customer_module.models import DigitizedDocument
    from apps.ocr_engine.services import OCRSpaceClient, SmartLayoutAnalyser
    from apps.document_generator.services import PDFGenerator

    # ── 1. Fetch document ─────────────────────────────────────────────────────
    try:
        document = DigitizedDocument.objects.get(pk=document_id)
    except DigitizedDocument.DoesNotExist:
        logger.error("process_document_task: Document #%d not found.", document_id)
        return

    document.status        = DigitizedDocument.Status.PROCESSING
    document.error_message = ""
    document.save(update_fields=["status", "error_message"])

    try:
        image_path = document.uploaded_file.path

        # ── 2. OCR (with bounding box overlay) ───────────────────────────────
        logger.info("Starting OCR for document #%d", document_id)
        client     = OCRSpaceClient()
        ocr_result = client.run_ocr(image_path)

        if not ocr_result["success"]:
            raise RuntimeError(f"OCR failed: {ocr_result['error']}")

        raw_text   = ocr_result["full_text"]
        lines      = ocr_result["lines"]
        page_count = ocr_result["pages"]
        overlay    = ocr_result.get("overlay")   # bounding box data

        # ── 3. Smart Layout Analysis ──────────────────────────────────────────
        logger.info("Running smart layout analysis for document #%d", document_id)
        analyser = SmartLayoutAnalyser()
        blocks   = analyser.analyse(lines, overlay=overlay)

        # ── 4. PDF Generation ─────────────────────────────────────────────────
        logger.info("Generating PDF for document #%d", document_id)
        generator    = PDFGenerator(style_name=document.style_template)
        pdf_filepath = generator.generate(
            blocks      = blocks,
            title       = document.title or f"Document #{document_id}",
            customer_id = document.customer_id,
            doc_id      = document_id,
        )

        # ── 5. Save results ───────────────────────────────────────────────────
        from django.conf import settings
        from pathlib import Path

        relative_path          = Path(pdf_filepath).relative_to(settings.MEDIA_ROOT)
        document.output_pdf    = str(relative_path)
        document.raw_ocr_text  = raw_text
        document.page_count    = page_count
        document.status        = DigitizedDocument.Status.COMPLETED
        document.completed_at  = timezone.now()
        document.save(update_fields=[
            "output_pdf", "raw_ocr_text", "page_count",
            "status", "completed_at", "error_message",
        ])

        logger.info("Document #%d completed successfully.", document_id)

    except Exception as exc:
        logger.exception(
            "process_document_task failed for document #%d: %s", document_id, exc
        )
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            document.status        = DigitizedDocument.Status.FAILED
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message"])
