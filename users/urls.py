# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView,
)
from .views import UserViewSet, SignupView, VerifyOTPView, ResendOTPView, ForgotPasswordView, ResetPasswordView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [

    # ── Public (no token required) ─────────────────────────
    path('auth/signup/',          SignupView.as_view(),          name='signup'),
    path('auth/verify-otp/',      VerifyOTPView.as_view(),      name='verify-otp'),
    path('auth/resend-otp/',      ResendOTPView.as_view(),      name='resend-otp'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/',  ResetPasswordView.as_view(),  name='reset-password'),

    # ── JWT token endpoints ────────────────────────────────
    path('token/',         TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),
    path('token/verify/',  TokenVerifyView.as_view(),     name='token_verify'),

    # ── Protected user management ──────────────────────────
    path('', include(router.urls)),
]

# ── Full endpoint reference ────────────────────────────────
#
# PUBLIC (no token):
#   POST  /api/auth/signup/          Register as parent or officer
#   POST  /api/auth/verify-otp/      Verify OTP → activate account
#   POST  /api/auth/resend-otp/      Resend OTP (can switch email/phone)
#   POST  /api/token/                Login → access + refresh tokens
#   POST  /api/token/refresh/        Refresh access token
#   POST  /api/token/verify/         Check if token is valid
#
# PROTECTED (Bearer token required):
#   GET    /api/users/                    List all users [Admin]
#   POST   /api/users/                    Create admin/officer [Admin]
#   GET    /api/users/me/                 Own profile [Any auth]
#   POST   /api/users/change_password/    Change own password [Any auth]
#   GET    /api/users/by_role/            Filter by role [Admin]
#   GET    /api/users/{id}/               Get user [Admin or Owner]
#   PATCH  /api/users/{id}/               Update user [Admin or Owner]
#   DELETE /api/users/{id}/               Soft deactivate [Admin]
#   POST   /api/users/{id}/reset_password/  Reset password [Admin]
#   POST   /api/users/{id}/deactivate/    Deactivate [Admin]
#   POST   /api/users/{id}/activate/      Activate [Admin]