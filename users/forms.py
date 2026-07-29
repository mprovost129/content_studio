from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class LearnerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False)
    display_name = forms.CharField(max_length=80, required=False)
    skill_level = forms.ChoiceField(choices=User.SkillLevel.choices, required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "display_name",
            "skill_level",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class LearnerProfileForm(forms.ModelForm):
    weekly_goal_minutes = forms.IntegerField(
        min_value=5,
        max_value=600,
        help_text="A realistic weekly target. Start small; 30–60 minutes is plenty for beginners.",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "display_name",
            "skill_level",
            "learning_goal",
            "weekly_goal_minutes",
            "email_lesson_reminders",
            "email_product_updates",
        )
        widgets = {
            "learning_goal": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "display_name": "Shown on your dashboard and future community features.",
            "skill_level": "Used later for better lesson recommendations.",
            "learning_goal": "Private note to help you remember why you are learning Python.",
            "email_lesson_reminders": "Foundation for future reminder emails. No automated emails are sent yet.",
            "email_product_updates": "Foundation for future Code with Michael updates. No automated emails are sent yet.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")
