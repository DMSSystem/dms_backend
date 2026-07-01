# audit_log/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from users.models import User
from rooms.models import Room, Dorm
from .models import AuditLog

class AuditLogAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_al', email='admin_al@dms.com',
            password='Admin_al@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_al', email='officer_al@dms.com',
            password='Officer_al@1234', role='officer'
        )
        
        self.list_url = reverse('audit-log-list')

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_admin_can_view_audit_logs(self):
        self._auth(self.admin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_officer_cannot_view_audit_logs(self):
        self._auth(self.officer)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_signal_logging_on_room_creation(self):
        # We need to authenticate as admin, make a room creation call, and verify it logs it with user and IP
        self._auth(self.admin)
        
        # Create a Dorm first since it's required for Room creation
        dorm = Dorm.objects.create(name='Kilimanjaro', number_of_rooms=1, room_capacity=4)
        
        # Clear existing logs created during user setups if any
        AuditLog.objects.all().delete()
        
        # Create a room via API to execute middleware and capture user
        self.client.post(reverse('room-list'), {
            'dorm': dorm.id,
            'room_number': '999',
            'capacity': 4
        })
        
        # Check if audit log was created
        logs = AuditLog.objects.filter(module='room', action='CREATE')
        self.assertEqual(logs.count(), 1)
        self.assertIn("Room 'Kilimanjaro - Room 999' was created", logs.first().description)
        self.assertEqual(logs.first().user, self.admin)

    def test_user_self_deletion_audit_log_handling(self):
        from audit_log.middleware import _local
        
        # Set the thread local current user to the admin user
        _local.user = self.admin
        
        try:
            # Delete the admin user (should not raise IntegrityError/ForeignKeyViolation)
            self.admin.delete()
        finally:
            # Clean up thread local
            _local.user = None
            
        # Verify that the admin user was deleted
        self.assertFalse(User.objects.filter(username='admin_al').exists())
        
        # Verify the audit log entries
        # Since the user was deleted, the audit log entries referencing this user should have user=None
        logs = AuditLog.objects.filter(description__icontains="deleted")
        self.assertTrue(logs.exists())
        for log in logs:
            self.assertIsNone(log.user)

