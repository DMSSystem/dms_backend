# rooms/models.py
from django.db import models

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

