# Generated for the live-tracking snapshot used to reconnect customer clients.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_incentive_technicianwallet_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicerequest',
            name='technician_latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='technician_longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='route_distance_meters',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='route_eta_seconds',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='tracking_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
