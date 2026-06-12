from django.db import models
from students.models import Student
from users.models import User
from django.utils import timezone

class LeaveOut(models.Model):
    """
    Records all student leave-out requests with approval status and approver reference
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leave_outs')
    leave_date = models.DateField(db_index=True)
    return_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_out'
        verbose_name = 'Leave Out'
        verbose_name_plural = 'Leave Outs'
        ordering = ['-leave_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.leave_date} to {self.return_date} ({self.status})"
    
    def is_overdue(self):
        """Flag overdue returns where student has not returned by the stated date"""
        return self.return_date < timezone.now().date() and self.status != 'completed'