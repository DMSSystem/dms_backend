# audit_log/views.py
from rest_framework import viewsets
from .models import AuditLog
from .serializers import AuditLogSerializer
from users.permissions import IsAdmin

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Audit Logs.
    - ReadOnly access only.
    - Restricted to Administrators.
    - Supports filtering by user, action, module, start_date, and end_date.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = AuditLog.objects.all().order_by('-timestamp')
        
        user_id = self.request.query_params.get('user_id')
        action_param = self.request.query_params.get('action')
        module = self.request.query_params.get('module')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action_param:
            queryset = queryset.filter(action__iexact=action_param)
        if module:
            queryset = queryset.filter(module__iexact=module)
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
            
        return queryset
