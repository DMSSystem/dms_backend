# rooms/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
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
    pagination_class = None

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.rooms.filter(current_occupancy__gt=0).exists():
            return Response(
                {"detail": "Cannot delete dormitory because it contains occupied rooms."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Room management.
    - Admins and Boarding Officers have full CRUD access.
    - Parents have read-only access.
    """
    queryset = Room.objects.all().select_related('dorm').order_by('dorm__name', 'room_number')
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]
    pagination_class = None

