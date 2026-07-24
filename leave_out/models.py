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
        ('escalated', 'Escalated'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leave_outs')
    leave_date = models.DateField(db_index=True)
    return_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_leaves')
    returned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confirmed_returns',
        help_text="The Admin or Officer who confirmed the student had returned."
    )
    returned_at = models.DateTimeField(null=True, blank=True)
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
        """Flag overdue returns where student has not returned by the stated date.
        Approved or escalated leaves that are past their return date are overdue.
        Rejected, pending, and completed leaves are never overdue."""
        return (
            self.status in ['approved', 'escalated'] and
            self.return_date < timezone.now().date()
        )

    @property
    def days_overdue(self):
        """Number of days past expected return date (0 if not overdue)."""
        if not self.is_overdue():
            return 0
        diff = (timezone.now().date() - self.return_date).days
        return max(0, diff)

    @property
    def overdue_severity(self):
        """Returns overdue severity tier: 'none', 'minor', 'moderate', or 'critical'."""
        if not self.is_overdue():
            return 'none'
        days = self.days_overdue
        if days <= 1:
            return 'minor'
        elif days <= 3:
            return 'moderate'
        return 'critical'


class ContactAttempt(models.Model):
    """
    Audit trail recording contact attempts made by staff regarding student leaves.
    """
    CONTACT_TYPE_CHOICES = (
        ('call', 'Phone Call'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Other'),
    )
    OUTCOME_CHOICES = (
        ('no_answer', 'No Answer'),
        ('spoke_with_parent', 'Spoke with Parent/Guardian'),
        ('left_voicemail', 'Left Voicemail'),
        ('unreachable', 'Unreachable / Line Busy'),
        ('wrong_number', 'Wrong Number'),
        ('resolved', 'Issue Resolved'),
    )

    leave_out = models.ForeignKey(LeaveOut, on_delete=models.CASCADE, related_name='contact_attempts')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contact_attempts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, default='call')
    contact_person = models.CharField(max_length=100, help_text="Person or phone number contacted")
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES, default='no_answer')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leave_contact_attempt'
        verbose_name = 'Contact Attempt'
        verbose_name_plural = 'Contact Attempts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contact_type} to {self.contact_person} ({self.outcome}) at {self.created_at}"