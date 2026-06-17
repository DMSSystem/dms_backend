# leave_out/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.core.mail import send_mail
from .models import LeaveOut
from .serializers import LeaveOutSerializer
from users.permissions import IsAdmin, IsAdminOrOfficer

class LeaveOutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Leave-Out requests.
    - Admins and Officers can view all requests and submit new requests.
    - Admins can approve or reject requests.
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
        
        # Apply role-based filtering
        if user.is_parent:
            queryset = queryset.filter(student__parent=user)
        
        # Apply overdue filter if specified
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                return_date__lt=timezone.now().date()
            ).exclude(status='completed')
            
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_admin or user.is_officer):
            raise PermissionDenied("Only administrators and boarding officers can submit leave-out requests.")
        serializer.save()

    @action(detail=True, methods=['put', 'post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        """
        Approve or reject a leave-out request.
        Admins only. Sends notification email to parent/guardian.
        Expects payload: {"status": "approved" | "rejected"}
        """
        leave_out = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['approved', 'rejected', 'completed', 'pending']:
            return Response(
                {"error": "Invalid status. Choose approved, rejected, completed, or pending."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        leave_out.status = new_status
        if new_status in ['approved', 'rejected']:
            leave_out.approved_by = request.user
        leave_out.save()
        
        # Notify Parent/Guardian of status change
        student = leave_out.student
        parent = student.parent
        if parent and parent.email and new_status in ['approved', 'rejected']:
            try:
                send_mail(
                    f"Student Leave-Out Status: {new_status.capitalize()}",
                    f"Dear {parent.full_name or parent.username},\n\n"
                    f"This is to notify you that the leave-out request for your child, "
                    f"{student.full_name} (Adm: {student.admission_no}), from {leave_out.leave_date} "
                    f"to {leave_out.return_date} has been {new_status.upper()}.\n\n"
                    f"Reason for request: {leave_out.reason}\n\n"
                    f"Best regards,\n"
                    f"Dormitory Management System",
                    "noreply@dms.com",
                    [parent.email],
                    fail_silently=True
                )
            except Exception:
                pass
                
        serializer = self.get_serializer(leave_out)
        return Response(serializer.data)
