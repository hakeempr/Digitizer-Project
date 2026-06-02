"""
Admin Module Views.

Covers:
  - Dashboard summary stats
  - Customer account approval / rejection queue
  - Complaint inbox & reply
  - Feedback/review inbox & reply
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.customer_module.models import Complaint, Feedback, DigitizedDocument
from utils.permissions import IsAdmin
from .models import AccountRequest, ComplaintReply, FeedbackReply
from .serializers import (
    AccountRequestSerializer,
    AccountDecisionSerializer,
    ComplaintReplySerializer,
    FeedbackReplySerializer,
    AdminDashboardSerializer,
)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class AdminDashboardView(APIView):
    """GET /api/v1/admin/dashboard/ — aggregated stats for the admin panel."""

    permission_classes = [IsAdmin]

    def get(self, request):
        customers = User.objects.filter(role=User.Role.CUSTOMER)
        data = {
            "total_customers":      customers.count(),
            "pending_requests":     customers.filter(
                                        account_status=User.AccountStatus.PENDING
                                    ).count(),
            "approved_customers":   customers.filter(
                                        account_status=User.AccountStatus.APPROVED
                                    ).count(),
            "rejected_customers":   customers.filter(
                                        account_status=User.AccountStatus.REJECTED
                                    ).count(),
            "total_documents":      DigitizedDocument.objects.count(),
            "open_complaints":      Complaint.objects.filter(
                                        status=Complaint.Status.OPEN
                                    ).count(),
            "unanswered_feedbacks": Feedback.objects.filter(
                                        admin_reply__isnull=True
                                    ).count(),
        }
        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)


# ─── Account Request Queue ────────────────────────────────────────────────────

class AccountRequestListView(generics.ListAPIView):
    """GET /api/v1/admin/account-requests/ — list all pending requests."""

    serializer_class   = AccountRequestSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AccountRequest.objects.select_related("customer")
        decision = self.request.query_params.get("decision")
        if decision:
            qs = qs.filter(decision=decision)
        return qs


class AccountRequestDetailView(generics.RetrieveAPIView):
    """GET /api/v1/admin/account-requests/<pk>/"""

    serializer_class   = AccountRequestSerializer
    permission_classes = [IsAdmin]
    queryset           = AccountRequest.objects.select_related("customer")


class AccountDecisionView(APIView):
    """
    POST /api/v1/admin/account-requests/<pk>/decide/
    Body: { "decision": "approved"|"rejected", "admin_notes": "..." }
    """

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            account_request = AccountRequest.objects.select_related("customer").get(pk=pk)
        except AccountRequest.DoesNotExist:
            return Response(
                {"detail": "Account request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AccountDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision    = serializer.validated_data["decision"]
        admin_notes = serializer.validated_data["admin_notes"]
        customer    = account_request.customer

        # Update the AccountRequest record
        account_request.decision    = decision
        account_request.admin_notes = admin_notes
        account_request.reviewed_by = request.user
        account_request.reviewed_at = timezone.now()
        account_request.save()

        # Update the actual User record
        if decision == "approved":
            customer.approve(notes=admin_notes)
        else:
            customer.reject(notes=admin_notes)

        return Response(
            {
                "message": f"Account {decision} for {customer.email}.",
                "decision": decision,
            }
        )


# ─── Complaint Management ─────────────────────────────────────────────────────

class AdminComplaintListView(generics.ListAPIView):
    """GET /api/v1/admin/complaints/ — list all customer complaints."""

    permission_classes = [IsAdmin]

    def get_queryset(self):
        from apps.customer_module.models import Complaint
        qs = Complaint.objects.select_related("customer")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def list(self, request, *args, **kwargs):
        from apps.customer_module.serializers import ComplaintSerializer
        qs = self.get_queryset()
        serializer = ComplaintSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class AdminComplaintDetailView(generics.RetrieveAPIView):
    """GET /api/v1/admin/complaints/<pk>/"""

    permission_classes = [IsAdmin]

    def get_queryset(self):
        from apps.customer_module.models import Complaint
        return Complaint.objects.select_related("customer")

    def retrieve(self, request, *args, **kwargs):
        from apps.customer_module.serializers import ComplaintSerializer
        obj = self.get_object()
        serializer = ComplaintSerializer(obj, context={"request": request})
        return Response(serializer.data)


class AdminComplaintReplyView(generics.CreateAPIView):
    """
    POST /api/v1/admin/complaints/<pk>/reply/
    Creates a ComplaintReply, marks the complaint as RESOLVED, and
    creates an inbox notification for the customer.
    """

    serializer_class   = ComplaintReplySerializer
    permission_classes = [IsAdmin]

    def create(self, request, pk=None):
        from apps.customer_module.models import Complaint
        from apps.notifications.models import Notification

        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response(
                {"detail": "Complaint not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if hasattr(complaint, "admin_reply"):
            return Response(
                {"detail": "This complaint already has a reply."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {**request.data, "complaint": complaint.pk}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        reply = serializer.save()

        # Mark complaint as resolved
        complaint.status = Complaint.Status.RESOLVED
        complaint.save(update_fields=["status"])

        # Notify customer via inbox
        Notification.objects.create(
            recipient=complaint.customer,
            subject=f"Re: {complaint.subject}",
            body=reply.body,
            category=Notification.Category.COMPLAINT_REPLY,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── Feedback / Review Management ─────────────────────────────────────────────

class AdminFeedbackListView(generics.ListAPIView):
    """GET /api/v1/admin/feedbacks/ — list all customer feedback."""

    permission_classes = [IsAdmin]

    def get_queryset(self):
        from apps.customer_module.models import Feedback
        return Feedback.objects.select_related("customer")

    def list(self, request, *args, **kwargs):
        from apps.customer_module.serializers import FeedbackSerializer
        qs = self.get_queryset()
        serializer = FeedbackSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class AdminFeedbackReplyView(generics.CreateAPIView):
    """
    POST /api/v1/admin/feedbacks/<pk>/reply/
    Creates a FeedbackReply and sends an inbox notification to the customer.
    """

    serializer_class   = FeedbackReplySerializer
    permission_classes = [IsAdmin]

    def create(self, request, pk=None):
        from apps.customer_module.models import Feedback
        from apps.notifications.models import Notification

        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response(
                {"detail": "Feedback not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if hasattr(feedback, "admin_reply"):
            return Response(
                {"detail": "This feedback already has a reply."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {**request.data, "feedback": feedback.pk}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        reply = serializer.save()

        # Notify customer
        Notification.objects.create(
            recipient=feedback.customer,
            subject=f"Re: Your feedback on document #{feedback.document_id}",
            body=reply.body,
            category=Notification.Category.FEEDBACK_REPLY,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
