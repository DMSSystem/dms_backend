# audit_log/middleware.py
import threading
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

_local = threading.local()

class AuditLogMiddleware:
    """
    Middleware to capture the current authenticated user and IP address
    for signal-based audit logging. Supports both standard Django auth
    and SimpleJWT token-based auth.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        
        # If user is not authenticated yet (typical for JWT-based REST calls),
        # try to authenticate manually using SimpleJWT.
        if not user or user.is_anonymous:
            try:
                jwt_auth = JWTAuthentication()
                header = jwt_auth.get_header(request)
                if header:
                    raw_token = jwt_auth.get_raw_token(header)
                    validated_token = jwt_auth.get_validated_token(raw_token)
                    user = jwt_auth.get_user(validated_token)
            except Exception:
                pass

        _local.user = user if user and not isinstance(user, AnonymousUser) else None
        _local.ip_address = self.get_client_ip(request)

        response = self.get_response(request)

        # Clear thread local storage after response is processed
        _local.user = None
        _local.ip_address = None
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def get_current_user():
    return getattr(_local, 'user', None)

def get_current_ip():
    return getattr(_local, 'ip_address', None)
