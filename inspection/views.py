# inspection/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Inspection
from .serializers import InspectionSerializer
from rooms.models import Room
from rooms.serializers import RoomSerializer
from users.permissions import IsAdminOrOfficer

class InspectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room Inspections.
    - Restricted to Administrators and Boarding Officers.
    - Set inspected_by on creation.
    - Support listing uninspected rooms.
    """
    queryset = Inspection.objects.all().order_by('-inspection_date')
    serializer_class = InspectionSerializer
    permission_classes = [IsAdminOrOfficer]

    def perform_create(self, serializer):
        serializer.save(inspected_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='uninspected')
    def uninspected(self, request):
        """
        List all rooms that have not been inspected within the last 7 days.
        """
        days = 7
        # Allow customizing the threshold via query parameter, e.g., ?days=14
        days_param = request.query_params.get('days')
        if days_param and days_param.isdigit():
            days = int(days_param)
            
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get IDs of rooms inspected since cutoff
        recent_inspections = Inspection.objects.filter(inspection_date__gte=cutoff_date)
        inspected_room_ids = recent_inspections.values_list('room_id', flat=True).distinct()
        
        # Exclude those rooms to find uninspected ones
        uninspected_rooms = Room.objects.exclude(id__in=inspected_room_ids).order_by('dorm_name', 'room_number')
        
        serializer = RoomSerializer(uninspected_rooms, many=True)
        return Response(serializer.data)
