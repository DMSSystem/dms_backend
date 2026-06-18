# Generated manually
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0002_dorm_alter_room_unique_together_room_dorm_and_more'),
    ]

    operations = [
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
