# students/views.py
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Student, EmergencyContact
from .serializers import StudentSerializer, EmergencyContactSerializer
from users.permissions import IsAdminOrReadOnly, IsAdminOrOfficer

class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Student management.
    - Admin has full CRUD.
    - Boarding Officer has read-only access to all students.
    - Parent has read-only access to their own child.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Student.objects.none()
        if user.is_admin or user.is_officer:
            return Student.objects.all()
        if user.is_parent:
            return Student.objects.filter(parent=user)
        return Student.objects.none()


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Emergency Contact management.
    - Admin has full CRUD.
    - Boarding Officer has read-only access to all contacts.
    - Parent has read-only access to emergency contacts of their child.
    """
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EmergencyContact.objects.none()
        if user.is_admin or user.is_officer:
            return EmergencyContact.objects.all()
        if user.is_parent:
            return EmergencyContact.objects.filter(student__parent=user)
        return EmergencyContact.objects.none()


class StudentByAdmissionView(generics.RetrieveAPIView):
    """
    Retrieve a student by admission number.
    - Admins/Officers can access any student.
    - Parents can only access their child.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        admission_no = self.kwargs.get('admission_no')
        user = self.request.user
        
        if user.is_admin or user.is_officer:
            return get_object_or_404(Student, admission_no=admission_no)
        elif user.is_parent:
            return get_object_or_404(Student, admission_no=admission_no, parent=user)
        
        # Unrecognized roles get 404/403
        return get_object_or_404(Student, id=0)


class StudentsByRoomView(generics.ListAPIView):
    """
    List all students assigned to a room.
    - Admins/Officers can see all occupants.
    - Parents can only see their own child if assigned to the room.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        user = self.request.user
        
        if user.is_admin or user.is_officer:
            return Student.objects.filter(room_id=room_id)
        elif user.is_parent:
            return Student.objects.filter(room_id=room_id, parent=user)
        return Student.objects.none()
