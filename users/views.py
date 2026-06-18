# users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.db import transaction

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, PasswordResetSerializer,
    SignupSerializer, OTPVerifySerializer, ResendOTPSerializer,
)
from .permissions import IsAdmin, IsOwnerOrAdmin
from .utils import send_otp


# ════════════════════════════════════════════════════════════
# PUBLIC AUTH VIEWS  (no token required)
# ════════════════════════════════════════════════════════════

class SignupView(APIView):
    """
    POST /api/auth/signup/

    Single unified signup for parent and officer roles.
    Admin accounts cannot be self-registered.
    OTP is always sent to the user's email address.

    Required fields (all roles):
      - username, email, first_name, last_name
      - role              : 'parent' or 'officer'
      - password, confirm_password

    Required fields (parent only):
      - student_admission_no : admission number of the parent's child

    Optional:
      - phone

    Flow:
      1. POST /api/auth/signup/       → account created (inactive), OTP sent to email
      2. POST /api/auth/verify-otp/   → account activated
      3. POST /api/token/             → login and get JWT tokens
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        success, _ = send_otp(user, method='email')

        if not success:
            return Response({
                "detail": (
                    "Account created but we could not send the verification email. "
                    "Use POST /api/auth/resend-otp/ to try again."
                ),
                "username": user.username,
                "next_step": "POST /api/auth/resend-otp/",
            }, status=status.HTTP_201_CREATED)

        return Response({
            "detail": (
                f"Account created successfully. A 6-digit verification code "
                f"has been sent to {user.email}. "
                f"Verify your account to activate it."
            ),
            "username": user.username,
            "role": user.role,
            "next_step": "POST /api/auth/verify-otp/",
        }, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp/

    Verifies the OTP sent to the user's email and activates the account.
    After success the user can log in via POST /api/token/.

    Body:
      - username  : the username used during signup
      - otp_code  : the 6-digit code received via email
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        user.mark_verified()

        return Response({
            "detail": "Account verified and activated successfully.",
            "username": user.username,
            "role": user.role,
            "next_step": "POST /api/token/ to log in.",
        }, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/

    Resends a fresh OTP to the user's registered email address.
    Use this if the previous code expired or was not received.

    Body:
      - username : the username used during signup
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        success, _ = send_otp(user, method='email')

        if not success:
            return Response(
                {"detail": "Failed to send verification email. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({
            "detail": f"A new verification code has been sent to {user.email}.",
            "username": user.username,
        }, status=status.HTTP_200_OK)


# ════════════════════════════════════════════════════════════
# USER MANAGEMENT VIEWSET  (token required)
# ════════════════════════════════════════════════════════════

class UserViewSet(viewsets.ModelViewSet):
    """
    Full user management ViewSet. Most actions require admin access.

    GET    /api/users/                       List all users [Admin]
    POST   /api/users/                       Create admin/officer directly [Admin]
    GET    /api/users/{id}/                  Get user [Admin or Owner]
    PUT    /api/users/{id}/                  Full update [Admin]
    PATCH  /api/users/{id}/                  Partial update [Authenticated]
    DELETE /api/users/{id}/                  Soft deactivate [Admin]
    GET    /api/users/me/                    Current user profile [Any auth]
    POST   /api/users/change_password/       Change own password [Any auth]
    POST   /api/users/{id}/reset_password/   Reset any password [Admin]
    POST   /api/users/{id}/deactivate/       Deactivate account [Admin]
    POST   /api/users/{id}/activate/         Activate account [Admin]
    GET    /api/users/by_role/?role=officer  Filter by role [Admin]
    """

    queryset = User.objects.all().order_by('username')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['me', 'change_password', 'partial_update']:
            return [IsAuthenticated()]
        if self.action in ['create', 'update', 'destroy', 'reset_password',
                           'deactivate', 'activate', 'list', 'by_role']:
            return [IsAdmin()]
        return [IsOwnerOrAdmin()]

    def destroy(self, request, *args, **kwargs):
        """Soft delete — sets is_active=False, never hard deletes."""
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated],
            url_path='change_password')
    def change_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password changed successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin],
            url_path='reset_password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": f"Password for '{user.username}' has been reset."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deactivate(self, request, pk=None):
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
        role = request.query_params.get('role')
        valid = [r[0] for r in User.ROLE_CHOICES]
        if not role:
            return Response(
                {"detail": f"Provide a role param. Options: {', '.join(valid)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if role not in valid:
            return Response(
                {"detail": f"Invalid role. Options: {', '.join(valid)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserSerializer(self.get_queryset().filter(role=role), many=True)
        return Response(serializer.data)