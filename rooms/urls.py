# rooms/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dorms', views.DormViewSet, basename='dorm')
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'academic-terms', views.AcademicTermViewSet, basename='academic-term')

urlpatterns = [
    path('', include(router.urls)),
]