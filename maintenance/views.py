# maintenance/views.py
from rest_framework import viewsets, permissions
from django.utils import timezone
from .models import MaintenanceRequest
from .serializers import MaintenanceRequestSerializer
from users.permissions import IsAdminOrOfficer

class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Maintenance Requests.
    - Restricted to Administrators and Boarding Officers.
    - Set reported_by on creation.
    - Set resolved_date when status changes to 'resolved'.
    """
    queryset = MaintenanceRequest.objects.all().order_by('-reported_date')
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAdminOrOfficer]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def perform_update(self, serializer):
        # Check if status is changed to resolved
        status_value = serializer.validated_data.get('status')
        
        if status_value == 'resolved':
            # Only set resolved_date if not already set or status is updated to resolved
            if not self.get_object().status == 'resolved':
                serializer.save(resolved_date=timezone.now())
                return
        
        serializer.save()
