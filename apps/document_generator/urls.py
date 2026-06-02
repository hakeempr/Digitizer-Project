"""URL routes for the Document Generator app."""

from django.urls import path
from .views import (
    DownloadPDFView,
    ExportHTMLView,
    RegenerateDocumentView,
    StyleTemplateListView,
)

urlpatterns = [
    path("styles/",                        StyleTemplateListView.as_view(),  name="doc-styles"),
    path("<int:doc_id>/download/",         DownloadPDFView.as_view(),        name="doc-download"),
    path("<int:doc_id>/export/html/",      ExportHTMLView.as_view(),         name="doc-export-html"),
    path("<int:doc_id>/regenerate/",       RegenerateDocumentView.as_view(), name="doc-regenerate"),
]
