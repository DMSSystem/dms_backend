# leave_out/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'leave-out', views.LeaveOutViewSet, basename='leaveout')

urlpatterns = [
    path('', include(router.urls)),
]