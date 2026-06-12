from django.db import models
from rooms.models import Room
from users.models import User

class Inspection(models.Model):
    """
    Records dormitory room inspection outcomes including status and inspector remarks
    """
    STATUS_CHOICES = (
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pending', 'Pending'),
    )
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='inspections')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections')
    inspection_date = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inspection'
        verbose_name = 'Inspection'
        verbose_name_plural = 'Inspections'
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"Room {self.room.room_number} - {self.inspection_date.date()} ({self.get_status_display()})"