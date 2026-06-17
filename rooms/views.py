# rooms/views.py
from rest_framework import viewsets
from .models import Room
from .serializers import RoomSerializer
from users.permissions import IsAdminOrReadOnly

class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room management.
    - Admins have full access.
    - Authenticated users (officers, parents) have read-only access.
    """
    queryset = Room.objects.all().order_by('dorm_name', 'room_number')
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]
