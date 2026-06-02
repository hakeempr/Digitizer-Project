"""URL routes for the Admin Module."""

from django.urls import path
from .views import (
    AdminDashboardView,
    AccountRequestListView,
    AccountRequestDetailView,
    AccountDecisionView,
    AdminComplaintListView,
    AdminComplaintDetailView,
    AdminComplaintReplyView,
    AdminFeedbackListView,
    AdminFeedbackReplyView,
)

urlpatterns = [
    # Dashboard
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),

    # Account approval queue
    path("account-requests/",          AccountRequestListView.as_view(),   name="admin-account-request-list"),
    path("account-requests/<int:pk>/", AccountRequestDetailView.as_view(), name="admin-account-request-detail"),
    path("account-requests/<int:pk>/decide/", AccountDecisionView.as_view(), name="admin-account-decide"),

    # Complaints
    path("complaints/",                AdminComplaintListView.as_view(),   name="admin-complaint-list"),
    path("complaints/<int:pk>/",       AdminComplaintDetailView.as_view(), name="admin-complaint-detail"),
    path("complaints/<int:pk>/reply/", AdminComplaintReplyView.as_view(),  name="admin-complaint-reply"),

    # Feedback / Reviews
    path("feedbacks/",                AdminFeedbackListView.as_view(),  name="admin-feedback-list"),
    path("feedbacks/<int:pk>/reply/", AdminFeedbackReplyView.as_view(), name="admin-feedback-reply"),
]
