# maintenance/serializers.py
from rest_framework import serializers
from .models import MaintenanceRequest


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    # Read-only computed fields
    reported_by_name = serializers.SerializerMethodField()
    reported_by_username = serializers.ReadOnlyField(source='reported_by.username')
    assigned_to_name = serializers.SerializerMethodField()
    dorm_block_name = serializers.ReadOnlyField(source='dorm_block.name')

    def get_reported_by_name(self, obj):
        if obj.reported_by:
            return (
                f"{obj.reported_by.first_name} {obj.reported_by.last_name}".strip()
                or obj.reported_by.username
            )
        return None

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return (
                f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
                or obj.assigned_to.username
            )
        return None

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id',
            'description',
            'location',
            'dorm_block',
            'dorm_block_name',
            'status',
            'urgency',
            'reported_by',
            'reported_by_name',
            'reported_by_username',
            'assigned_to',
            'assigned_to_name',
            'reported_date',
            'resolved_date',
            'remarks',
            'admin_remarks',
        ]
        read_only_fields = [
            'id',
            'reported_by',
            'reported_by_name',
            'reported_by_username',
            'assigned_to_name',
            'dorm_block_name',
            'reported_date',
            'resolved_date',
        ]
