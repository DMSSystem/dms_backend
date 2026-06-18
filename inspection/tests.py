# inspection/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from users.models import User
from rooms.models import Room, Dorm
from .models import Inspection

class InspectionAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_in', email='admin_in@dms.com',
            password='Admin_in@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_in', email='officer_in@dms.com',
            password='Officer_in@1234', role='officer'
        )
        self.parent = User.objects.create_user(
            username='parent_in', email='parent_in@dms.com',
            password='Parent_in@1234', role='parent'
        )
        
        # Create rooms
        self.dorm = Dorm.objects.create(name='Elbrus', number_of_rooms=2, room_capacity=4)
        self.room1 = Room.objects.create(dorm=self.dorm, room_number='101', capacity=4)
        self.room2 = Room.objects.create(dorm=self.dorm, room_number='102', capacity=4)

        
        # Create an inspection for room1 today
        self.inspection = Inspection.objects.create(
            room=self.room1,
            inspected_by=self.officer,
            inspection_date=timezone.now(),
            status='pass',
            remarks='Clean room'
        )
        
        self.list_url = reverse('inspection-list')
        self.uninspected_url = reverse('inspection-uninspected')

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_officer_can_submit_inspection(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'room': self.room2.id,
            'inspection_date': timezone.now(),
            'status': 'fail',
            'remarks': 'Messy beds'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['inspected_by_username'], 'officer_in')

    def test_parent_cannot_view_or_submit_inspection(self):
        self._auth(self.parent)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_uninspected_rooms_list(self):
        self._auth(self.officer)
        res = self.client.get(self.uninspected_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Only room2 should be returned because room1 was inspected today (within 7 days)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['room_number'], '102')
