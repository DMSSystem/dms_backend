from django.db import models
from users.models import User
from rooms.models import Dorm


class MaintenanceRequest(models.Model):
    """
    Tracks maintenance issues submitted by boarding officers with resolution status.
    - Officers submit requests specifying location, dorm block, urgency & description.
    - Admins approve (→ in_progress), resolve, or reject with optional remarks.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    )

    URGENCY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    )

    description = models.TextField()
    location = models.CharField(max_length=200)          # e.g. 'Room 101'
    dorm_block = models.ForeignKey(
        Dorm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_requests',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True
    )
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')

    # Reporter / assignment
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_requests',
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_maintenance',
    )

    # Dates
    reported_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    # Notes
    remarks = models.TextField(blank=True)          # officer additional notes
    admin_remarks = models.TextField(blank=True)    # admin approval / rejection notes

    class Meta:
        db_table = 'maintenance_request'
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
        ordering = ['-reported_date']

    def __str__(self):
        return f"{self.get_urgency_display()} - {self.location} ({self.status})"
