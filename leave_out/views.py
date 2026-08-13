# leave_out/views.py
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.core.mail import send_mail
from .models import LeaveOut, ContactAttempt
from .serializers import LeaveOutSerializer, ContactAttemptSerializer
from users.permissions import IsAdmin, IsAdminOrOfficer

logger = logging.getLogger(__name__)

class LeaveOutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Leave-Out requests.
    - Admins and Officers can view all requests and submit new requests.
    - Admins can approve, reject, complete, or escalate requests.
    - Officers can mark completed, escalate overdue leaves, or log contact attempts.
    - Parents can view only their child's requests (read-only).
    """
    serializer_class = LeaveOutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return LeaveOut.objects.none()
        
        # Start with base queryset
        queryset = LeaveOut.objects.all().order_by('-leave_date')
        
        # Apply role-based filtering (support multi-parent M2M and single parent)
        if user.is_parent:
            queryset = queryset.filter(student__parents=user)
        
        # Apply overdue filter if specified
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                status__in=['approved', 'escalated'],
                return_date__lt=timezone.now().date()
            )

        # Apply overdue_severity filter
        severity = self.request.query_params.get('overdue_severity')
        if severity and severity in ['minor', 'moderate', 'critical']:
            today = timezone.now().date()
            if severity == 'minor':
                queryset = queryset.filter(
                    status__in=['approved', 'escalated'],
                    return_date__exact=today - timezone.timedelta(days=1)
                )
            elif severity == 'moderate':
                queryset = queryset.filter(
                    status__in=['approved', 'escalated'],
                    return_date__range=[
                        today - timezone.timedelta(days=3),
                        today - timezone.timedelta(days=2)
                    ]
                )
            elif severity == 'critical':
                queryset = queryset.filter(
                    status__in=['approved', 'escalated'],
                    return_date__lt=today - timezone.timedelta(days=3)
                )
            
        return queryset.select_related(
            'student', 'student__room', 'student__room__dorm', 'approved_by', 'returned_by'
        ).prefetch_related(
            'student__parents', 'student__emergency_contacts', 'contact_attempts', 'contact_attempts__performed_by'
        )

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_admin or user.is_officer):
            raise PermissionDenied("Only administrators and boarding officers can submit leave-out requests.")
        serializer.save()

    @action(detail=True, methods=['put', 'post'], permission_classes=[IsAdminOrOfficer])
    def approve(self, request, pk=None):
        """
        Change the status of a leave-out request.
        - Admins: can set status to approved, rejected, completed, pending, or escalated.
        - Officers: can set completed or escalated (for missing/overdue students or reopening mistakes).
        Sends notification email to parent/guardian on approve/reject/escalated.
        Expects payload: {"status": "approved" | "rejected" | "completed" | "pending" | "escalated"}
        """
        leave_out = self.get_object()
        new_status = request.data.get('status')
        user = request.user

        if new_status not in ['approved', 'rejected', 'completed', 'pending', 'escalated']:
            return Response(
                {"error": "Invalid status. Choose approved, rejected, completed, pending, or escalated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Officers may mark completed (student returned) or escalated (student missing/overdue)
        if user.is_officer and new_status not in ['completed', 'escalated']:
            raise PermissionDenied(
                "Boarding Officers can mark a leave as completed or escalated. "
                "Approving or rejecting a leave request requires an Administrator."
            )

        leave_out.status = new_status
        if new_status in ['approved', 'rejected']:
            leave_out.approved_by = request.user
        if new_status == 'completed':
            leave_out.returned_by = request.user
            leave_out.returned_at = timezone.now()
        elif new_status in ['approved', 'escalated', 'pending']:
            # Reopening or clearing returned info if status is moved out of completed
            leave_out.returned_by = None
            leave_out.returned_at = None

        leave_out.save()
        
        # Notify Parent/Guardian of status change
        student = leave_out.student
        parents = student.parents.all()
        parent_emails = [p.email for p in parents if p.email]

        if parent_emails and new_status in ['approved', 'rejected', 'escalated']:
            try:
                send_mail(
                    f"Student Leave-Out Status Update: {new_status.capitalize()}",
                    f"This is to notify you that the leave-out request for "
                    f"{student.full_name} (Adm: {student.admission_no}), from {leave_out.leave_date} "
                    f"to {leave_out.return_date} is now marked as {new_status.upper()}\n\n"
                    f"Reason for request: {leave_out.reason}\n\n"
                    f"Best regards,\n\n"
                    f"Dormitory Management System",
                    "noreply@dms.com",
                    parent_emails,
                    fail_silently=False
                )
            except Exception as e:
                logger.error(
                    f"Failed to send parent notification email for student {student.admission_no} "
                    f"to {', '.join(parent_emails)}: {str(e)}",
                    exc_info=True
                )
        serializer = self.get_serializer(leave_out)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrOfficer])
    def log_contact(self, request, pk=None):
        """
        Record a contact attempt (phone call, SMS, etc.) for an overdue or active leave.
        """
        leave_out = self.get_object()
        serializer = ContactAttemptSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(leave_out=leave_out, performed_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)