# leave_out/serializers.py
from rest_framework import serializers
from .models import LeaveOut
from students.serializers import StudentSerializer

class LeaveOutSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', read_only=True)
    approved_by_username = serializers.ReadOnlyField(source='approved_by.username')
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = LeaveOut
        fields = [
            'id', 'student', 'student_details', 'leave_date', 'return_date',
            'reason', 'status', 'approved_by', 'approved_by_username',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'approved_by', 'created_at', 'updated_at']

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def validate(self, attrs):
        leave_date = attrs.get('leave_date')
        return_date = attrs.get('return_date')
        
        # In updates, if one is missing, check from instance
        if not leave_date and self.instance:
            leave_date = self.instance.leave_date
        if not return_date and self.instance:
            return_date = self.instance.return_date

        if leave_date and return_date:
            if return_date < leave_date:
                raise serializers.ValidationError({"return_date": "Return date cannot be before leave date."})
        return attrs
