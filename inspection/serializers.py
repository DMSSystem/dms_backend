# inspection/serializers.py
from rest_framework import serializers
from .models import Inspection
from rooms.serializers import RoomSerializer

class InspectionSerializer(serializers.ModelSerializer):
    room_details = RoomSerializer(source='room', read_only=True)
    inspected_by_username = serializers.ReadOnlyField(source='inspected_by.username')

    class Meta:
        model = Inspection
        fields = [
            'id', 'room', 'room_details', 'inspected_by',
            'inspected_by_username', 'inspection_date', 'status',
            'remarks', 'created_at'
        ]
        read_only_fields = ['id', 'inspected_by', 'created_at']
