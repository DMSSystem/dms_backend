# duty_roster/serializers.py
from rest_framework import serializers
from .models import DutyRoster, DutyAssignment
from students.serializers import StudentSerializer

class DutyAssignmentSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', read_only=True)
    student_name = serializers.ReadOnlyField(source='student.full_name')
    student_admission_no = serializers.ReadOnlyField(source='student.admission_no')

    class Meta:
        model = DutyAssignment
        fields = [
            'id', 'duty_roster', 'student', 'student_details',
            'student_name', 'student_admission_no', 'status',
            'completed_at', 'remarks'
        ]
        read_only_fields = ['id', 'completed_at']


class DutyRosterSerializer(serializers.ModelSerializer):
    assignments = DutyAssignmentSerializer(many=True, read_only=True)
    student_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False,
        help_text="List of student IDs to assign to this duty roster."
    )
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = DutyRoster
        fields = [
            'id', 'duty_date', 'dorm_name', 'task', 'shift',
            'supervisor', 'assignments', 'student_ids',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        student_ids = validated_data.pop('student_ids', [])
        duty_roster = DutyRoster.objects.create(**validated_data)
        
        # Create assignments
        for student_id in student_ids:
            DutyAssignment.objects.create(duty_roster=duty_roster, student_id=student_id)
            
        return duty_roster

    def update(self, instance, validated_data):
        student_ids = validated_data.pop('student_ids', None)
        
        # Update roster fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if student_ids is not None:
            # Sync assignments
            existing_student_ids = set(instance.assignments.values_list('student_id', flat=True))
            new_student_ids = set(student_ids)
            
            # Delete assignments not in the new list
            instance.assignments.filter(student_id__in=existing_student_ids - new_student_ids).delete()
            
            # Create new assignments
            for student_id in new_student_ids - existing_student_ids:
                DutyAssignment.objects.create(duty_roster=instance, student_id=student_id)
                
        return instance
