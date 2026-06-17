# duty_roster/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DutyRosterViewSet, DutyAssignmentViewSet

router = DefaultRouter()
router.register(r'duty-rosters', DutyRosterViewSet, basename='duty-roster')
router.register(r'duty-assignments', DutyAssignmentViewSet, basename='duty-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
