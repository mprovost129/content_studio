from django import forms

from .models import (
    BrandProfile,
    CaptionDraft,
    GraphicAsset,
    GraphicTemplate,
    Lesson,
    LessonBlock,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class LessonForm(StyledModelForm):
    class Meta:
        model = Lesson
        fields = (
            "title",
            "summary",
            "status",
            "difficulty",
            "category",
            "tags",
            "series",
            "series_position",
            "accent_color",
            "call_to_action",
            "seo_title",
            "seo_description",
            "enable_playground",
            "internal_notes",
        )
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "internal_notes": forms.Textarea(attrs={"rows": 3}),
            "accent_color": forms.TextInput(attrs={"type": "color"}),
        }
        help_texts = {
            "title": "Use a clear learner-facing topic, such as Python List Comprehensions.",
            "summary": "Describe what the learner will understand or build in one or two sentences.",
            "status": "Keep new work in Draft; move it to In review or Ready after checking it.",
            "category": "The primary topic used for organization and website discovery.",
            "tags": "Optional search terms. Hold Ctrl while selecting multiple tags on Windows.",
            "series": "Optional. Use when this lesson belongs to a planned sequence.",
            "series_position": "The lesson number inside its series, if applicable.",
            "accent_color": "Leave unchanged to use the category or default brand color.",
            "call_to_action": "Leave blank to use the default call to action from Branding.",
            "seo_title": "Recommended before website export; aim for 30–60 characters.",
            "seo_description": "Recommended before website export; aim for 120–160 characters.",
            "enable_playground": (
                "Opt in only when the code uses browser-compatible Python. Code runs in the "
                "visitor's browser, never on the Django server."
            ),
            "internal_notes": "Private planning notes. These are not included in generated outputs.",
        }


class LessonBlockForm(StyledModelForm):
    class Meta:
        model = LessonBlock
        fields = ("block_type", "title", "content", "data")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
            "data": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": '{"choices": ["A", "B"], "answer": "A"}',
                }
            ),
        }
        help_texts = {
            "content": "Use plain text. Code and output blocks preserve line breaks.",
            "data": "Optional structured details in JSON, such as quiz choices or an answer.",
        }


class BrandProfileForm(StyledModelForm):
    class Meta:
        model = BrandProfile
        fields = (
            "name",
            "social_handle",
            "default_accent",
            "background_color",
            "default_call_to_action",
            "logo",
        )
        widgets = {
            "default_accent": forms.TextInput(attrs={"type": "color"}),
            "background_color": forms.TextInput(attrs={"type": "color"}),
        }


class CaptionGenerationForm(forms.Form):
    platforms = forms.MultipleChoiceField(
        choices=CaptionDraft.Platform.choices,
        initial=[
            CaptionDraft.Platform.FACEBOOK,
            CaptionDraft.Platform.INSTAGRAM,
            CaptionDraft.Platform.THREADS,
        ],
        widget=forms.CheckboxSelectMultiple,
    )


class CaptionDraftForm(StyledModelForm):
    class Meta:
        model = CaptionDraft
        fields = ("content", "status")
        widgets = {"content": forms.Textarea(attrs={"rows": 14})}


class GraphicGenerationForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=GraphicTemplate.objects.none(), widget=forms.Select(attrs={"class": "form-select"})
    )
    output_formats = forms.MultipleChoiceField(
        choices=GraphicAsset.Format.choices,
        initial=[GraphicAsset.Format.INSTAGRAM_SQUARE],
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = GraphicTemplate.objects.filter(is_active=True)
