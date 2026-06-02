"""URL routes for the Customer Module."""

from django.urls import path
from .views import (
    DocumentUploadView,
    DocumentListView,
    DocumentDetailView,
    DocumentStatusView,
    FeedbackCreateView,
    FeedbackListView,
    ComplaintCreateView,
    ComplaintListView,
    InboxListView,
    InboxMarkReadView,
)

urlpatterns = [
    # Documents
    path("documents/",                  DocumentUploadView.as_view(),  name="customer-document-upload"),
    path("documents/list/",             DocumentListView.as_view(),    name="customer-document-list"),
    path("documents/<int:pk>/",         DocumentDetailView.as_view(),  name="customer-document-detail"),
    path("documents/<int:pk>/status/",  DocumentStatusView.as_view(),  name="customer-document-status"),

    # Feedback / reviews
    path("feedbacks/",      FeedbackCreateView.as_view(), name="customer-feedback-create"),
    path("feedbacks/list/", FeedbackListView.as_view(),   name="customer-feedback-list"),

    # Complaints
    path("complaints/",      ComplaintCreateView.as_view(), name="customer-complaint-create"),
    path("complaints/list/", ComplaintListView.as_view(),   name="customer-complaint-list"),

    # Inbox
    path("inbox/",                  InboxListView.as_view(),     name="customer-inbox"),
    path("inbox/<int:pk>/read/",    InboxMarkReadView.as_view(), name="customer-inbox-read"),
]
