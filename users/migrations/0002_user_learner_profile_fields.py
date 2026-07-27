# Generated manually for phase 6 learner profiles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="display_name",
            field=models.CharField(blank=True, help_text="Optional public-facing name shown on learner pages.", max_length=80),
        ),
        migrations.AddField(
            model_name="user",
            name="skill_level",
            field=models.CharField(choices=[("new", "Brand new"), ("beginner", "Beginner"), ("returning", "Returning learner"), ("intermediate", "Intermediate")], default="new", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="learning_goal",
            field=models.TextField(blank=True, help_text="Optional private goal, such as building a first project or learning Django."),
        ),
        migrations.AddField(
            model_name="user",
            name="weekly_goal_minutes",
            field=models.PositiveSmallIntegerField(default=30, help_text="Target weekly learning time in minutes."),
        ),
        migrations.AddField(
            model_name="user",
            name="email_lesson_reminders",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_product_updates",
            field=models.BooleanField(default=False),
        ),
    ]
