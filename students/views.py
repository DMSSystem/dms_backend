# students/views.py
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Student, EmergencyContact
from .serializers import StudentSerializer, EmergencyContactSerializer
from users.permissions import IsAdminOrOfficerOrReadOnly, IsAdminOrOfficer

from rest_framework.decorators import action

class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Student management.
    - Admin and Officer have full CRUD.
    - Parent has read-only access to their own child.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Student.objects.none()
        
        queryset = Student.objects.none()
        if user.is_admin or user.is_officer:
            queryset = Student.objects.all()
        elif user.is_parent:
            queryset = Student.objects.filter(parents=user)

        # Optional query parameters
        status_param = self.request.query_params.get('status')
        if status_param and queryset.exists():
            queryset = queryset.filter(status=status_param)

        return queryset.select_related('room', 'room__dorm').prefetch_related('parents', 'emergency_contacts')

    @action(detail=False, methods=['post'], url_path='bulk-import', permission_classes=[IsAdminOrOfficer])
    def bulk_import(self, request):
        """
        Bulk import students from JSON array of student data.
        """
        students_data = request.data.get('students', [])
        if not isinstance(students_data, list) or len(students_data) == 0:
            return Response({'error': 'Please provide a non-empty list of students.'}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        errors = []

        for idx, item in enumerate(students_data):
            serializer = StudentSerializer(data=item)
            if serializer.is_valid():
                serializer.save()
                created_count += 1
            else:
                errors.append({
                    'row': idx + 1,
                    'admission_no': item.get('admission_no', 'N/A'),
                    'errors': serializer.errors
                })

        return Response({
            'message': f"Successfully imported {created_count} student(s).",
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_count > 0 else status.HTTP_400_BAD_REQUEST)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Emergency Contact management.
    - Admin and Officer have full CRUD.
    - Parent has read-only access to active emergency contacts of their child.
    """
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAdminOrOfficerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EmergencyContact.objects.none()
        if user.is_admin or user.is_officer:
            return EmergencyContact.objects.all()
        if user.is_parent:
            return EmergencyContact.objects.filter(student__parents=user, is_active=True)
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
            return get_object_or_404(Student, admission_no=admission_no, parents=user)
        
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
            return Student.objects.filter(room_id=room_id, parents=user)
        return Student.objects.none()
