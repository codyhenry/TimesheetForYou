from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="force_password_change",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                blank=True,
                choices=[("nanny", "Nanny"), ("office", "Office"), ("admin", "Admin")],
                max_length=20,
            ),
        ),
    ]
