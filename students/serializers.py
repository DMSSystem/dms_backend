# students/serializers.py
from rest_framework import serializers
from .models import Student, EmergencyContact
from rooms.serializers import RoomSerializer

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'student', 'name', 'relationship', 'phone']
        read_only_fields = ['id']
        extra_kwargs = {
            'student': {'required': False, 'allow_null': True}
        }


class StudentSerializer(serializers.ModelSerializer):
    emergency_contacts = EmergencyContactSerializer(many=True, required=True)
    room_details = RoomSerializer(source='room', read_only=True)
    parent_username = serializers.ReadOnlyField(source='parent.username')

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'admission_no', 'room', 'room_details',
            'parent', 'parent_username', 'grade', 'stream', 'emergency_contacts'
        ]
        read_only_fields = ['id']

    def validate_emergency_contacts(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one emergency contact is required.")
        return value

    def create(self, validated_data):
        contacts_data = validated_data.pop('emergency_contacts')
        student = Student.objects.create(**validated_data)
        
        # Handle room occupancy
        if student.room:
            room = student.room
            if room.current_occupancy >= room.capacity:
                raise serializers.ValidationError({"room": "This room is already at full capacity."})
            room.current_occupancy += 1
            room.save()

        # Create emergency contacts
        for contact_data in contacts_data:
            EmergencyContact.objects.create(student=student, **contact_data)
            
        return student

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('emergency_contacts', None)
        old_room = instance.room
        new_room = validated_data.get('room', old_room)

        # Update student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle room capacity change
        if old_room != new_room:
            if old_room:
                old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
                old_room.save()
            if new_room:
                if new_room.current_occupancy >= new_room.capacity:
                    raise serializers.ValidationError({"room": "The new room is already at full capacity."})
                new_room.current_occupancy += 1
                new_room.save()

        if contacts_data is not None:
            if not contacts_data or len(contacts_data) == 0:
                raise serializers.ValidationError({"emergency_contacts": "At least one emergency contact is required."})
            # Replace existing contacts
            instance.emergency_contacts.all().delete()
            for contact_data in contacts_data:
                EmergencyContact.objects.create(student=instance, **contact_data)
                
        return instance
