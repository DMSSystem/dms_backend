# duty_roster/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from users.models import User
from rooms.models import Room, Dorm
from students.models import Student
from .models import DutyRoster, DutyAssignment

class DutyRosterAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_dr', email='admin_dr@dms.com',
            password='Admin_dr@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_dr', email='officer_dr@dms.com',
            password='Officer_dr@1234', role='officer'
        )
        self.parent1 = User.objects.create_user(
            username='parent1_dr', email='parent1_dr@dms.com',
            password='Parent1_dr@1234', role='parent'
        )
        
        self.dorm = Dorm.objects.create(name='Kilimanjaro', number_of_rooms=1, room_capacity=4)
        self.room = Room.objects.create(dorm=self.dorm, room_number='505', capacity=4)

        
        self.student = Student.objects.create(
            full_name='Charlie Brown',
            admission_no='ADM003',
            room=self.room,
            parent=self.parent1
        )
        
        # Create roster
        self.roster = DutyRoster.objects.create(
            duty_date=timezone.now().date(),
            dorm_name='Kilimanjaro',
            task='dorm_cleaning',
            shift='morning',
            created_by=self.admin
        )
        
        self.assignment = DutyAssignment.objects.create(
            duty_roster=self.roster,
            student=self.student,
            status='pending'
        )
        
        self.roster_list_url = reverse('duty-roster-list')
        self.assignment_detail_url = reverse('duty-assignment-detail', args=[self.assignment.id])

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_admin_can_create_roster_with_assignments(self):
        self._auth(self.admin)
        res = self.client.post(self.roster_list_url, {
            'duty_date': timezone.now().date() + timezone.timedelta(days=1),
            'dorm_name': 'Kilimanjaro',
            'task': 'bathroom',
            'shift': 'morning',
            'student_ids': [self.student.id]
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DutyRoster.objects.filter(task='bathroom').exists())
        self.assertEqual(DutyAssignment.objects.filter(duty_roster__task='bathroom').count(), 1)

    def test_officer_cannot_create_roster(self):
        self._auth(self.officer)
        res = self.client.post(self.roster_list_url, {
            'duty_date': timezone.now().date() + timezone.timedelta(days=1),
            'dorm_name': 'Kilimanjaro',
            'task': 'bathroom',
            'shift': 'morning',
            'student_ids': [self.student.id]
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_officer_can_update_assignment_status(self):
        self._auth(self.officer)
        self.assertIsNone(self.assignment.completed_at)
        res = self.client.patch(self.assignment_detail_url, {'status': 'completed', 'remarks': 'Great job'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.status, 'completed')
        self.assertIsNotNone(self.assignment.completed_at)

    def test_parent_only_sees_child_assignments(self):
        # Create another student and assignment not belonging to parent1
        student2 = Student.objects.create(full_name='Jane Doe', admission_no='ADM009', room=self.room)
        DutyAssignment.objects.create(duty_roster=self.roster, student=student2, status='pending')
        
        self._auth(self.parent1)
        res = self.client.get(reverse('duty-assignment-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['student_admission_no'], 'ADM003')
