from django.db import models
from users.models import User

class AuditLog(models.Model):
    """
    Maintains a comprehensive log of all user actions performed within the system
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=100)  # e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN'
    module = models.CharField(max_length=50)   # e.g., 'leave_out', 'maintenance', 'user'
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.action} - {self.timestamp}"