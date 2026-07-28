from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_badges(apps, schema_editor):
    LearnerBadge = apps.get_model("studio", "LearnerBadge")
    defaults = [
        {
            "key": "first-lesson",
            "title": "First Python Win",
            "description": "Completed your first Code with Michael lesson.",
            "criteria_type": "lessons_completed",
            "threshold": 1,
        },
        {
            "key": "five-lessons",
            "title": "Python Starter",
            "description": "Completed five beginner Python lessons.",
            "criteria_type": "lessons_completed",
            "threshold": 5,
        },
        {
            "key": "first-quiz-correct",
            "title": "Quiz Checkpoint",
            "description": "Answered your first quiz question correctly.",
            "criteria_type": "quizzes_correct",
            "threshold": 1,
        },
        {
            "key": "first-challenge-passed",
            "title": "Code Runner",
            "description": "Saved your first passing coding challenge attempt.",
            "criteria_type": "challenges_passed",
            "threshold": 1,
        },
    ]
    for item in defaults:
        LearnerBadge.objects.update_or_create(key=item["key"], defaults=item)


def unseed_badges(apps, schema_editor):
    LearnerBadge = apps.get_model("studio", "LearnerBadge")
    LearnerBadge.objects.filter(key__in=["first-lesson", "five-lessons", "first-quiz-correct", "first-challenge-passed"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("studio", "0007_quizzes_challenges"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearnerBadge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("key", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("criteria_type", models.CharField(choices=[("lessons_completed", "Lessons completed"), ("quizzes_correct", "Correct quiz answers"), ("challenges_passed", "Challenges passed")], max_length=40)),
                ("threshold", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ("criteria_type", "threshold", "title")},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("not_started", "Not started"), ("in_progress", "In progress"), ("completed", "Completed")], default="in_progress", max_length=20)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("last_activity_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("quiz_correct", models.PositiveSmallIntegerField(default=0)),
                ("quiz_total", models.PositiveSmallIntegerField(default=0)),
                ("challenges_passed", models.PositiveSmallIntegerField(default=0)),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_records", to="studio.lesson")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-last_activity_at",)},
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("response_text", models.TextField(blank=True)),
                ("is_correct", models.BooleanField(default=False)),
                ("feedback", models.TextField(blank=True)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="studio.quizquestion")),
                ("selected_choice", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attempts", to="studio.quizchoice")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="LearnerBadgeAward",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("awarded_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("badge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="awards", to="studio.learnerbadge")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="badge_awards", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-awarded_at",)},
        ),
        migrations.AddConstraint(model_name="lessonprogress", constraint=models.UniqueConstraint(fields=("user", "lesson"), name="unique_user_lesson_progress")),
        migrations.AddConstraint(model_name="learnerbadgeaward", constraint=models.UniqueConstraint(fields=("user", "badge"), name="unique_user_badge_award")),
        migrations.RunPython(seed_badges, unseed_badges),
    ]
