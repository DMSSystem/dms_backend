# rooms/models.py
from django.db import models
from django.utils import timezone

class Dorm(models.Model):
    """
    Stores dormitory information including dorm name, number of rooms, and default capacity
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)  # 'Kilimanjaro', 'A Block', 'Blue House'
    number_of_rooms = models.PositiveIntegerField(default=1)
    room_capacity = models.PositiveIntegerField(default=4)

    class Meta:
        db_table = 'dorm'
        verbose_name = 'Dorm'
        verbose_name_plural = 'Dorms'

    def __str__(self):
        return self.name


class Room(models.Model):
    """
    Stores dormitory room information including dorm, capacity, and current occupancy
    """
    dorm = models.ForeignKey(Dorm, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField(default=4)
    current_occupancy = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'room'
        unique_together = ['dorm', 'room_number']  # Prevent duplicate rooms in same dorm
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
    
    def __str__(self):
        return f"{self.dorm.name} - Room {self.room_number}"
    
    def is_available(self):
        return self.current_occupancy < self.capacity


class AcademicTerm(models.Model):
    """
    Stores academic term/semester records for institutional tracking.
    Only one term can be active at a time.
    """
    name = models.CharField(max_length=100)          # e.g. 'Term 1 2026', 'Semester 2 2025'
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_term'
        verbose_name = 'Academic Term'
        verbose_name_plural = 'Academic Terms'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} – {self.end_date})"

    def save(self, *args, **kwargs):
        """Ensure only one term is active at a time."""
        if self.is_active:
            AcademicTerm.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
