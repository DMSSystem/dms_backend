# maintenance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'maintenance', views.MaintenanceRequestViewSet, basename='maintenancerequest')

urlpatterns = [
    path('', include(router.urls)),
]