# rooms/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Room, Dorm, AcademicTerm
from .serializers import RoomSerializer, DormSerializer, AcademicTermSerializer
from users.permissions import IsAdminOrReadOnly, IsAdmin

class DormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dorm management.
    - Admins have full CRUD access.
    - Others have read-only access.
    """
    queryset = Dorm.objects.all().order_by('name')
    serializer_class = DormSerializer
    permission_classes = [IsAdminOrReadOnly]
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
    - Admins have full CRUD access.
    - Others have read-only access.
    """
    queryset = Room.objects.all().select_related('dorm').order_by('dorm__name', 'room_number')
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class AcademicTermViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Academic Term management.
    - Admins have full CRUD access.
    - Other authenticated users have read-only access.
    """
    queryset = AcademicTerm.objects.all().order_by('-start_date')
    serializer_class = AcademicTermSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
