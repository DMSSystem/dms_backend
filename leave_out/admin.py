from django.contrib import admin
from .models import LeaveOut

@admin.register(LeaveOut)
class LeaveOutAdmin(admin.ModelAdmin):
    list_display = ('student', 'leave_date', 'return_date', 'status', 'approved_by')
    list_filter = ('status', 'leave_date', 'return_date')
    search_fields = ('student__full_name', 'student__admission_no', 'reason')
