from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("timesheets", "0003_timesheet_week_lock"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeentry",
            name="family_requested_nanny",
            field=models.BooleanField(default=False),
        ),
    ]
