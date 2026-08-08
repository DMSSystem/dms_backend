# leave_out/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import LeaveOut, ContactAttempt
from students.serializers import StudentSerializer

class ContactAttemptSerializer(serializers.ModelSerializer):
    performed_by_username = serializers.ReadOnlyField(source='performed_by.username')
    outcome_display = serializers.ReadOnlyField(source='get_outcome_display')
    contact_type_display = serializers.ReadOnlyField(source='get_contact_type_display')

    class Meta:
        model = ContactAttempt
        fields = [
            'id', 'leave_out', 'performed_by', 'performed_by_username',
            'contact_type', 'contact_type_display', 'contact_person',
            'outcome', 'outcome_display', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'leave_out', 'performed_by', 'created_at']

    def validate_contact_person(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Contact person or phone number is required.")
        return value.strip()


class LeaveOutSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', read_only=True)
    approved_by_username = serializers.ReadOnlyField(source='approved_by.username')
    returned_by_username = serializers.ReadOnlyField(source='returned_by.username')
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.ReadOnlyField()
    overdue_severity = serializers.ReadOnlyField()
    contact_attempts = ContactAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveOut
        fields = [
            'id', 'student', 'student_details', 'leave_date', 'return_date',
            'reason', 'status', 'approved_by', 'approved_by_username',
            'returned_by', 'returned_by_username', 'returned_at',
            'is_overdue', 'days_overdue', 'overdue_severity', 'contact_attempts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'approved_by', 'returned_by', 'returned_at', 'created_at', 'updated_at']

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("A reason is required for the leave request.")
        return value.strip()

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def validate(self, attrs):
        leave_date = attrs.get('leave_date')
        return_date = attrs.get('return_date')
        student = attrs.get('student')
        
        # In updates, if one is missing, check from instance
        if not leave_date and self.instance:
            leave_date = self.instance.leave_date
        if not return_date and self.instance:
            return_date = self.instance.return_date
        if not student and self.instance:
            student = self.instance.student

        today = timezone.now().date()

        # Validate leave_date is today or in the future when creating a new leave or changing leave_date
        if leave_date and (not self.instance or 'leave_date' in attrs):
            if leave_date < today:
                raise serializers.ValidationError({"leave_date": "Leave date must be today or a future date."})

        if leave_date and return_date:
            if return_date < leave_date:
                raise serializers.ValidationError({"return_date": "Return date cannot be before leave date."})

        # Validate that student does not already have an active/pending leave request
        if student and (not self.instance or 'student' in attrs):
            existing_query = LeaveOut.objects.filter(
                student=student,
                status__in=['pending', 'approved']
            )
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise serializers.ValidationError({
                    "student": "This student already has an active or pending leave request. They cannot hold multiple active leaves simultaneously."
                })

        return attrs