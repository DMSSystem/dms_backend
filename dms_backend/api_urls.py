# dms_backend/api_urls.py
from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),
    path('', include('rooms.urls')),
    path('', include('students.urls')),
    path('', include('leave_out.urls')),
    path('', include('maintenance.urls')),
    path('', include('duty_roster.urls')),
    path('', include('inspection.urls')),
    path('', include('audit_log.urls')),
]
