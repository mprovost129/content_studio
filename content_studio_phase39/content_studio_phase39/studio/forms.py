import json

from django import forms
from django.utils import timezone

from .services.recommendation_tuning_presets import PRESET_CHOICES

from .models import (
    BrandProfile,
    CaptionDraft,
    CodeChallenge,
    ChallengeTestCase,
    Category,
    ContentPlan,
    GraphicAsset,
    GraphicTemplate,
    Lesson,
    LearningResource,
    ResourceCTA,
    RecommendationTuning,
    ExperimentDecisionTuning,
    RecommendationTuningChangeLog,
    LessonBlock,
    NewsletterSubscriber,
    NewsletterCampaign,
    NewsletterMetricImport,
    SubscriberSegment,
    PublishingRecord,
    QuizChoice,
    QuizQuestion,
    Series,
)


class RecommendationTuningExperimentSnapshotForm(forms.Form):
    window_days = forms.TypedChoiceField(
        coerce=int,
        choices=((7, "7 days before/after"), (14, "14 days before/after"), (30, "30 days before/after"), (60, "60 days before/after")),
        initial=14,
        label="Comparison window",
        help_text="The same number of days will be compared before and after the tuning change timestamp.",
    )
    notes = forms.CharField(
        required=False,
        label="Snapshot notes",
        help_text="Optional note about what you are trying to learn from this experiment snapshot.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


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



class RecommendationTuningForm(StyledModelForm):
    change_reason = forms.CharField(
        required=False,
        label="Reason for change",
        help_text="Optional note for the audit log, such as testing lead magnets or resetting after a simulation.",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    experiment_label = forms.CharField(
        required=False,
        max_length=160,
        label="Experiment label",
        help_text="Optional name for this tuning test, such as August Instagram growth test.",
    )
    experiment_status = forms.ChoiceField(
        required=False,
        choices=RecommendationTuningChangeLog.ExperimentStatus.choices,
        initial=RecommendationTuningChangeLog.ExperimentStatus.NOT_EXPERIMENT,
        label="Experiment status",
        help_text="Use Running or Planned when this change is part of a recommendation-ranking experiment.",
    )
    experiment_notes = forms.CharField(
        required=False,
        label="Experiment notes",
        help_text="Optional hypothesis or success criteria for this experiment.",
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = RecommendationTuning
        fields = (
            "name",
            "is_active",
            "lesson_cta_bonus",
            "quiz_cta_bonus",
            "challenge_cta_bonus",
            "pdf_open_bonus",
            "pdf_lead_magnet_bonus",
            "newsletter_cta_bonus",
            "related_lesson_weight",
            "category_match_weight",
            "difficulty_match_weight",
            "topic_overlap_weight",
            "topic_overlap_cap",
            "active_quiz_weight",
            "active_challenge_weight",
            "practice_code_weight",
            "conversion_weight",
            "conversion_cap",
            "cta_click_weight",
            "cta_click_cap",
            "exact_accepted_boost",
            "exact_dismissed_penalty",
            "ignored_per_show_penalty",
            "ignored_penalty_cap",
            "similar_accepted_boost",
            "similar_accepted_cap",
            "similar_dismissed_penalty",
            "similar_dismissed_cap",
            "similar_ignored_penalty",
            "similar_ignored_cap",
            "same_lesson_accepted_boost",
            "same_lesson_accepted_cap",
            "same_lesson_dismissed_penalty",
            "same_lesson_dismissed_cap",
            "feedback_adjustment_floor",
            "feedback_adjustment_ceiling",
            "notes",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "lesson_cta_bonus": "Base bonus for Start matching lesson recommendations.",
            "quiz_cta_bonus": "Base bonus for Try quiz next recommendations.",
            "challenge_cta_bonus": "Base bonus for Practice with a challenge recommendations.",
            "pdf_open_bonus": "Base bonus for open PDF download recommendations.",
            "pdf_lead_magnet_bonus": "Base bonus for email-gated PDF lead magnet recommendations.",
            "newsletter_cta_bonus": "Base bonus for Join the newsletter recommendations.",
            "related_lesson_weight": "Score added when a lesson is already related to the resource.",
            "category_match_weight": "Score added when resource and lesson categories match.",
            "difficulty_match_weight": "Score added when learner levels match.",
            "topic_overlap_weight": "Score per matching topic keyword.",
            "topic_overlap_cap": "Maximum keyword-overlap score.",
            "conversion_weight": "Score per prior resource-attributed conversion.",
            "cta_click_weight": "Score per prior CTA click.",
            "feedback_adjustment_floor": "Lowest total feedback adjustment allowed, usually a negative number.",
            "feedback_adjustment_ceiling": "Highest total feedback adjustment allowed.",
        }

    def clean(self):
        cleaned = super().clean()
        floor = cleaned.get("feedback_adjustment_floor")
        ceiling = cleaned.get("feedback_adjustment_ceiling")
        if floor is not None and ceiling is not None and floor > ceiling:
            raise forms.ValidationError("Feedback adjustment floor must be less than or equal to the ceiling.")
        return cleaned





class RecommendationTuningExperimentOutcomeForm(StyledModelForm):
    class Meta:
        model = RecommendationTuningChangeLog
        fields = (
            "experiment_label",
            "experiment_status",
            "experiment_outcome",
            "experiment_notes",
        )
        widgets = {
            "experiment_notes": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "experiment_label": "Name the test so it can be reviewed later.",
            "experiment_status": "Mark whether the experiment is still running, should be kept, or should be rolled back.",
            "experiment_outcome": "Record the result once enough performance data is available.",
            "experiment_notes": "Summarize what happened and the decision you made.",
        }

class RecommendationTuningSimulationForm(forms.Form):
    resource = forms.ModelChoiceField(
        queryset=LearningResource.objects.all().order_by("title"),
        required=False,
        label="Resource to simulate",
        help_text="Choose a resource to compare how each preset ranks CTA recommendations.",
    )
    preset_keys = forms.MultipleChoiceField(
        choices=PRESET_CHOICES,
        required=False,
        label="Presets to compare",
        help_text="Leave blank to compare every preset against the active tuning profile.",
        widget=forms.CheckboxSelectMultiple,
    )
    limit = forms.IntegerField(
        min_value=3,
        max_value=12,
        initial=8,
        label="Recommendations per profile",
        help_text="Keep this small when comparing many presets side by side.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resource"].widget.attrs.setdefault("class", "form-select")
        self.fields["limit"].widget.attrs.setdefault("class", "form-control")



class ExperimentDecisionTuningForm(StyledModelForm):
    class Meta:
        model = ExperimentDecisionTuning
        fields = (
            "name",
            "is_active",
            "keep_score_threshold",
            "keep_primary_positive_min",
            "keep_high_confidence_score",
            "rollback_score_threshold",
            "rollback_primary_negative_min",
            "rollback_high_confidence_score",
            "low_confidence_abs_score",
            "max_metric_change_magnitude",
            "social_new_followers_weight",
            "social_engagements_weight",
            "social_reach_weight",
            "social_clicks_weight",
            "resources_pdf_downloads_weight",
            "resources_pdf_unlocks_weight",
            "resources_subscribers_weight",
            "newsletter_clicks_weight",
            "newsletter_open_rate_weight",
            "ctas_cta_clicks_weight",
            "conversions_total_conversions_weight",
            "conversions_lesson_views_weight",
            "conversions_quiz_attempts_weight",
            "conversions_challenge_attempts_weight",
            "conversions_lesson_completions_weight",
            "newsletter_unsubscribes_penalty_weight",
            "newsletter_bounces_penalty_weight",
            "notes",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "keep_score_threshold": "Minimum weighted score required before Studio recommends keeping a tuning experiment.",
            "keep_primary_positive_min": "Minimum number of primary growth signals that must improve for a keep recommendation.",
            "keep_high_confidence_score": "Score at or above this value shows high confidence for keep recommendations.",
            "rollback_score_threshold": "Score at or below this value triggers rollback consideration. Use a negative number.",
            "rollback_primary_negative_min": "Minimum number of primary growth signals that must decline for a rollback recommendation.",
            "rollback_high_confidence_score": "Score at or below this value shows high confidence for rollback recommendations.",
            "low_confidence_abs_score": "Inconclusive decisions below this absolute score are labeled low confidence.",
            "max_metric_change_magnitude": "Caps how much any single metric change can influence the decision score.",
        }

    def clean(self):
        cleaned = super().clean()
        keep = cleaned.get("keep_score_threshold")
        keep_high = cleaned.get("keep_high_confidence_score")
        rollback = cleaned.get("rollback_score_threshold")
        rollback_high = cleaned.get("rollback_high_confidence_score")
        if keep is not None and keep_high is not None and keep_high < keep:
            raise forms.ValidationError("Keep high-confidence score must be greater than or equal to the keep threshold.")
        if rollback is not None and rollback_high is not None and rollback_high > rollback:
            raise forms.ValidationError("Rollback high-confidence score must be less than or equal to the rollback threshold.")
        return cleaned



class LessonIdeaForm(forms.Form):
    topic = forms.CharField(
        max_length=180,
        label="Lesson idea",
        help_text="Use a short beginner topic, such as Python variables, for loops, functions, lists, or calculating a total price.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Python variables"}),
    )
    audience = forms.CharField(
        max_length=180,
        required=False,
        initial="absolute beginners",
        help_text="Who this draft is for. Example: absolute beginners, teens, adults new to coding, or Facebook followers.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    objective = forms.CharField(
        required=False,
        label="Learning objective",
        help_text="Optional. Leave blank and the studio will create a basic beginner objective.",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        help_text="Optional category for the draft lesson.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    series = forms.ModelChoiceField(
        queryset=Series.objects.none(),
        required=False,
        help_text="Optional learning path / series for the draft lesson.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    include_quiz = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Create one starter multiple-choice question and choices.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    include_challenge = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Create one starter code challenge and one test case.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["series"].queryset = Series.objects.filter(is_active=True).order_by("title")

    def clean_topic(self):
        topic = " ".join(self.cleaned_data["topic"].split())
        if len(topic) < 3:
            raise forms.ValidationError("Enter a more specific beginner lesson idea.")
        return topic


class ResourceIdeaForm(forms.Form):
    topic = forms.CharField(
        max_length=180,
        label="Resource idea",
        help_text="Use a short beginner topic, such as Python list cheat sheet, fixing NameError, setup VS Code, or calculating a total price.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Python list cheat sheet"}),
    )
    resource_type = forms.ChoiceField(
        choices=LearningResource.ResourceType.choices,
        initial=LearningResource.ResourceType.CHEAT_SHEET,
        help_text="Choose the kind of resource draft to create.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    audience = forms.CharField(
        max_length=180,
        required=False,
        initial="absolute beginners",
        help_text="Who this resource is for. Example: absolute beginners, adults new to coding, or Facebook followers.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        help_text="Optional category for the draft resource.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    related_lessons = forms.ModelMultipleChoiceField(
        queryset=Lesson.objects.none(),
        required=False,
        help_text="Optional lessons to connect to this resource.",
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
    )
    featured = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Feature this resource on the public learner homepage after review.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["related_lessons"].queryset = Lesson.objects.exclude(status=Lesson.Status.ARCHIVED).order_by("title")

    def clean_topic(self):
        topic = " ".join(self.cleaned_data["topic"].split())
        if len(topic) < 3:
            raise forms.ValidationError("Enter a more specific beginner resource idea.")
        return topic


class LessonForm(StyledModelForm):
    OPTIONAL_WITH_DEFAULTS = ("facebook_status", "instagram_status", "threads_status", "website_status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.OPTIONAL_WITH_DEFAULTS:
            if name in self.fields:
                self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        for name in self.OPTIONAL_WITH_DEFAULTS:
            if not cleaned.get(name):
                cleaned[name] = Lesson.Status.IDEA
        return cleaned

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
            "learning_objective",
            "beginner_takeaway",
            "common_mistake",
            "practice_prompt",
            "starter_code",
            "solution_code",
            "expected_output",
            "hint_1",
            "hint_2",
            "next_lesson",
            "facebook_status",
            "instagram_status",
            "threads_status",
            "website_status",
            "enable_playground",
            "internal_notes",
        )
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "common_mistake": forms.Textarea(attrs={"rows": 3}),
            "practice_prompt": forms.Textarea(attrs={"rows": 3}),
            "starter_code": forms.Textarea(attrs={"rows": 8, "class": "form-control code-input"}),
            "solution_code": forms.Textarea(attrs={"rows": 8, "class": "form-control code-input"}),
            "expected_output": forms.Textarea(attrs={"rows": 4, "class": "form-control code-input"}),
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
            "learning_objective": "Begin with a measurable result, such as Learner can create and print a variable.",
            "beginner_takeaway": "Plain-language memory hook for the learner and social captions.",
            "common_mistake": "Useful for beginner warning boxes, carousels, and follow-up posts.",
            "practice_prompt": "A small task the learner can try after the explanation.",
            "starter_code": "Optional starter file for playground challenges.",
            "solution_code": "Optional reviewed answer. Use for your reference and future answer reveal features.",
            "expected_output": "Optional output for manual checking or future answer validation.",
            "hint_1": "First gentle hint for a challenge.",
            "hint_2": "Second, more direct hint for a challenge.",
            "next_lesson": "Optional next lesson to recommend in a path.",
            "facebook_status": "Track this lesson's Facebook production state separately from the lesson's master status.",
            "instagram_status": "Track this lesson's Instagram production state separately from the lesson's master status.",
            "threads_status": "Track this lesson's Threads production state separately from the lesson's master status.",
            "website_status": "Track this lesson's public website production state separately from the lesson's master status.",
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


    def clean_data(self):
        value = self.cleaned_data.get("data")
        if value in (None, ""):
            return {}
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise forms.ValidationError(f"Enter valid JSON: {exc.msg}.") from exc
        if not isinstance(value, dict):
            raise forms.ValidationError("Structured data must be a JSON object, such as {\"answer\": \"A\"}.")
        return value

class BlockTemplateApplyForm(forms.Form):
    template_key = forms.ChoiceField(
        label="Block template",
        choices=(),
        help_text="Choose a reusable beginner lesson structure to append to this lesson.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .services.block_templates import get_block_template_choices

        self.fields["template_key"].choices = get_block_template_choices()




class SocialCarouselTemplateApplyForm(forms.Form):
    template_key = forms.ChoiceField(
        label="Social carousel template",
        choices=(),
        help_text="Choose a brand-growth carousel format to append to this lesson.",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    output_formats = forms.MultipleChoiceField(
        label="Optional graphics to generate now",
        choices=GraphicAsset.Format.choices,
        required=False,
        initial=[GraphicAsset.Format.INSTAGRAM_SQUARE],
        widget=forms.CheckboxSelectMultiple,
        help_text="Leave unchecked to only add carousel-ready blocks.",
    )
    generate_now = forms.BooleanField(
        required=False,
        initial=False,
        label="Generate PNG assets now",
        help_text="Creates graphics immediately using the matching social carousel graphic template.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .services.social_carousels import get_social_carousel_template_choices

        self.fields["template_key"].choices = get_social_carousel_template_choices()

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


class ResourceCTAForm(StyledModelForm):
    class Meta:
        model = ResourceCTA
        fields = (
            "position",
            "target_type",
            "title",
            "description",
            "button_label",
            "target_lesson",
            "target_url",
            "is_active",
            "internal_notes",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "internal_notes": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "position": "Lower numbers appear first on the public resource page.",
            "target_type": "Choose the main action this block is trying to drive.",
            "target_lesson": "Use for matching lesson, quiz, or challenge CTAs.",
            "target_url": "Use only for external or custom links.",
            "is_active": "Inactive CTA blocks stay saved but do not show publicly.",
        }

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get("target_type")
        target_lesson = cleaned.get("target_lesson")
        target_url = cleaned.get("target_url")
        if target_type in {ResourceCTA.TargetType.LESSON, ResourceCTA.TargetType.QUIZ, ResourceCTA.TargetType.CHALLENGE} and not target_lesson:
            raise forms.ValidationError("Choose a target lesson for lesson, quiz, and challenge CTA blocks.")
        if target_type == ResourceCTA.TargetType.EXTERNAL and not target_url:
            raise forms.ValidationError("Enter a target URL for external CTA blocks.")
        return cleaned


class LearningResourceForm(StyledModelForm):
    class Meta:
        model = LearningResource
        fields = (
            "title",
            "summary",
            "resource_type",
            "status",
            "difficulty",
            "category",
            "tags",
            "related_lessons",
            "featured",
            "content",
            "beginner_tip",
            "downloadable_file",
            "pdf_download_enabled",
            "pdf_footer_note",
            "pdf_requires_email",
            "pdf_lead_magnet_headline",
            "pdf_lead_magnet_description",
            "external_url",
            "estimated_read_minutes",
            "seo_title",
            "seo_description",
            "internal_notes",
        )
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "content": forms.Textarea(attrs={"rows": 16, "class": "form-control code-input"}),
            "pdf_lead_magnet_description": forms.Textarea(attrs={"rows": 3}),
            "internal_notes": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "title": "Use a search-friendly title, such as Python List Cheat Sheet or Common Python NameError Fixes.",
            "summary": "Briefly describe who this helps and when to use it.",
            "resource_type": "Controls where this appears in the public resource library.",
            "status": "Ready and Published resources appear publicly.",
            "related_lessons": "Optional lessons that should be linked from the resource page.",
            "content": "Write the public resource body. Keep it skimmable with headings, short examples, and beginner language.",
            "beginner_tip": "One small reminder that helps beginners use this reference correctly.",
            "downloadable_file": "Optional manually uploaded PDF, image, or reference file to offer as a download.",
            "pdf_download_enabled": "Creates an on-demand branded Code with Michael PDF from this resource content.",
            "pdf_footer_note": "Optional footer note for generated PDFs. Keep it short and evergreen.",
            "pdf_requires_email": "Turn this on when the PDF should act as a lead magnet and require email signup before download.",
            "pdf_lead_magnet_headline": "Optional custom headline for the gated download page.",
            "pdf_lead_magnet_description": "Optional short pitch explaining what the learner gets after signing up.",
            "external_url": "Optional link to a related tool, official docs page, or hosted download.",
            "estimated_read_minutes": "Used on public cards to set expectations.",
            "seo_title": "Recommended before publishing; aim for 30–60 characters.",
            "seo_description": "Recommended before publishing; aim for 120–160 characters.",
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


class QuizQuestionForm(StyledModelForm):
    class Meta:
        model = QuizQuestion
        fields = ("position", "question_type", "prompt", "explanation", "is_active")
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 4}),
            "explanation": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "position": "Controls where this question appears in the lesson quiz section.",
            "prompt": "Keep the question short and focused on one skill.",
            "explanation": "Show this after the learner answers so the quiz teaches, not just scores.",
        }


class QuizChoiceForm(StyledModelForm):
    class Meta:
        model = QuizChoice
        fields = ("position", "text", "is_correct")
        help_texts = {
            "position": "Controls the answer order.",
            "is_correct": "Mark one or more correct answers. For beginner quizzes, one correct answer is usually best.",
        }


class CodeChallengeForm(StyledModelForm):
    class Meta:
        model = CodeChallenge
        fields = (
            "position",
            "title",
            "prompt",
            "starter_code",
            "solution_code",
            "expected_output",
            "hint_1",
            "hint_2",
            "validation_mode",
            "is_active",
        )
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 4}),
            "starter_code": forms.Textarea(attrs={"rows": 8, "class": "form-control code-input"}),
            "solution_code": forms.Textarea(attrs={"rows": 8, "class": "form-control code-input"}),
            "expected_output": forms.Textarea(attrs={"rows": 4, "class": "form-control code-input"}),
        }
        help_texts = {
            "position": "Controls where this challenge appears on the public lesson page.",
            "starter_code": "This becomes the editable starting code for the learner.",
            "solution_code": "Hidden behind a reveal section on the public page.",
            "expected_output": "Used by the browser playground for simple answer checking.",
            "validation_mode": "Exact match is strict; contains output is more forgiving; manual review is best for open-ended work.",
        }



class ChallengeTestCaseForm(StyledModelForm):
    class Meta:
        model = ChallengeTestCase
        fields = ("position", "name", "description", "test_code", "expected_output", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "test_code": forms.Textarea(attrs={"rows": 8, "class": "form-control code-input"}),
            "expected_output": forms.Textarea(attrs={"rows": 4, "class": "form-control code-input"}),
        }
        help_texts = {
            "position": "Controls where this test runs in the challenge test list.",
            "name": "Optional short label, such as add_numbers(2, 3).",
            "test_code": "Append code that proves the learner solution works. Use assertions or print expected values.",
            "expected_output": "Optional exact stdout expected for this test. Leave blank if using assertions only.",
        }


class ContentPlanForm(StyledModelForm):
    class Meta:
        model = ContentPlan
        fields = (
            "platform",
            "scheduled_at",
            "status",
            "carousel_template",
            "caption",
            "graphic",
            "post_goal",
            "notes",
        )
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "scheduled_at": "When you plan to publish this post.",
            "carousel_template": "Optional. Use the same key shown in the Social Carousel panel, such as concept_explanation or spot_the_bug.",
            "caption": "Optional. Connect the planned post to a prepared caption draft.",
            "graphic": "Optional. Connect the planned post to a generated graphic asset.",
            "post_goal": "Example: drive lesson clicks, grow Facebook reach, or prompt beginners to try the challenge.",
        }

    def __init__(self, *args, lesson=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lesson is not None:
            self.fields["caption"].queryset = lesson.captions.order_by("platform", "-created_at")
            self.fields["graphic"].queryset = lesson.assets.order_by("output_format", "slide_number", "-created_at")
        self.fields["caption"].required = False
        self.fields["graphic"].required = False
        self.fields["carousel_template"].required = False



class PublishingRecordForm(StyledModelForm):
    class Meta:
        model = PublishingRecord
        fields = (
            "platform",
            "published_at",
            "post_url",
            "caption",
            "graphic",
            "caption_text",
            "notes",
            "impressions",
            "reach",
            "likes",
            "comments",
            "saves",
            "shares",
            "clicks",
            "new_followers",
            "follower_count_after",
        )
        widgets = {
            "published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "caption_text": forms.Textarea(attrs={"rows": 8}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "platform": "Where this content was published.",
            "post_url": "Paste the direct post, page, reel, thread, or archive URL when available.",
            "caption": "Optional. Connect this record to the draft caption that was used.",
            "graphic": "Optional. Connect this record to the generated graphic that was used.",
            "caption_text": "Final caption snapshot. Fill this in if the published copy differs from the draft.",
            "impressions": "How many times the content was shown.",
            "reach": "How many unique accounts saw the content.",
            "clicks": "Profile, link, or post clicks when available.",
            "new_followers": "Follower change attributed to this post. Negative values are allowed.",
            "follower_count_after": "Total follower count after this post, if known.",
        }

    def __init__(self, *args, lesson=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lesson is not None:
            self.fields["caption"].queryset = lesson.captions.order_by("platform", "-created_at")
            self.fields["graphic"].queryset = lesson.assets.order_by("output_format", "slide_number", "-created_at")
        self.fields["caption"].required = False
        self.fields["graphic"].required = False

    def clean(self):
        cleaned = super().clean()
        caption = cleaned.get("caption")
        caption_text = cleaned.get("caption_text")
        if caption and not caption_text:
            cleaned["caption_text"] = caption.content
        return cleaned


class NewsletterSignupForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = NewsletterSubscriber
        fields = ("email", "first_name")
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name, optional"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Unable to process this signup.")
        return cleaned


class SubscriberSegmentForm(StyledModelForm):
    class Meta:
        model = SubscriberSegment
        fields = (
            "name",
            "description",
            "is_active",
            "status_filter",
            "source_filter",
            "skill_level_filter",
            "source_lesson",
            "subscribed_after",
            "subscribed_before",
            "subscribed_within_days",
            "search_text",
            "external_provider",
            "external_segment_id",
            "external_audience_id",
            "provider_sync_status",
            "provider_last_synced_at",
            "provider_notes",
            "notes",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "provider_notes": forms.Textarea(attrs={"rows": 3}),
            "subscribed_after": forms.DateInput(attrs={"type": "date"}),
            "subscribed_before": forms.DateInput(attrs={"type": "date"}),
            "provider_last_synced_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        help_texts = {
            "name": "Example: Brand new learners from lesson pages, Recent playground signups, or Beginner profiles.",
            "status_filter": "Use Active for real email sends. Any status is mainly for analysis.",
            "source_filter": "Limit by where the subscriber signed up.",
            "skill_level_filter": "Uses the learner profile skill level when the subscriber has an account.",
            "source_lesson": "Limit to people who signed up from one specific lesson page.",
            "subscribed_within_days": "Optional rolling window, such as 30. Leave blank for all-time.",
            "search_text": "Optional keyword across email, first name, notes, and source lesson title.",
            "external_provider": "Set this when this saved segment maps to an email platform audience, tag, or segment.",
            "external_segment_id": "Provider segment, tag, saved filter, or group ID for future API syncs.",
            "external_audience_id": "Provider audience/list/publication ID that contains this segment.",
            "provider_sync_status": "Manual sync state until direct provider sync is added.",
        }

    def clean(self):
        cleaned = super().clean()
        after = cleaned.get("subscribed_after")
        before = cleaned.get("subscribed_before")
        if after and before and before < after:
            self.add_error("subscribed_before", "End date must be after the start date.")
        return cleaned


class NewsletterCampaignForm(StyledModelForm):
    class Meta:
        model = NewsletterCampaign
        fields = (
            "lesson",
            "title",
            "subject",
            "preview_text",
            "body",
            "call_to_action",
            "cta_url",
            "status",
            "target_segment",
            "saved_segment",
            "scheduled_at",
            "sent_at",
            "content_plan",
            "publishing_record",
            "estimated_recipients",
            "actual_recipients",
            "opens",
            "clicks",
            "unsubscribes",
            "bounces",
            "external_provider",
            "external_campaign_id",
            "external_audience_id",
            "provider_url",
            "provider_sync_status",
            "provider_last_synced_at",
            "provider_notes",
            "notes",
        )
        widgets = {
            "body": forms.Textarea(attrs={"rows": 14}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "provider_notes": forms.Textarea(attrs={"rows": 3}),
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "sent_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "provider_last_synced_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        help_texts = {
            "lesson": "Optional lesson this email promotes or explains.",
            "subject": "Keep this clear and beginner-friendly.",
            "preview_text": "Inbox preview text that appears after the subject line.",
            "body": "Draft email copy. This app plans and tracks campaigns; it does not send email automatically.",
            "target_segment": "Legacy quick segment. Prefer a saved segment when you want reusable targeting rules.",
            "saved_segment": "Optional saved audience segment. This lets campaign targeting and reporting stay consistent.",
            "content_plan": "Optional planned Email list content slot.",
            "publishing_record": "Optional performance record after the email is sent.",
            "estimated_recipients": "Projected send size before sending.",
            "actual_recipients": "Final delivered/send count from your email platform.",
            "external_provider": "Email platform this campaign is prepared for or connected to.",
            "external_campaign_id": "Provider campaign ID once copied from Mailchimp, Beehiiv, ConvertKit, or another service.",
            "external_audience_id": "Provider audience/list/publication ID used for this send.",
            "provider_url": "Direct provider dashboard URL for quick review.",
            "provider_sync_status": "Manual sync state until API sync is added.",
        }

    def __init__(self, *args, lesson=None, **kwargs):
        super().__init__(*args, **kwargs)
        if lesson is not None:
            self.fields["lesson"].initial = lesson
            self.fields["lesson"].queryset = Lesson.objects.filter(pk=lesson.pk)
            self.fields["content_plan"].queryset = lesson.content_plans.filter(platform=ContentPlan.Platform.EMAIL).order_by("-scheduled_at")
            self.fields["publishing_record"].queryset = lesson.publishing_records.filter(platform=PublishingRecord.Platform.EMAIL).order_by("-published_at")
        else:
            self.fields["lesson"].queryset = Lesson.objects.order_by("title")
            self.fields["content_plan"].queryset = ContentPlan.objects.filter(platform=ContentPlan.Platform.EMAIL).select_related("lesson").order_by("-scheduled_at")
            self.fields["publishing_record"].queryset = PublishingRecord.objects.filter(platform=PublishingRecord.Platform.EMAIL).select_related("lesson").order_by("-published_at")
        self.fields["saved_segment"].queryset = SubscriberSegment.objects.filter(is_active=True).order_by("name")
        self.fields["lesson"].required = False
        self.fields["content_plan"].required = False
        self.fields["publishing_record"].required = False
        self.fields["saved_segment"].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        scheduled_at = cleaned.get("scheduled_at")
        sent_at = cleaned.get("sent_at")
        if status == NewsletterCampaign.Status.SCHEDULED and not scheduled_at:
            self.add_error("scheduled_at", "Scheduled campaigns need a scheduled date and time.")
        if status == NewsletterCampaign.Status.SENT and not sent_at:
            cleaned["sent_at"] = timezone.now()
        return cleaned


class NewsletterMetricImportForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=NewsletterCampaign.objects.none(),
        help_text="Choose the campaign that should receive these metrics.",
    )
    provider = forms.ChoiceField(
        choices=NewsletterMetricImport.Provider.choices,
        initial=NewsletterMetricImport.Provider.MANUAL,
        help_text="This only labels the import source; parsing uses common metric names across platforms.",
    )
    pasted_metrics = forms.CharField(
        required=False,
        label="Paste metrics",
        widget=forms.Textarea(attrs={"rows": 9, "placeholder": "recipients,opens,clicks,unsubscribes,bounces\n421,212,38,1,0"}),
        help_text="Paste a CSV row or key-value lines copied from your email platform.",
    )
    metrics_file = forms.FileField(
        required=False,
        label="Upload CSV",
        help_text="Optional CSV export from Mailchimp, Beehiiv, ConvertKit, or another email platform.",
    )
    mark_sent = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Mark the campaign as sent if imported metrics are applied.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Optional note about where the metrics came from.",
    )

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = NewsletterCampaign.objects.select_related("lesson").order_by("-scheduled_at", "-created_at")
        if campaign is not None:
            queryset = NewsletterCampaign.objects.filter(pk=campaign.pk)
            self.fields["campaign"].initial = campaign
        self.fields["campaign"].queryset = queryset
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault("class", "form-control")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_metrics_file(self):
        upload = self.cleaned_data.get("metrics_file")
        if upload and upload.size > 1024 * 1024:
            raise forms.ValidationError("Upload a CSV smaller than 1 MB.")
        return upload

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("pasted_metrics") and not cleaned.get("metrics_file"):
            raise forms.ValidationError("Paste metrics or upload a CSV file.")
        return cleaned

    def source_text(self):
        pasted = (self.cleaned_data.get("pasted_metrics") or "").strip()
        upload = self.cleaned_data.get("metrics_file")
        if upload:
            raw = upload.read()
            for encoding in ("utf-8-sig", "utf-8", "latin-1"):
                try:
                    decoded = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    decoded = ""
            return decoded.strip()
        return pasted


class NewsletterSubscriberForm(StyledModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = (
            "email",
            "first_name",
            "status",
            "source",
            "source_lesson",
            "source_resource",
            "source_url",
            "consent_text",
            "external_provider",
            "external_contact_id",
            "external_list_id",
            "provider_sync_status",
            "provider_last_synced_at",
            "provider_notes",
            "notes",
        )
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "consent_text": forms.Textarea(attrs={"rows": 2}),
            "provider_notes": forms.Textarea(attrs={"rows": 3}),
            "provider_last_synced_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        help_texts = {
            "email": "Subscriber email address. Keep this unique.",
            "status": "Use Unsubscribed for people who opt out.",
            "source": "Where this subscriber came from.",
            "source_lesson": "Optional lesson that created the signup.",
            "source_resource": "Optional resource or PDF lead magnet that created the signup.",
            "source_url": "Optional page URL or campaign source.",
            "external_provider": "Email platform where this contact exists.",
            "external_contact_id": "Provider contact/subscriber ID for future automated syncs.",
            "external_list_id": "Provider audience, list, publication, or form ID.",
            "provider_sync_status": "Manual sync state until direct provider sync is added.",
            "provider_last_synced_at": "When this subscriber was last checked or updated in the provider.",
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
