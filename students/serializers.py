# students/serializers.py
import re
from rest_framework import serializers
from .models import Student, EmergencyContact
from rooms.serializers import RoomSerializer
from users.models import User
from users.serializers import UserSerializer

class EmergencyContactSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EmergencyContact
        fields = ['id', 'student', 'name', 'relationship', 'phone', 'is_primary', 'priority', 'is_active']
        read_only_fields = ['is_active']
        extra_kwargs = {
            'student': {'required': False, 'allow_null': True}
        }

    def validate_phone(self, value):
        """Phone must contain only digits, spaces, +, -, parentheses."""
        if not value:
            return value
        cleaned_val = str(value).replace('\r', '').replace('\n', '').strip()
        cleaned = re.sub(r'[\s\-\(\)\+]', '', cleaned_val)
        if not cleaned.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits (spaces, +, - and parentheses are allowed)."
            )
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise serializers.ValidationError(
                "Phone number must be between 7 and 15 digits."
            )
        return cleaned_val


class StudentSerializer(serializers.ModelSerializer):
    emergency_contacts = EmergencyContactSerializer(many=True, required=False)
    active_emergency_contacts = serializers.SerializerMethodField()
    room_details = RoomSerializer(source='room', read_only=True)
    parents = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='parent'),
        many=True,
        required=False
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='parent'),
        write_only=True,
        required=False,
        allow_null=True
    )
    parent_details = serializers.SerializerMethodField()
    parent_username = serializers.SerializerMethodField()
    parent_email = serializers.SerializerMethodField()
    parent_phone = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'admission_no', 'room', 'room_details',
            'parents', 'parent', 'parent_details', 'parent_username', 'parent_email', 'parent_phone',
            'grade', 'stream', 'status', 'emergency_contacts', 'active_emergency_contacts'
        ]
        read_only_fields = ['id']

    def get_active_emergency_contacts(self, instance):
        contacts = [c for c in instance.emergency_contacts.all() if c.is_active]
        return EmergencyContactSerializer(contacts, many=True).data

    def get_parent_details(self, instance):
        parents = instance.parents.all()
        return UserSerializer(parents, many=True).data

    def get_parent_username(self, instance):
        p = instance.parent
        return p.username if p else None

    def get_parent_email(self, instance):
        p = instance.parent
        return p.email if p else None

    def get_parent_phone(self, instance):
        p = instance.parent
        return p.phone if p else None

    def validate_full_name(self, value):
        """Full name must only contain letters, spaces, hyphens, and apostrophes."""
        if not value or not value.strip():
            raise serializers.ValidationError("Full name is required.")
        if not re.match(r"^[A-Za-z\s\-\']+$", value.strip()):
            raise serializers.ValidationError(
                "Full name must contain only letters, spaces, hyphens, and apostrophes."
            )
        return value.strip()

    def validate_admission_no(self, value):
        """Admission number must contain letters, digits, hyphens, or slashes only."""
        if not value or not value.strip():
            raise serializers.ValidationError("Admission number is required.")
        if not re.match(r'^[A-Za-z0-9\-\/]+$', value.strip()):
            raise serializers.ValidationError(
                "Admission number must contain only letters, digits, hyphens, or slashes."
            )
        return value.strip()

    def validate_emergency_contacts(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one emergency contact is required.")
        
        # Check for duplicate phone numbers within the payload
        seen_phones = set()
        for contact in value:
            raw_phone = contact.get('phone', '')
            cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', raw_phone)
            if cleaned_phone in seen_phones:
                raise serializers.ValidationError(
                    f"Duplicate emergency contact phone number detected: {raw_phone}"
                )
            seen_phones.add(cleaned_phone)

        return value

    def create(self, validated_data):
        contacts_data = validated_data.pop('emergency_contacts', [])
        parents_data = validated_data.pop('parents', None)
        single_parent = validated_data.pop('parent', None)

        student = Student.objects.create(**validated_data)
        
        # Handle parent linkage
        if parents_data:
            student.parents.set(parents_data)
        elif single_parent:
            student.parents.set([single_parent])

        # Handle room occupancy
        if student.room:
            room = student.room
            if room.current_occupancy >= room.capacity:
                raise serializers.ValidationError({"room": "This room is already at full capacity."})
            room.current_occupancy += 1
            room.save()

        # Create emergency contacts
        for idx, contact_data in enumerate(contacts_data):
            if 'priority' not in contact_data:
                contact_data['priority'] = idx + 1
            EmergencyContact.objects.create(student=student, is_active=True, **contact_data)
            
        return student

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('emergency_contacts', None)
        parents_data = validated_data.pop('parents', None)
        single_parent = validated_data.pop('parent', None)
        old_room = instance.room
        new_room = validated_data.get('room', old_room)

        # Update student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle parent linkage update
        if parents_data is not None:
            instance.parents.set(parents_data)
        elif single_parent is not None:
            instance.parents.set([single_parent] if single_parent else [])

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
            
            # Soft-deactivate existing active contacts to retain audit history
            existing_active = list(instance.emergency_contacts.filter(is_active=True))
            
            updated_ids = set()
            for idx, contact_data in enumerate(contacts_data):
                cid = contact_data.get('id', None)
                if 'priority' not in contact_data:
                    contact_data['priority'] = idx + 1
                    
                if cid:
                    contact_obj = instance.emergency_contacts.filter(id=cid).first()
                    if contact_obj:
                        for k, v in contact_data.items():
                            setattr(contact_obj, k, v)
                        contact_obj.is_active = True
                        contact_obj.save()
                        updated_ids.add(contact_obj.id)
                        continue
                
                # Match by name and relationship if ID wasn't provided
                matched = instance.emergency_contacts.filter(
                    name=contact_data.get('name'),
                    relationship=contact_data.get('relationship'),
                    is_active=True
                ).first()
                if matched:
                    for k, v in contact_data.items():
                        setattr(matched, k, v)
                    matched.save()
                    updated_ids.add(matched.id)
                else:
                    new_contact = EmergencyContact.objects.create(student=instance, is_active=True, **contact_data)
                    updated_ids.add(new_contact.id)

            # Deactivate contacts that were replaced/removed
            for old_c in existing_active:
                if old_c.id not in updated_ids:
                    old_c.is_active = False
                    old_c.save()

        return instance