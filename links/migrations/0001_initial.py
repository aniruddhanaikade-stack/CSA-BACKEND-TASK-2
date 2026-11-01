from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Link",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("long_url", models.URLField(max_length=2000, unique=True)),
                ("code", models.CharField(max_length=10, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("visits", models.IntegerField(default=0)),
            ],
        ),
    ]
