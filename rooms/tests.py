# rooms/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from .models import Room, Dorm

class RoomAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_rm', email='admin_rm@dms.com',
            password='Admin_rm@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_rm', email='officer_rm@dms.com',
            password='Officer_rm@1234', role='officer'
        )
        self.parent = User.objects.create_user(
            username='parent_rm', email='parent_rm@dms.com',
            password='Parent_rm@1234', role='parent'
        )
        
        # Create a dorm and room
        self.dorm = Dorm.objects.create(
            name='Kilimanjaro',
            number_of_rooms=1,
            room_capacity=4
        )
        self.room = Room.objects.create(
            dorm=self.dorm,
            room_number='101',
            capacity=4,
            current_occupancy=0
        )
        
        # Create another dorm for API creation tests
        self.dorm2 = Dorm.objects.create(
            name='Mount Kenya',
            number_of_rooms=5,
            room_capacity=6
        )
        
        # URLs
        self.list_url = reverse('room-list')
        self.detail_url = reverse('room-detail', args=[self.room.id])

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_admin_can_create_room(self):
        self._auth(self.admin)
        res = self.client.post(self.list_url, {
            'dorm': self.dorm2.id,
            'room_number': '202',
            'capacity': 6,
            'current_occupancy': 0
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Room.objects.filter(dorm=self.dorm2, room_number='202').exists())

    def test_officer_can_create_room(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'dorm': self.dorm2.id,
            'room_number': '303',
            'capacity': 6
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_parent_cannot_create_room(self):
        self._auth(self.parent)
        res = self.client.post(self.list_url, {
            'dorm': self.dorm2.id,
            'room_number': '404',
            'capacity': 6
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_room(self):
        self._auth(self.admin)
        res = self.client.patch(self.detail_url, {'capacity': 8})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 8)

    def test_invalid_capacity_rejected(self):
        self._auth(self.admin)
        res = self.client.patch(self.detail_url, {'capacity': 0})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_occupancy_exceeding_capacity_rejected(self):
        self._auth(self.admin)
        res = self.client.patch(self.detail_url, {'current_occupancy': 5})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_create_dorm_with_auto_rooms(self):
        self._auth(self.admin)
        url = reverse('dorm-list')
        res = self.client.post(url, {
            'name': 'Ruwenzori',
            'number_of_rooms': 5,
            'room_capacity': 4
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Check that Dorm was created
        dorm = Dorm.objects.get(name='Ruwenzori')
        # Check that 5 Room instances were auto-created
        self.assertEqual(Room.objects.filter(dorm=dorm).count(), 5)
        # Check room numbers are '1' through '5'
        room_numbers = list(Room.objects.filter(dorm=dorm).values_list('room_number', flat=True).order_by('id'))
        self.assertEqual(room_numbers, ['1', '2', '3', '4', '5'])

    def test_admin_updating_dorm_increases_rooms(self):
        self._auth(self.admin)
        url = reverse('dorm-detail', args=[self.dorm.id])
        # Initially Kilimanjaro has 1 room (created in setUp)
        self.assertEqual(Room.objects.filter(dorm=self.dorm).count(), 1)
        res = self.client.patch(url, {'number_of_rooms': 3})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Check rooms list increased
        self.assertEqual(Room.objects.filter(dorm=self.dorm).count(), 3)
        room_numbers = list(Room.objects.filter(dorm=self.dorm).values_list('room_number', flat=True).order_by('id'))
        self.assertEqual(room_numbers, ['101', '2', '3']) # '101' was manually created in setup, 2 and 3 auto-created

