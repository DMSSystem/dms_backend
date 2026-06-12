# duty_roster/models.py
from django.db import models
from students.models import Student
from django.utils import timezone

class DutyRoster(models.Model):
    """
    Daily cleaning duty roster for student groups in dormitories
    Morning shifts: Monday-Friday
    Day shifts: Saturday
    No duties: Sunday
    """
    
    TASK_CHOICES = (
        ('dorm_cleaning', 'Dormitory Cleaning'),
        ('bathroom', 'Bathroom Cleaning'),
        ('corridor', 'Corridor Sweeping'),
        ('common_room', 'Common Room Cleaning'),
    )
    
    SHIFT_CHOICES = (
        ('morning', 'Morning (4:30 AM - 5:00 AM)'),  # Monday-Friday
        ('day', 'Daytime (10:00 AM - 2:00 PM)'),      # Saturday only
    )
    
    # Basic information
    duty_date = models.DateField(db_index=True)
    dorm_name = models.CharField(max_length=100)  # e.g., 'Kilimanjaro', 'Kenya House'
    task = models.CharField(max_length=50, choices=TASK_CHOICES)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    
    # Assigned students (group of 4-6 students per task)
    assigned_students = models.ManyToManyField(Student, related_name='duties', through='DutyAssignment')
    
    # Supervisor (prefect or senior student)
    supervisor = models.CharField(max_length=100, blank=True, help_text="Prefect or senior student in charge")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_duties')
    
    class Meta:
        db_table = 'duty_roster'
        verbose_name = 'Duty Roster'
        verbose_name_plural = 'Duty Rosters'
        ordering = ['duty_date', 'dorm_name', 'task']
        unique_together = ['dorm_name', 'duty_date', 'task']  # One task per dorm per day
    
    def __str__(self):
        shift_display = 'Morning' if self.shift == 'morning' else 'Daytime'
        return f"{self.dorm_name} - {self.get_task_display()} ({self.duty_date}, {shift_display})"
    
    def get_student_count(self):
        return self.assigned_students.count()
    
    @classmethod
    def get_shift_for_date(cls, date):
        """Determine shift based on day of week"""
        # Monday = 0, Tuesday = 1, ..., Saturday = 5, Sunday = 6
        if date.weekday() == 5:  # Saturday
            return 'day'
        elif date.weekday() == 6:  # Sunday
            return None  # No duty on Sunday
        else:  # Monday to Friday
            return 'morning'


class DutyAssignment(models.Model):
    """
    Tracks individual student assignments and their completion status
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    )
    
    duty_roster = models.ForeignKey(DutyRoster, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='duty_assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'duty_assignment'
        unique_together = ['duty_roster', 'student']
        ordering = ['duty_roster__duty_date', 'student__full_name']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.duty_roster} - {self.get_status_display()}"
    
    def mark_completed(self):
        """Mark duty as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()