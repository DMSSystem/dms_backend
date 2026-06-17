# leave_out/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from users.models import User
from rooms.models import Room
from students.models import Student
from .models import LeaveOut

class LeaveOutAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_lo', email='admin_lo@dms.com',
            password='Admin@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_lo', email='officer_lo@dms.com',
            password='Officer@1234', role='officer'
        )
        self.parent1 = User.objects.create_user(
            username='parent1_lo', email='parent1_lo@dms.com',
            password='Parent1@1234', role='parent'
        )
        
        self.room = Room.objects.create(dorm_name='Everest', room_number='404', capacity=4)
        
        self.student = Student.objects.create(
            full_name='Charlie Brown',
            admission_no='ADM003',
            room=self.room,
            parent=self.parent1
        )
        
        # Create a leave out
        self.leave_out = LeaveOut.objects.create(
            student=self.student,
            leave_date=timezone.now().date(),
            return_date=timezone.now().date() + timezone.timedelta(days=2),
            reason='Medical checkup',
            status='pending'
        )
        
        self.list_url = reverse('leaveout-list')
        self.detail_url = reverse('leaveout-detail', args=[self.leave_out.id])
        self.approve_url = reverse('leaveout-approve', args=[self.leave_out.id])

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_officer_can_submit_leave_out(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'student': self.student.id,
            'leave_date': timezone.now().date() + timezone.timedelta(days=1),
            'return_date': timezone.now().date() + timezone.timedelta(days=3),
            'reason': 'Family function'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], 'pending')

    def test_parent_cannot_submit_leave_out(self):
        self._auth(self.parent1)
        res = self.client.post(self.list_url, {
            'student': self.student.id,
            'leave_date': timezone.now().date(),
            'return_date': timezone.now().date(),
            'reason': 'Hack'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_leave_out(self):
        self._auth(self.admin)
        res = self.client.post(self.approve_url, {'status': 'approved'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.leave_out.refresh_from_db()
        self.assertEqual(self.leave_out.status, 'approved')
        self.assertEqual(self.leave_out.approved_by, self.admin)

    def test_officer_cannot_approve_leave_out(self):
        self._auth(self.officer)
        res = self.client.post(self.approve_url, {'status': 'approved'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_overdue_filter(self):
        # Create an overdue leave out
        overdue_leave = LeaveOut.objects.create(
            student=self.student,
            leave_date=timezone.now().date() - timezone.timedelta(days=5),
            return_date=timezone.now().date() - timezone.timedelta(days=2),
            reason='Holiday',
            status='approved'
        )
        
        self._auth(self.officer)
        res = self.client.get(self.list_url + '?overdue=true')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should return only overdue_leave, not the active leave_out
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['id'], overdue_leave.id)
        self.assertTrue(overdue_leave.is_overdue())
