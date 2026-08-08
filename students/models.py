from django.db import models
from django.utils import timezone
from rooms.models import Room
from users.models import User

class Student(models.Model):
    """
    Stores student records including room assignment and emergency contact references.
    Supports multiple parent accounts (e.g. Mother and Father) per student.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('eloped', 'Eloped / Missing'),
    )

    full_name = models.CharField(max_length=100)
    admission_no = models.CharField(max_length=50, unique=True, db_index=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='students')
    parents = models.ManyToManyField(
        User, 
        blank=True,
        related_name='children_students',
        help_text="Parent or guardian user accounts linked to this student."
    )
    grade = models.CharField(max_length=50, blank=True, null=True)
    stream = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    class Meta:
        db_table = 'student'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.admission_no} - {self.full_name}"

    @property
    def parent(self):
        """Backward-compatible helper returning primary parent account or None."""
        return self.parents.first()


class EmergencyContact(models.Model):
    """
    Stores emergency contact details linked to each student with priority ranking and audit history support.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)  # e.g., 'Father', 'Mother', 'Guardian'
    phone = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=1, help_text="Priority order (1=highest)")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Soft-delete flag to retain history")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emergency_contact'
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'
        ordering = ['-is_primary', 'priority', 'id']
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.student.full_name}"
