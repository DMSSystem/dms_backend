# users/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.db import transaction

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
)
from .permissions import IsAdmin, IsOwnerOrAdmin
from students.models import Student


# ============================================================
# PUBLIC SIGNUP VIEWS (No authentication required)
# ============================================================

class ParentSignUpView(generics.CreateAPIView):
    """
    Public endpoint for parents to create their own account.
    No admin approval needed - fully automatic.
    Parents must provide a valid student admission number.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable JWT authentication for signup
    serializer_class = UserCreateSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Get parent information
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        phone = request.data.get('phone', '')
        student_admission_no = request.data.get('student_admission_no')
        
        # Validate required fields
        if not all([username, email, password, confirm_password, student_admission_no]):
            return Response(
                {'error': 'All fields (username, email, password, confirm_password, student_admission_no) are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify student exists
        try:
            student = Student.objects.get(admission_no=student_admission_no)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student with this admission number not found. Please contact the school.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if student already has a parent
        if hasattr(student, 'parent') and student.parent:
            return Response(
                {'error': f'Student {student.full_name} already has a registered parent. Contact admin if this is an error.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email exists
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password match
        if password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create parent account - ACTIVE IMMEDIATELY
        user = User.objects.create_user(
            username=username,
            email=email.lower(),
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='parent',
            phone=phone,
            is_active=True
        )
        
        # Link parent to student
        student.parent = user
        student.save()
        
        # Send welcome email (optional - can be commented out during development)
        try:
            send_mail(
                'Welcome to Dormitory Management System',
                f'''
                Dear {username},
                
                Your account has been successfully created and linked to:
                Student: {student.full_name}
                Admission Number: {student_admission_no}
                
                You can now login to:
                - View your child's leave requests
                - Receive dormitory updates
                - Get important notifications
                
                Login at your school's DMS portal.
                
                Best regards,
                DMS Team
                ''',
                'noreply@dms.com',
                [email],
                fail_silently=True,
            )
        except Exception:
            # Don't fail signup if email fails
            pass
        
        return Response({
            'message': 'Account created successfully! You can now login.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'linked_student': student.full_name,
                'admission_no': student.admission_no
            }
        }, status=status.HTTP_201_CREATED)


class StaffSignUpView(generics.CreateAPIView):
    """
    Public endpoint for staff/boarding officers to create their own account.
    No admin approval needed - fully automatic.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable JWT authentication for signup
    serializer_class = UserCreateSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        phone = request.data.get('phone', '')
        
        # Validate required fields
        if not all([username, email, password, confirm_password]):
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email exists
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password match
        if password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create staff account - ACTIVE IMMEDIATELY
        user = User.objects.create_user(
            username=username,
            email=email.lower(),
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='officer',
            phone=phone,
            is_active=True
        )
        
        # Send welcome email (optional)
        try:
            send_mail(
                'Welcome to Dormitory Management System - Staff Portal',
                f'''
                Dear {username},
                
                Your staff account has been successfully created.
                
                You can now login to:
                - Submit leave requests for students
                - Report maintenance issues
                - View duty rosters
                - Record room inspections
                
                Login at your school's DMS portal.
                
                Best regards,
                DMS Team
                ''',
                'noreply@dms.com',
                [email],
                fail_silently=True,
            )
        except Exception:
            pass
        
        return Response({
            'message': 'Staff account created successfully! You can now login.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone
            }
        }, status=status.HTTP_201_CREATED)


# ============================================================
# USER VIEWSET (Protected endpoints)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management.

    Endpoints generated:
      GET    /users/              → list all users       [Admin only]
      POST   /users/              → create user          [Public - signup]
      GET    /users/{id}/         → retrieve user        [Admin or Owner]
      PUT    /users/{id}/         → full update          [Admin only]
      PATCH  /users/{id}/         → partial update       [Admin or Owner]
      DELETE /users/{id}/         → deactivate user      [Admin only]

    Custom actions:
      GET    /users/me/                    → current user profile
      POST   /users/change_password/       → change own password
      POST   /users/{id}/reset_password/   → admin resets any password
      POST   /users/{id}/deactivate/       → admin deactivates a user
      POST   /users/{id}/activate/         → admin reactivates a user
      GET    /users/by_role/?role=officer  → filter users by role
    """

    queryset = User.objects.all().order_by('username')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]  # Signup is public
        if self.action in ['me', 'change_password', 'partial_update']:
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy', 'reset_password',
                           'deactivate', 'activate', 'list', 'by_role']:
            return [IsAdmin()]
        return [IsOwnerOrAdmin()]

    # ── Standard CRUD overrides ─────────────────────────────

    def destroy(self, request, *args, **kwargs):
        """
        Override delete: deactivate instead of hard delete.
        Preserves referential integrity for audit logs and related records.
        """
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response(
            {"detail": f"User '{user.username}' has been deactivated."},
            status=status.HTTP_200_OK
        )

    # ── Custom actions ──────────────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return the currently authenticated user's profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='change_password')
    def change_password(self, request):
        """Allow any authenticated user to change their own password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin],
            url_path='reset_password')
    def reset_password(self, request, pk=None):
        """Allow an admin to reset any user's password."""
        user = self.get_object()
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"detail": f"Password for '{user.username}' has been reset."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.is_active:
            return Response(
                {"detail": "This account is already inactive."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response({"detail": f"User '{user.username}' has been deactivated."})

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Reactivate a previously deactivated user account."""
        user = self.get_object()
        if user.is_active:
            return Response(
                {"detail": "This account is already active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = True
        user.save()
        return Response({"detail": f"User '{user.username}' has been activated."})

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin],
            url_path='by_role')
    def by_role(self, request):
        """Filter users by role. e.g. /users/by_role/?role=officer"""
        role = request.query_params.get('role')
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if not role:
            return Response(
                {"detail": f"Provide a role query param. Options: {', '.join(valid_roles)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if role not in valid_roles:
            return Response(
                {"detail": f"Invalid role. Options: {', '.join(valid_roles)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        users = self.queryset.filter(role=role)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)