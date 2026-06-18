# rooms/views.py
from rest_framework import viewsets
from .models import Room, Dorm
from .serializers import RoomSerializer, DormSerializer
from users.permissions import IsAdminOrOfficerOrReadOnly

class DormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dorm management.
    - Admins and Boarding Officers have full CRUD access.
    - Parents have read-only access.
    """
    queryset = Dorm.objects.all().order_by('name')
    serializer_class = DormSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room management.
    - Admins and Boarding Officers have full CRUD access.
    - Parents have read-only access.
    """
    queryset = Room.objects.all().select_related('dorm').order_by('dorm__name', 'room_number')
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]

