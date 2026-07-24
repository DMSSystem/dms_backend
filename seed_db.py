import os
import django

# Set django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dms_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from rooms.models import Dorm, Room, AcademicTerm
from students.models import Student, EmergencyContact
from leave_out.models import LeaveOut
from maintenance.models import MaintenanceRequest

User = get_user_model()

def seed():
    print("Clearing old database records...")
    LeaveOut.objects.all().delete()
    MaintenanceRequest.objects.all().delete()
    EmergencyContact.objects.all().delete()
    Student.objects.all().delete()
    Room.objects.all().delete()
    Dorm.objects.all().delete()
    AcademicTerm.objects.all().delete()
    User.objects.all().delete()

    print("Creating user accounts...")
    # 1. Admin
    admin_user = User.objects.create_superuser(
        username='admin',
        email='emarube89@gmail.com',
        password='Password123',
        first_name='Senior Boarding',
        last_name='Master',
        role='admin',
        is_verified=True,
        is_active=True
    )
    print("- Created Admin: admin / Password123")

    # 2. Officer
    officer_user = User.objects.create_user(
        username='officer',
        email='officer@school.com',
        password='Password123',
        first_name='Boarding',
        last_name='Master',
        role='officer',
        is_verified=True,
        is_active=True
    )
    print("- Created Officer: officer / Password123")

    # 3. Parent
    parent_user = User.objects.create_user(
        username='parent',
        email='parent@guardian.com',
        password='Password123',
        first_name='John',
        last_name='Doe',
        role='parent',
        phone='+254712345678',
        is_verified=True,
        is_active=True
    )
    print("- Created Parent: parent / Password123")

    print("Creating dormitory blocks...")
    # We create dorms. The serializer create method would normally do bulk creation, but we can do it directly:
    dorm_kili = Dorm.objects.create(name="Kilimanjaro", number_of_rooms=4, room_capacity=4)
    rooms_kili = [
        Room.objects.create(dorm=dorm_kili, room_number=str(i), capacity=4, current_occupancy=0)
        for i in range(1, 5)
    ]
    
    dorm_ruw = Dorm.objects.create(name="Ruwenzori", number_of_rooms=4, room_capacity=4)
    rooms_ruw = [
        Room.objects.create(dorm=dorm_ruw, room_number=str(i), capacity=4, current_occupancy=0)
        for i in range(1, 5)
    ]
    print("- Created Dorm blocks: Kilimanjaro, Ruwenzori")

    print("Creating academic terms...")
    term = AcademicTerm.objects.create(
        name="Term 2 2026",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 8, 15),
        is_active=True
    )
    print("- Created active Academic Term: Term 2 2026")

    print("Creating students...")
    # Student 1 (assigned to Parent)
    room_1 = rooms_kili[0]
    student_1 = Student.objects.create(
        full_name="Ian Okoth",
        admission_no="1249",
        grade="Year 10",
        stream="West",
        room=room_1,
        parent=parent_user
    )
    # Update room occupancy
    room_1.current_occupancy = 1
    room_1.save()

    EmergencyContact.objects.create(
        student=student_1,
        name="John Doe",
        relationship="Father",
        phone="+254712345678"
    )

    # Student 2
    room_2 = rooms_kili[1]
    student_2 = Student.objects.create(
        full_name="Mich Sego",
        admission_no="1248",
        grade="Year 11",
        stream="East",
        room=room_2
    )
    room_2.current_occupancy = 1
    room_2.save()

    EmergencyContact.objects.create(
        student=student_2,
        name="Mary Sego",
        relationship="Mother",
        phone="+254787654321"
    )
    print("- Created Students: Ian Okoth, Mich Sego")

    print("Creating leaves and maintenance requests...")
    # Active leave
    LeaveOut.objects.create(
        student=student_1,
        leave_date=timezone.now().date() + timedelta(days=2),
        return_date=timezone.now().date() + timedelta(days=4),
        reason="Family event",
        status="approved",
        approved_by=officer_user
    )

    # Overdue leave
    LeaveOut.objects.create(
        student=student_2,
        leave_date=timezone.now().date() - timedelta(days=5),
        return_date=timezone.now().date() - timedelta(days=1),
        reason="Medical checkup",
        status="approved",
        approved_by=officer_user
    )

    # Completed leave
    LeaveOut.objects.create(
        student=student_1,
        leave_date=timezone.now().date() - timedelta(days=10),
        return_date=timezone.now().date() - timedelta(days=8),
        reason="Fees clearance",
        status="completed",
        approved_by=officer_user
    )

    # Maintenance Request
    MaintenanceRequest.objects.create(
        dorm_block=dorm_kili,
        location="Room 1 bathroom",
        description="Leaking sink faucet, causing minor flooding.",
        urgency="medium",
        status="pending",
        reported_by=officer_user
    )

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
