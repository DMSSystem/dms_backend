# maintenance/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import MaintenanceRequest
from .serializers import MaintenanceRequestSerializer
from users.permissions import IsAdminOrOfficer, IsAdmin


class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Maintenance Requests.

    Access Rules:
    - Officers: create + view/edit/delete their OWN pending requests.
    - Admins:   full access – view all, approve, reject, resolve, assign.

    Workflow:
    - Officer submits → status = 'pending'
    - Admin approves → status auto-sets to 'in_progress'
    - Admin marks resolved → status = 'resolved', resolved_date set
    - Admin rejects → status = 'rejected'
    """
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAdminOrOfficer]

    def get_queryset(self):
        user = self.request.user
        qs = MaintenanceRequest.objects.select_related(
            'reported_by', 'assigned_to', 'dorm_block'
        ).order_by('-reported_date')

        if user.is_admin:
            # Admins see everything; optional filter by dorm block
            dorm_block = self.request.query_params.get('dorm_block')
            if dorm_block:
                qs = qs.filter(dorm_block=dorm_block)
            return qs

        # Officers see only their own requests
        return qs.filter(reported_by=user)

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def perform_update(self, serializer):
        """
        Officers can only update description/location/urgency/dorm_block/remarks
        when the request is still pending.
        Admins can update status, admin_remarks, assigned_to.
        """
        user = self.request.user
        instance = self.get_object()

        if not user.is_admin:
            # Officers: only editable fields while pending
            if instance.status != 'pending':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    "You can only edit requests that are still pending."
                )
            # Strip any admin-only fields the officer might have snuck in
            allowed = ['description', 'location', 'dorm_block', 'urgency', 'remarks']
            data = {k: v for k, v in serializer.validated_data.items() if k in allowed}
            serializer.save(**{k: v for k, v in data.items()})
            return

        # Admin update logic
        new_status = serializer.validated_data.get('status', instance.status)

        if new_status == 'resolved' and instance.status != 'resolved':
            serializer.save(resolved_date=timezone.now())
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Officers can only delete their own PENDING requests."""
        instance = self.get_object()
        user = request.user

        if not user.is_admin:
            if instance.reported_by != user:
                return Response(
                    {'detail': 'You can only cancel your own requests.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if instance.status != 'pending':
                return Response(
                    {'detail': 'Only pending requests can be cancelled.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def history(self, request):
        """
        GET /maintenance/history/?dorm_block=<id>&status=<status>
        Returns maintenance history grouped per dormitory block for the report.
        """
        qs = MaintenanceRequest.objects.select_related(
            'reported_by', 'assigned_to', 'dorm_block'
        ).order_by('dorm_block__name', '-reported_date')

        dorm_block = request.query_params.get('dorm_block')
        status_filter = request.query_params.get('status')

        if dorm_block:
            qs = qs.filter(dorm_block=dorm_block)
        if status_filter:
            qs = qs.filter(status=status_filter)

        serializer = MaintenanceRequestSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        """PATCH /maintenance/<id>/approve/ → auto-set status to in_progress"""
        instance = self.get_object()
        if instance.status != 'pending':
            return Response(
                {'detail': 'Only pending requests can be approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'in_progress'
        instance.admin_remarks = request.data.get('admin_remarks', instance.admin_remarks)
        instance.save(update_fields=['status', 'admin_remarks'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        """PATCH /maintenance/<id>/reject/ → set status to rejected"""
        instance = self.get_object()
        if instance.status not in ('pending', 'in_progress'):
            return Response(
                {'detail': 'Only pending or in-progress requests can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'rejected'
        instance.admin_remarks = request.data.get('admin_remarks', instance.admin_remarks)
        instance.save(update_fields=['status', 'admin_remarks'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def resolve(self, request, pk=None):
        """PATCH /maintenance/<id>/resolve/ → set status to resolved"""
        instance = self.get_object()
        if instance.status != 'in_progress':
            return Response(
                {'detail': 'Only in-progress requests can be marked as resolved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'resolved'
        instance.resolved_date = timezone.now()
        instance.admin_remarks = request.data.get('admin_remarks', instance.admin_remarks)
        instance.save(update_fields=['status', 'resolved_date', 'admin_remarks'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
