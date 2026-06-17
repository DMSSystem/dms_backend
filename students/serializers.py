# students/serializers.py
from rest_framework import serializers
from .models import Student, EmergencyContact
from rooms.serializers import RoomSerializer

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'student', 'name', 'relationship', 'phone']
        read_only_fields = ['id']


class StudentSerializer(serializers.ModelSerializer):
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    room_details = RoomSerializer(source='room', read_only=True)
    parent_username = serializers.ReadOnlyField(source='parent.username')

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'admission_no', 'room', 'room_details',
            'parent', 'parent_username', 'emergency_contacts'
        ]
        read_only_fields = ['id']
