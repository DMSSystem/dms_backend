from django.contrib import admin
from .models import Dorm, Room

@admin.register(Dorm)
class DormAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_rooms', 'room_capacity')
    search_fields = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('dorm', 'room_number', 'capacity', 'current_occupancy')
    list_filter = ('dorm', 'capacity')
    search_fields = ('room_number', 'dorm__name')

