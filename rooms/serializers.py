# rooms/serializers.py
from rest_framework import serializers
from .models import Room

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'dorm_name', 'room_number', 'capacity', 'current_occupancy']
        read_only_fields = ['id']

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer.")
        return value

    def validate(self, attrs):
        capacity = attrs.get('capacity', self.instance.capacity if self.instance else 4)
        current_occupancy = attrs.get('current_occupancy', self.instance.current_occupancy if self.instance else 0)
        
        if current_occupancy > capacity:
            raise serializers.ValidationError({"current_occupancy": "Current occupancy cannot exceed room capacity."})
        return attrs
