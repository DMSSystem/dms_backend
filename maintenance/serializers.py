# maintenance/serializers.py
from rest_framework import serializers
from .models import MaintenanceRequest

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.ReadOnlyField(source='reported_by.username')

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'description', 'location', 'status', 'urgency',
            'reported_by', 'reported_by_username', 'reported_date',
            'resolved_date', 'remarks'
        ]
        read_only_fields = ['id', 'reported_by', 'reported_date', 'resolved_date']
