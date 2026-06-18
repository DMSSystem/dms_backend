# Generated manually
from django.db import migrations, models
import django.db.models.deletion

def populate_null_dorms(apps, schema_editor):
    Room = apps.get_model('rooms', 'Room')
    Dorm = apps.get_model('rooms', 'Dorm')
    
    null_rooms = Room.objects.filter(dorm__isnull=True)
    if null_rooms.exists():
        # Get first existing dorm or create 'Kilimanjaro'
        dorm = Dorm.objects.first()
        if not dorm:
            dorm, _ = Dorm.objects.get_or_create(
                name='Kilimanjaro',
                defaults={
                    'number_of_rooms': 1,
                    'room_capacity': 4
                }
            )
        for room in null_rooms:
            room.dorm = dorm
            room.save()
        # Sync the dorm's room count
        dorm.number_of_rooms = Room.objects.filter(dorm=dorm).count()
        dorm.save()


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0002_dorm_alter_room_unique_together_room_dorm_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_null_dorms, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='room',
            name='dorm',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rooms',
                to='rooms.dorm'
            ),
        ),
    ]

