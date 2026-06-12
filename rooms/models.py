# rooms/models.py
from django.db import models

class Room(models.Model):
    """
    Stores dormitory room information including dorm name, block, capacity, and current occupancy
    """
    # Changed from 'dorm_block' to 'dorm_name' for flexibility
    dorm_name = models.CharField(max_length=100, db_index=True)  # 'Kilimanjaro', 'A Block', 'Blue House'
    room_number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField(default=4)
    current_occupancy = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'room'
        unique_together = ['dorm_name', 'room_number']  # Prevent duplicate rooms in same dorm
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
    
    def __str__(self):
        return f"{self.dorm_name} - Room {self.room_number}"
    
    def is_available(self):
        return self.current_occupancy < self.capacity
