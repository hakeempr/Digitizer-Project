"""URL routes for the OCR Engine app."""

from django.urls import path
from .views import TriggerOCRView, RawOCRResultView

urlpatterns = [
    path("trigger/<int:document_id>/", TriggerOCRView.as_view(),    name="ocr-trigger"),
    path("result/<int:document_id>/",  RawOCRResultView.as_view(),  name="ocr-result"),
]
