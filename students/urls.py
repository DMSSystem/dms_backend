# students/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'emergency-contacts', views.EmergencyContactViewSet, basename='emergency-contact')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional custom routes
    path('students/by-admission/<str:admission_no>/', 
         views.StudentByAdmissionView.as_view(), 
         name='student-by-admission'),
    
    path('students/by-room/<int:room_id>/', 
         views.StudentsByRoomView.as_view(), 
         name='students-by-room'),
]