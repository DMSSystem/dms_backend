# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet, 
    ParentSignUpView, 
    StaffSignUpView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    
    # Public signup endpoints (no authentication)
    path('signup/parent/', ParentSignUpView.as_view(), name='parent-signup'),
    path('signup/staff/', StaffSignUpView.as_view(), name='staff-signup'),
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User management endpoints (auto-generated + custom actions)
    path('', include(router.urls)),
]

# Auto-generated routes from router:
# GET    /users/                          list
# POST   /users/                          create
# GET    /users/{id}/                     retrieve
# PUT    /users/{id}/                     update
# PATCH  /users/{id}/                     partial_update
# DELETE /users/{id}/                     destroy (soft delete)
# GET    /users/me/                       me
# POST   /users/change_password/          change_password
# POST   /users/{id}/reset_password/      reset_password
# POST   /users/{id}/deactivate/          deactivate
# POST   /users/{id}/activate/            activate
# GET    /users/by_role/?role=officer     by_role