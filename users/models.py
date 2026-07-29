from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class SkillLevel(models.TextChoices):
        NEW = "new", "Brand new"
        BEGINNER = "beginner", "Beginner"
        RETURNING = "returning", "Returning learner"
        INTERMEDIATE = "intermediate", "Intermediate"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(
        max_length=80,
        blank=True,
        help_text="Optional public-facing name shown on learner pages.",
    )
    skill_level = models.CharField(
        max_length=20, choices=SkillLevel.choices, default=SkillLevel.NEW
    )
    learning_goal = models.TextField(
        blank=True,
        help_text="Optional private goal, such as building a first project or learning Django.",
    )
    weekly_goal_minutes = models.PositiveSmallIntegerField(
        default=30,
        help_text="Target weekly learning time in minutes.",
    )
    email_lesson_reminders = models.BooleanField(default=True)
    email_product_updates = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.display_name or self.first_name or self.email.split("@")[0]

    @property
    def learner_name(self):
        return self.display_name or self.get_full_name() or self.email.split("@")[0]

    def __str__(self):
        return self.email
