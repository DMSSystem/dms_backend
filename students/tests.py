# students/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from rooms.models import Room, Dorm
from .models import Student, EmergencyContact

class StudentAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin_st', email='admin_st@dms.com',
            password='Admin_st@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer_st', email='officer_st@dms.com',
            password='Officer_st@1234', role='officer'
        )
        self.parent1 = User.objects.create_user(
            username='parent1_st', email='parent1_st@dms.com',
            password='Parent1_st@1234', role='parent'
        )
        self.parent2 = User.objects.create_user(
            username='parent2_st', email='parent2_st@dms.com',
            password='Parent2_st@1234', role='parent'
        )
        
        # Create rooms
        self.dorm = Dorm.objects.create(name='Lhotse', number_of_rooms=1, room_capacity=4)
        self.room = Room.objects.create(dorm=self.dorm, room_number='303', capacity=4)

        
        # Create students
        self.student1 = Student.objects.create(
            full_name='John Doe',
            admission_no='ADM001',
            room=self.room,
            parent=self.parent1
        )
        self.student2 = Student.objects.create(
            full_name='Jane Smith',
            admission_no='ADM002',
            room=self.room,
            parent=self.parent2
        )
        
        # Emergency Contacts
        self.contact1 = EmergencyContact.objects.create(
            student=self.student1,
            name='Robert Doe',
            relationship='Father',
            phone='0711111111'
        )
        self.contact2 = EmergencyContact.objects.create(
            student=self.student2,
            name='Mary Smith',
            relationship='Mother',
            phone='0722222222'
        )

        # URLs
        self.list_url = reverse('student-list')
        self.contact_list_url = reverse('emergency-contact-list')

    def _auth(self, user):
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_admin_can_list_all_students(self):
        self._auth(self.admin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Pagination disabled: root is a list
        self.assertEqual(len(res.data), 2)

    def test_parent_can_only_see_own_child(self):
        self._auth(self.parent1)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['admission_no'], 'ADM001')

    def test_parent_only_gets_own_child_contact(self):
        self._auth(self.parent2)
        res = self.client.get(self.contact_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['name'], 'Mary Smith')

    def test_by_admission_endpoint(self):
        # Admin gets child 1
        self._auth(self.admin)
        url = reverse('student-by-admission', args=['ADM001'])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['full_name'], 'John Doe')

        # Parent 1 gets child 1
        self._auth(self.parent1)
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # Parent 2 gets child 1 (not allowed -> 404)
        self._auth(self.parent2)
        res3 = self.client.get(url)
        self.assertEqual(res3.status_code, status.HTTP_404_NOT_FOUND)

    def test_by_room_endpoint(self):
        self._auth(self.officer)
        url = reverse('students-by-room', args=[self.room.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 2)

    def test_officer_can_create_student_with_emergency_contacts(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'full_name': 'Bill Gates',
            'admission_no': 'ADM999',
            'room': self.room.id,
            'grade': 'Form 4',
            'stream': 'Blue',
            'emergency_contacts': [
                {'name': 'Melinda Gates', 'relationship': 'Spouse', 'phone': '0733333333'}
            ]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Student.objects.filter(admission_no='ADM999').exists())
        student = Student.objects.get(admission_no='ADM999')
        self.assertEqual(student.grade, 'Form 4')
        self.assertEqual(student.stream, 'Blue')
        self.assertEqual(student.emergency_contacts.count(), 1)
        self.assertEqual(student.emergency_contacts.first().name, 'Melinda Gates')

    def test_student_creation_without_emergency_contacts_rejected(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'full_name': 'Steve Jobs',
            'admission_no': 'ADM888',
            'room': self.room.id,
            'emergency_contacts': []
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_parent_cannot_create_student(self):
        self._auth(self.parent1)
        res = self.client.post(self.list_url, {
            'full_name': 'Mark Zuckerberg',
            'admission_no': 'ADM777',
            'room': self.room.id,
            'emergency_contacts': [
                {'name': 'Priscilla Chan', 'relationship': 'Spouse', 'phone': '0744444444'}
            ]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
