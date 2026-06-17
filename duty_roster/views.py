# duty_roster/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from .models import DutyRoster, DutyAssignment
from .serializers import DutyRosterSerializer, DutyAssignmentSerializer
from users.permissions import IsAdminOrReadOnly

class IsAdminOrOfficerForAssignment(permissions.BasePermission):
    """
    Custom permission for DutyAssignment:
    - Admin: full access (CRUD).
    - Officer: list, retrieve, and update (cannot delete).
    - Parent: list and retrieve only (filtered to child).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_admin or request.user.is_officer

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if request.user.is_officer:
            return request.method != 'DELETE'
        if request.user.is_parent:
            return request.method in permissions.SAFE_METHODS and obj.student.parent == request.user
        return False


class DutyRosterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Duty Roster management.
    - Admin: Full CRUD.
    - Officer: Read-only.
    - Parent: Read-only, filtered to rosters containing assignments for their child.
    """
    serializer_class = DutyRosterSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return DutyRoster.objects.none()
        
        queryset = DutyRoster.objects.all().order_by('duty_date', 'dorm_name')
        
        if user.is_parent:
            queryset = queryset.filter(assigned_students__parent=user).distinct()
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Duty Assignment tracking.
    - Admin: Full CRUD.
    - Officer: View all, update completion status and remarks (no delete).
    - Parent: View only their child's assignments (read-only).
    """
    serializer_class = DutyAssignmentSerializer
    permission_classes = [IsAdminOrOfficerForAssignment]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return DutyAssignment.objects.none()
        
        queryset = DutyAssignment.objects.all().order_by('duty_roster__duty_date', 'student__full_name')
        
        if user.is_parent:
            queryset = queryset.filter(student__parent=user)
            
        return queryset

    def perform_update(self, serializer):
        status_value = serializer.validated_data.get('status')
        if status_value == 'completed':
            if not self.get_object().status == 'completed':
                serializer.save(completed_at=timezone.now())
                return
        elif status_value and status_value != 'completed':
            # Clear completed_at if status changed back from completed
            serializer.save(completed_at=None)
            return
            
        serializer.save()
