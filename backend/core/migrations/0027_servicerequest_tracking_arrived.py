from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_servicerequest_tracking_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicerequest',
            name='tracking_arrived',
            field=models.BooleanField(default=False),
        ),
    ]
