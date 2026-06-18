# rooms/serializers.py
from rest_framework import serializers
from .models import Room, Dorm

class DormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dorm
        fields = ['id', 'name', 'number_of_rooms', 'room_capacity']
        read_only_fields = ['id']

    def validate_number_of_rooms(self, value):
        if value <= 0:
            raise serializers.ValidationError("A dorm must have at least 1 room.")
        return value

    def validate_room_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Room capacity must be a positive integer.")
        return value

    def create(self, validated_data):
        dorm = super().create(validated_data)
        rooms = [
            Room(dorm=dorm, room_number=str(i), capacity=dorm.room_capacity)
            for i in range(1, dorm.number_of_rooms + 1)
        ]
        Room.objects.bulk_create(rooms)
        return dorm

    def update(self, instance, validated_data):
        old_num_rooms = instance.number_of_rooms
        dorm = super().update(instance, validated_data)
        new_num_rooms = dorm.number_of_rooms
        new_capacity = dorm.room_capacity

        if new_num_rooms > old_num_rooms:
            rooms_to_create = [
                Room(dorm=dorm, room_number=str(i), capacity=new_capacity)
                for i in range(old_num_rooms + 1, new_num_rooms + 1)
            ]
            Room.objects.bulk_create(rooms_to_create)
            
        return dorm


class RoomSerializer(serializers.ModelSerializer):
    dorm_name = serializers.CharField(source='dorm.name', read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'dorm', 'dorm_name', 'room_number', 'capacity', 'current_occupancy']
        read_only_fields = ['id', 'dorm_name']

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

