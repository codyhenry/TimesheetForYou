from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("timesheets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="timesheetsubmission",
            name="is_late_submission",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="timesheetsubmission",
            name="late_submission_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="weeklytimesheet",
            name="is_late_submission",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="weeklytimesheet",
            name="late_submission_note",
            field=models.TextField(blank=True),
        ),
    ]
