# dms_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/', include('users.urls')),           # /api/users/, /api/token/
    # path('api/', include('rooms.urls')),           # /api/rooms/  ← ADDED
    # path('api/', include('students.urls')),        # /api/students/, /api/emergency-contacts/ ← ADDED
    # path('api/', include('leave_out.urls')),       # /api/leave-out/
    # path('api/', include('maintenance.urls')),     # /api/maintenance/
    # path('api/', include('duty_roster.urls')),     # /api/duty-roster/
    # path('api/', include('inspection.urls')),      # /api/inspections/
    # path('api/', include('audit_log.urls')),       # /api/audit-logs/
]