from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("timesheets", "0002_late_submission_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimesheetWeekLock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("week_start_date", models.DateField(unique=True)),
                ("week_end_date", models.DateField()),
                ("note", models.TextField(blank=True)),
                ("locked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "locked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="locked_timesheet_weeks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-week_start_date"],
            },
        ),
    ]
