from django.contrib import admin
from .models import MaintenanceRequest


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'location', 'dorm_block', 'urgency', 'status', 'reported_by', 'reported_date']
    list_filter = ['status', 'urgency', 'dorm_block']
    search_fields = ['location', 'description', 'reported_by__username']
    readonly_fields = ['reported_date', 'resolved_date']
    ordering = ['-reported_date']
