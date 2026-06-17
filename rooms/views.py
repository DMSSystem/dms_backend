# rooms/views.py
from rest_framework import viewsets
from .models import Room
from .serializers import RoomSerializer
from users.permissions import IsAdminOrOfficerOrReadOnly

class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room management.
    - Admins and Boarding Officers have full CRUD access.
    - Parents have read-only access.
    """
    queryset = Room.objects.all().order_by('dorm_name', 'room_number')
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]
