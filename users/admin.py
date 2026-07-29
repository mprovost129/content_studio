from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "display_name",
        "skill_level",
        "weekly_goal_minutes",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "skill_level",
        "email_lesson_reminders",
        "email_product_updates",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "display_name",
        "learning_goal",
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "display_name",
                    "skill_level",
                    "learning_goal",
                    "weekly_goal_minutes",
                    "email_lesson_reminders",
                    "email_product_updates",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "display_name",
                    "skill_level",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
