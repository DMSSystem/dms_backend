from django.db import models
from rooms.models import Room
from users.models import User

class Student(models.Model):
    """
    Stores student records including room assignment and emergency contact reference
    """
    full_name = models.CharField(max_length=100)
    admission_no = models.CharField(max_length=50, unique=True, db_index=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='students')
    
    class Meta:
        db_table = 'student'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.admission_no} - {self.full_name}"

class EmergencyContact(models.Model):
    """
    Stores emergency contact details linked to each student
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)  # e.g., 'Father', 'Mother', 'Guardian'
    phone = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'emergency_contact'
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.student.full_name}"
