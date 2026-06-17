# maintenance/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from users.models import User
from .models import MaintenanceRequest

class MaintenanceAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_mt', email='admin_mt@dms.com',
            password='Admin@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_mt', email='officer_mt@dms.com',
            password='Officer@1234', role='officer'
        )
        self.parent = User.objects.create_user(
            username='parent_mt', email='parent_mt@dms.com',
            password='Parent@1234', role='parent'
        )
        
        # Create request
        self.req = MaintenanceRequest.objects.create(
            description='Leaking faucet',
            location='Room 101, Block A',
            urgency='medium',
            status='pending',
            reported_by=self.officer
        )
        
        self.list_url = reverse('maintenancerequest-list')
        self.detail_url = reverse('maintenancerequest-detail', args=[self.req.id])

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_officer_can_submit_request(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'description': 'Broken window pane',
            'location': 'Common room, Block B',
            'urgency': 'high'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['reported_by_username'], 'officer_mt')
        self.assertEqual(res.data['status'], 'pending')

    def test_parent_cannot_view_or_submit_request(self):
        self._auth(self.parent)
        res_get = self.client.get(self.list_url)
        # Parents get 403 Forbidden because permission is IsAdminOrOfficer
        self.assertEqual(res_get.status_code, status.HTTP_403_FORBIDDEN)
        
        res_post = self.client.post(self.list_url, {
            'description': 'Hack',
            'location': 'Secret',
            'urgency': 'low'
        })
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_resolution_sets_date(self):
        self._auth(self.admin)
        self.assertIsNone(self.req.resolved_date)
        res = self.client.patch(self.detail_url, {'status': 'resolved'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'resolved')
        self.assertIsNotNone(self.req.resolved_date)
