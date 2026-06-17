# audit_log/serializers.py
from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_username', 'action', 'module',
            'description', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
