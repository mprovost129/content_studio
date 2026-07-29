from datetime import timedelta
from decimal import Decimal
import json

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Enter a six-digit hex color such as #3776AB.",
)

class EmailProvider(models.TextChoices):
    NONE = "none", "Not connected"
    MAILCHIMP = "mailchimp", "Mailchimp"
    BEEHIIV = "beehiiv", "Beehiiv"
    CONVERTKIT = "convertkit", "ConvertKit"
    OTHER = "other", "Other"


class ProviderSyncStatus(models.TextChoices):
    NOT_CONNECTED = "not_connected", "Not connected"
    READY = "ready", "Ready to sync"
    SYNCED = "synced", "Synced"
    NEEDS_REVIEW = "needs_review", "Needs review"
    ERROR = "error", "Error"

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BrandProfile(TimestampedModel):
    name = models.CharField(max_length=120, default="Code with Michael")
    social_handle = models.CharField(max_length=80, default="@code_with_michael")
    default_accent = models.CharField(
        max_length=7, default="#3776AB", validators=[hex_color_validator]
    )
    background_color = models.CharField(
        max_length=7, default="#0A0C16", validators=[hex_color_validator]
    )
    default_call_to_action = models.CharField(
        max_length=180, default="Save this post and follow for more Python lessons."
    )
    logo = models.ImageField(upload_to="branding/", blank=True)

    class Meta:
        verbose_name = "brand profile"

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile


class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    accent_color = models.CharField(
        max_length=7, default="#3776AB", validators=[hex_color_validator]
    )

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimestampedModel):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Series(TimestampedModel):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=190, unique=True, blank=True)
    description = models.TextField(blank=True)
    total_lessons = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)
        verbose_name_plural = "series"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(TimestampedModel):
    class Status(models.TextChoices):
        IDEA = "idea", "Idea"
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        READY = "ready", "Ready"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        MIXED = "mixed", "Mixed"

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="lessons")
    series = models.ForeignKey(
        Series, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    series_position = models.PositiveSmallIntegerField(null=True, blank=True)
    accent_color = models.CharField(
        max_length=7, blank=True, validators=[hex_color_validator]
    )
    call_to_action = models.CharField(max_length=220, blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    learning_objective = models.CharField(
        max_length=240,
        blank=True,
        help_text="One clear outcome the beginner should reach by the end of the lesson.",
    )
    beginner_takeaway = models.CharField(
        max_length=240,
        blank=True,
        help_text="The plain-English idea the learner should remember after finishing.",
    )
    common_mistake = models.TextField(
        blank=True,
        help_text="A likely beginner error to call out in the lesson, caption, or carousel.",
    )
    practice_prompt = models.TextField(
        blank=True,
        help_text="A short learner task that can become a challenge block or social post.",
    )
    starter_code = models.TextField(
        blank=True,
        help_text="Optional code the learner starts from in the playground or challenge.",
    )
    solution_code = models.TextField(
        blank=True,
        help_text="Optional reviewed solution code. Keep this hidden from the first learner view.",
    )
    expected_output = models.TextField(
        blank=True,
        help_text="Optional output used for manual review or simple code-checking later.",
    )
    hint_1 = models.CharField(max_length=240, blank=True)
    hint_2 = models.CharField(max_length=240, blank=True)
    next_lesson = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_lessons",
        help_text="Optional lesson to recommend after this one.",
    )
    facebook_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    instagram_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    threads_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    website_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDEA, db_index=True
    )
    enable_playground = models.BooleanField(
        default=False,
        help_text="Allow code blocks to run in the browser-based Python playground.",
    )
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons_updated",
    )

    class Meta:
        ordering = ("-updated_at",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:210] or "lesson"
            candidate = base
            suffix = 2
            while Lesson.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("studio:lesson-detail", kwargs={"slug": self.slug})

    @property
    def resolved_accent_color(self):
        if self.accent_color:
            return self.accent_color
        if self.category_id:
            return self.category.accent_color
        return BrandProfile.get_default().default_accent

    @property
    def quality_diagnostics(self):
        checks = [
            ("summary", "Summary", bool(self.summary)),
            ("objective", "Learning objective", bool(self.learning_objective)),
            ("takeaway", "Beginner takeaway", bool(self.beginner_takeaway)),
            ("content", "Content blocks", self.blocks.exists() if self.pk else False),
            ("code", "Code example", self.blocks.filter(block_type=LessonBlock.BlockType.CODE).exists() if self.pk else False),
            ("output", "Expected output", bool(self.expected_output) or (self.blocks.filter(block_type=LessonBlock.BlockType.OUTPUT).exists() if self.pk else False)),
            ("practice", "Practice prompt or challenge", bool(self.practice_prompt) or (self.blocks.filter(block_type=LessonBlock.BlockType.CHALLENGE).exists() if self.pk else False) or (self.code_challenges.exists() if self.pk else False)),
            ("quiz", "Structured quiz", self.quiz_questions.exists() if self.pk else False),
            ("mistake", "Common mistake", bool(self.common_mistake)),
            ("seo", "SEO metadata", bool(self.seo_title and self.seo_description)),
        ]
        complete = sum(1 for _, _, passed in checks if passed)
        return {
            "score": round(complete / len(checks) * 100),
            "complete": complete,
            "total": len(checks),
            "checks": [
                {"key": key, "label": label, "complete": passed}
                for key, label, passed in checks
            ],
        }

    def __str__(self):
        return self.title


class LessonBlock(TimestampedModel):
    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        TEXT = "text", "Explanation"
        CODE = "code", "Code"
        OUTPUT = "output", "Output"
        CALLOUT = "callout", "Callout / tip"
        LIST = "list", "List"
        IMAGE = "image", "Image"
        QUIZ = "quiz", "Quiz"
        CHALLENGE = "challenge", "Challenge"
        COMPARISON = "comparison", "Comparison"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="blocks")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    block_type = models.CharField(max_length=20, choices=BlockType.choices)
    title = models.CharField(max_length=180, blank=True)
    content = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "position"), name="unique_lesson_block_position"
            )
        ]

    def __str__(self):
        return f"{self.lesson}: {self.get_block_type_display()} {self.position}"


class QuizQuestion(TimestampedModel):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        TRUE_FALSE = "true_false", "True / false"
        SHORT_ANSWER = "short_answer", "Short answer"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quiz_questions")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    question_type = models.CharField(
        max_length=30, choices=QuestionType.choices, default=QuestionType.MULTIPLE_CHOICE
    )
    prompt = models.TextField(help_text="Ask one clear beginner-friendly question.")
    explanation = models.TextField(
        blank=True, help_text="Explain why the correct answer is correct in plain English."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "position"), name="unique_lesson_quiz_position"
            )
        ]

    @property
    def correct_choices(self):
        return self.choices.filter(is_correct=True)

    def __str__(self):
        return f"{self.lesson}: Question {self.position}"


class QuizChoice(TimestampedModel):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="choices")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("question", "position"), name="unique_quiz_choice_position"
            )
        ]

    def __str__(self):
        marker = "correct" if self.is_correct else "choice"
        return f"{self.question} - {marker} {self.position}"


class CodeChallenge(TimestampedModel):
    class ValidationMode(models.TextChoices):
        EXACT_OUTPUT = "exact_output", "Exact output match"
        CONTAINS_OUTPUT = "contains_output", "Output contains text"
        MANUAL = "manual", "Manual review"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="code_challenges")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    title = models.CharField(max_length=180)
    prompt = models.TextField(help_text="Describe the task the beginner should complete.")
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    hint_1 = models.CharField(max_length=240, blank=True)
    hint_2 = models.CharField(max_length=240, blank=True)
    validation_mode = models.CharField(
        max_length=30, choices=ValidationMode.choices, default=ValidationMode.EXACT_OUTPUT
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "position"), name="unique_lesson_challenge_position"
            )
        ]

    def __str__(self):
        return f"{self.lesson}: Challenge {self.position} - {self.title}"

    @property
    def active_test_cases_json(self):
        payload = [
            {
                "id": test_case.pk,
                "name": test_case.name,
                "description": test_case.description,
                "test_code": test_case.test_code,
                "expected_output": test_case.expected_output,
            }
            for test_case in self.test_cases.filter(is_active=True)
        ]
        return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


class ChallengeTestCase(TimestampedModel):
    challenge = models.ForeignKey(CodeChallenge, on_delete=models.CASCADE, related_name="test_cases")
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    name = models.CharField(max_length=140, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Plain-English explanation of what this test checks.",
    )
    test_code = models.TextField(
        help_text=(
            "Python code appended after the learner's submitted code. "
            "Use print(...) or assertions to check function return values."
        )
    )
    expected_output = models.TextField(
        blank=True,
        help_text="Optional stdout expected from this individual test case.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("challenge", "position"), name="unique_challenge_test_position"
            )
        ]

    def __str__(self):
        label = self.name or f"Test {self.position}"
        return f"{self.challenge}: {label}"


class ChallengeAttempt(TimestampedModel):
    challenge = models.ForeignKey(CodeChallenge, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenge_attempts",
    )
    session_key = models.CharField(max_length=80, blank=True, db_index=True)
    submitted_code = models.TextField()
    observed_output = models.TextField(blank=True)
    test_results = models.JSONField(default=dict, blank=True)
    tests_passed = models.PositiveSmallIntegerField(default=0)
    tests_total = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        result = "passed" if self.passed else "needs review"
        return f"{self.challenge} - {result}"


class LessonProgress(TimestampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    quiz_correct = models.PositiveSmallIntegerField(default=0)
    quiz_total = models.PositiveSmallIntegerField(default=0)
    challenges_passed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("-last_activity_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "lesson"), name="unique_user_lesson_progress")
        ]

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = self.completed_at or timezone.now()
        self.last_activity_at = timezone.now()

    @property
    def percent_complete(self):
        if self.status == self.Status.COMPLETED:
            return 100
        total_items = max(1, self.quiz_total + self.lesson.code_challenges.filter(is_active=True).count())
        completed_items = self.quiz_correct + self.challenges_passed
        return min(95, round(completed_items / total_items * 100))

    def __str__(self):
        return f"{self.user} - {self.lesson} - {self.get_status_display()}"


class QuizAttempt(TimestampedModel):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    selected_choice = models.ForeignKey(
        QuizChoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts"
    )
    response_text = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        result = "correct" if self.is_correct else "incorrect"
        return f"{self.user} - {self.question} - {result}"


class LearnerBadge(TimestampedModel):
    class CriteriaType(models.TextChoices):
        LESSONS_COMPLETED = "lessons_completed", "Lessons completed"
        QUIZZES_CORRECT = "quizzes_correct", "Correct quiz answers"
        CHALLENGES_PASSED = "challenges_passed", "Challenges passed"

    key = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    criteria_type = models.CharField(max_length=40, choices=CriteriaType.choices)
    threshold = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("criteria_type", "threshold", "title")

    def __str__(self):
        return self.title


class LearnerBadgeAward(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badge_awards"
    )
    badge = models.ForeignKey(LearnerBadge, on_delete=models.CASCADE, related_name="awards")
    awarded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-awarded_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "badge"), name="unique_user_badge_award")
        ]

    def __str__(self):
        return f"{self.user} earned {self.badge}"


class GraphicTemplate(TimestampedModel):
    class TemplateType(models.TextChoices):
        LESSON = "lesson", "Lesson explainer"
        PROJECT = "project", "Project series"
        CHALLENGE = "challenge", "Challenge / quiz"
        ANSWER = "answer", "Answer"
        SPOT_BUG = "spot_bug", "Spot the bug"
        MINI_PROGRAM = "mini_program", "Mini program"
        COMPARISON = "comparison", "Comparison / cheat sheet"
        ERROR = "error", "Errors / common mistakes"
        COMMUNITY = "community", "Community / celebration"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, unique=True)
    template_type = models.CharField(max_length=30, choices=TemplateType.choices)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class GraphicAsset(TimestampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    class Format(models.TextChoices):
        INSTAGRAM_SQUARE = "instagram_square", "Instagram / Facebook square"
        INSTAGRAM_PORTRAIT = "instagram_portrait", "Instagram / Threads portrait"
        STORY = "story", "Instagram / Facebook story"
        FACEBOOK_LANDSCAPE = "facebook_landscape", "Facebook landscape"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assets")
    template = models.ForeignKey(
        GraphicTemplate, on_delete=models.PROTECT, related_name="assets"
    )
    output_format = models.CharField(max_length=30, choices=Format.choices)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    slide_number = models.PositiveSmallIntegerField(default=1)
    file = models.ImageField(upload_to="generated/%Y/%m/", blank=True)
    alt_text = models.CharField(max_length=300, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("output_format", "slide_number", "created_at")

    def __str__(self):
        return f"{self.lesson} - {self.get_output_format_display()} #{self.slide_number}"


class AIModelPricing(TimestampedModel):
    model = models.CharField(max_length=80)
    effective_from = models.DateField(default=timezone.localdate)
    input_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    cached_input_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    output_per_million = models.DecimalField(max_digits=10, decimal_places=4)
    cache_write_multiplier = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal("1.250")
    )
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-effective_from", "model")
        constraints = [
            models.UniqueConstraint(
                fields=("model", "effective_from"), name="unique_model_price_date"
            )
        ]

    def __str__(self):
        return f"{self.model} pricing from {self.effective_from}"


class AIGeneration(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Purpose(models.TextChoices):
        CAPTION = "caption", "Caption"
        LESSON_DRAFT = "lesson_draft", "Lesson draft"
        IMPROVEMENT = "improvement", "Lesson improvement"
        QUIZ = "quiz", "Quiz"
        CHALLENGE = "challenge", "Challenge"

    lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_generations"
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    model = models.CharField(max_length=80)
    reasoning_effort = models.CharField(max_length=20, blank=True)
    response_id = models.CharField(max_length=120, blank=True, db_index=True)
    instructions = models.TextField(blank=True)
    prompt = models.TextField()
    response_text = models.TextField(blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    cached_input_tokens = models.PositiveIntegerField(default=0)
    cache_write_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    reasoning_tokens = models.PositiveIntegerField(default=0)
    input_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    cached_input_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    output_price_per_million = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    cache_write_multiplier = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal("1.250")
    )
    estimated_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def calculate_estimated_cost(self):
        million = Decimal("1000000")
        uncached = max(self.input_tokens - self.cached_input_tokens - self.cache_write_tokens, 0)
        regular_cost = Decimal(uncached) * self.input_price_per_million / million
        cached_cost = (
            Decimal(self.cached_input_tokens) * self.cached_input_price_per_million / million
        )
        cache_write_cost = (
            Decimal(self.cache_write_tokens)
            * self.input_price_per_million
            * self.cache_write_multiplier
            / million
        )
        output_cost = Decimal(self.output_tokens) * self.output_price_per_million / million
        return (regular_cost + cached_cost + cache_write_cost + output_cost).quantize(
            Decimal("0.000001")
        )

    def __str__(self):
        return f"{self.get_purpose_display()} via {self.model} ({self.status})"


class CaptionDraft(TimestampedModel):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        THREADS = "threads", "Threads"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        ARCHIVED = "archived", "Archived"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="captions")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    content = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    generation = models.ForeignKey(
        AIGeneration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="caption_drafts",
    )

    class Meta:
        ordering = ("platform", "-created_at")

    def __str__(self):
        return f"{self.lesson} - {self.get_platform_display()} caption"


class ContentPlan(TimestampedModel):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        THREADS = "threads", "Threads"
        WEBSITE = "website", "Website"
        EMAIL = "email", "Email list"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        IDEA = "idea", "Idea"
        PLANNED = "planned", "Planned"
        DRAFTED = "drafted", "Drafted"
        READY = "ready", "Ready"
        SCHEDULED = "scheduled", "Scheduled"
        POSTED = "posted", "Posted"
        SKIPPED = "skipped", "Skipped"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="content_plans")
    platform = models.CharField(max_length=20, choices=Platform.choices, db_index=True)
    scheduled_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED, db_index=True
    )
    carousel_template = models.CharField(
        max_length=80,
        blank=True,
        help_text="Optional social carousel format, such as beginner_mistake or spot_the_bug.",
    )
    caption = models.ForeignKey(
        CaptionDraft,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_plans",
    )
    graphic = models.ForeignKey(
        GraphicAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_plans",
    )
    post_goal = models.CharField(
        max_length=180,
        blank=True,
        help_text="What this post should accomplish, such as reach beginners, drive website clicks, or promote a challenge.",
    )
    notes = models.TextField(blank=True)
    publishing_record = models.OneToOneField(
        "PublishingRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_plan",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_plans_created",
    )

    class Meta:
        ordering = ("scheduled_at", "platform", "lesson__title")
        indexes = [
            models.Index(fields=("scheduled_at", "platform")),
            models.Index(fields=("status", "scheduled_at")),
            models.Index(fields=("lesson", "platform")),
        ]

    @property
    def week_start(self):
        local_date = timezone.localtime(self.scheduled_at).date()
        return local_date - timedelta(days=local_date.weekday())

    def mark_posted(self, publishing_record):
        self.publishing_record = publishing_record
        self.status = self.Status.POSTED
        self.save(update_fields=["publishing_record", "status", "updated_at"])

    def __str__(self):
        return f"{self.lesson} - {self.get_platform_display()} planned for {self.scheduled_at:%Y-%m-%d %H:%M}"


class PublishingRecord(TimestampedModel):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        THREADS = "threads", "Threads"
        WEBSITE = "website", "Website"
        EMAIL = "email", "Email list"
        OTHER = "other", "Other"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="publishing_records")
    platform = models.CharField(max_length=20, choices=Platform.choices, db_index=True)
    published_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this content was posted or published.",
    )
    post_url = models.URLField(blank=True, help_text="Direct URL to the published post, page, or email archive.")
    caption = models.ForeignKey(
        CaptionDraft,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publishing_records",
    )
    graphic = models.ForeignKey(
        GraphicAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publishing_records",
    )
    caption_text = models.TextField(
        blank=True,
        help_text="Snapshot of the final caption used. This stays intact even if the caption draft changes later.",
    )
    notes = models.TextField(blank=True)
    impressions = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    new_followers = models.IntegerField(default=0)
    follower_count_after = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publishing_records_created",
    )

    class Meta:
        ordering = ("-published_at", "-created_at")
        indexes = [
            models.Index(fields=("platform", "published_at")),
            models.Index(fields=("lesson", "platform")),
        ]

    @property
    def engagement_total(self):
        return self.likes + self.comments + self.saves + self.shares + self.clicks

    @property
    def engagement_rate(self):
        denominator = self.reach or self.impressions
        if not denominator:
            return None
        return round(self.engagement_total / denominator * 100, 2)

    def save(self, *args, **kwargs):
        if self.caption and not self.caption_text:
            self.caption_text = self.caption.content
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lesson} - {self.get_platform_display()} on {self.published_at:%Y-%m-%d}"


class NewsletterCampaign(TimestampedModel):
    class Status(models.TextChoices):
        IDEA = "idea", "Idea"
        DRAFT = "draft", "Draft"
        READY = "ready", "Ready"
        SCHEDULED = "scheduled", "Scheduled"
        SENT = "sent", "Sent"
        ARCHIVED = "archived", "Archived"

    class Segment(models.TextChoices):
        ALL_ACTIVE = "all_active", "All active subscribers"
        BEGINNER = "beginner", "Beginner learners"
        INTERMEDIATE = "intermediate", "Intermediate learners"
        ADVANCED = "advanced", "Advanced learners"
        MANUAL = "manual", "Manual segment"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_campaigns",
        help_text="Optional lesson this email promotes or teaches from.",
    )
    title = models.CharField(max_length=180)
    subject = models.CharField(max_length=180)
    preview_text = models.CharField(max_length=220, blank=True)
    body = models.TextField(help_text="Draft email body. Review before sending in your email platform.")
    call_to_action = models.CharField(max_length=180, blank=True)
    cta_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    target_segment = models.CharField(
        max_length=30, choices=Segment.choices, default=Segment.ALL_ACTIVE, db_index=True
    )
    saved_segment = models.ForeignKey(
        "SubscriberSegment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        help_text="Optional saved subscriber segment. Use this for repeatable campaign targeting rules.",
    )
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
    content_plan = models.OneToOneField(
        ContentPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_campaign",
        help_text="Optional planned email slot connected to this campaign.",
    )
    publishing_record = models.OneToOneField(
        PublishingRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_campaign",
        help_text="Optional sent email performance record.",
    )
    estimated_recipients = models.PositiveIntegerField(default=0)
    actual_recipients = models.PositiveIntegerField(default=0)
    opens = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    unsubscribes = models.PositiveIntegerField(default=0)
    bounces = models.PositiveIntegerField(default=0)
    external_provider = models.CharField(
        max_length=30,
        choices=EmailProvider.choices,
        default=EmailProvider.NONE,
        db_index=True,
        help_text="Email service provider this campaign is prepared to sync with.",
    )
    external_campaign_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Campaign ID from Mailchimp, Beehiiv, ConvertKit, or another provider.",
    )
    external_audience_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Audience, list, publication, or form ID used by the email provider.",
    )
    provider_url = models.URLField(
        blank=True,
        help_text="Optional provider dashboard URL for this campaign.",
    )
    provider_sync_status = models.CharField(
        max_length=30,
        choices=ProviderSyncStatus.choices,
        default=ProviderSyncStatus.NOT_CONNECTED,
        db_index=True,
    )
    provider_last_synced_at = models.DateTimeField(null=True, blank=True)
    provider_notes = models.TextField(
        blank=True,
        help_text="Private notes about provider setup, sync issues, field mapping, or manual actions.",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_campaigns_created",
    )

    class Meta:
        ordering = ("-scheduled_at", "-created_at")
        indexes = [
            models.Index(fields=("status", "scheduled_at")),
            models.Index(fields=("target_segment", "scheduled_at")),
            models.Index(fields=("external_provider", "provider_sync_status")),
        ]

    @property
    def open_rate(self):
        if not self.actual_recipients:
            return None
        return round(self.opens / self.actual_recipients * 100, 2)

    @property
    def click_rate(self):
        if not self.actual_recipients:
            return None
        return round(self.clicks / self.actual_recipients * 100, 2)

    @property
    def click_to_open_rate(self):
        if not self.opens:
            return None
        return round(self.clicks / self.opens * 100, 2)

    def mark_sent(self, when=None):
        self.status = self.Status.SENT
        self.sent_at = when or timezone.now()

    @property
    def audience_label(self):
        if self.saved_segment_id:
            return self.saved_segment.name
        return self.get_target_segment_display()

    @property
    def estimated_segment_count(self):
        if self.saved_segment_id:
            return self.saved_segment.subscriber_count
        if self.target_segment == self.Segment.ALL_ACTIVE:
            return NewsletterSubscriber.objects.filter(status=NewsletterSubscriber.Status.ACTIVE).count()
        skill_map = {
            self.Segment.BEGINNER: ["new", "beginner"],
            self.Segment.INTERMEDIATE: ["returning", "intermediate"],
            self.Segment.ADVANCED: ["intermediate"],
        }
        levels = skill_map.get(self.target_segment)
        if levels:
            return NewsletterSubscriber.objects.filter(status=NewsletterSubscriber.Status.ACTIVE, user__skill_level__in=levels).count()
        return self.estimated_recipients

    def __str__(self):
        return self.title


class NewsletterMetricImport(TimestampedModel):
    class Provider(models.TextChoices):
        MAILCHIMP = "mailchimp", "Mailchimp"
        BEEHIIV = "beehiiv", "Beehiiv"
        CONVERTKIT = "convertkit", "ConvertKit"
        MANUAL = "manual", "Manual / pasted"
        OTHER = "other", "Other"

    campaign = models.ForeignKey(
        NewsletterCampaign,
        on_delete=models.CASCADE,
        related_name="metric_imports",
    )
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.MANUAL)
    source_filename = models.CharField(max_length=220, blank=True)
    raw_payload = models.TextField(blank=True)
    normalized_data = models.JSONField(default=dict, blank=True)
    actual_recipients = models.PositiveIntegerField(default=0)
    opens = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    unsubscribes = models.PositiveIntegerField(default=0)
    bounces = models.PositiveIntegerField(default=0)
    warnings = models.JSONField(default=list, blank=True)
    applied_at = models.DateTimeField(default=timezone.now)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_metric_imports",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-applied_at", "-created_at")
        indexes = [
            models.Index(fields=("campaign", "applied_at")),
            models.Index(fields=("provider", "applied_at")),
        ]

    def apply_to_campaign(self, mark_sent=False):
        fields = ["actual_recipients", "opens", "clicks", "unsubscribes", "bounces", "updated_at"]
        self.campaign.actual_recipients = self.actual_recipients
        self.campaign.opens = self.opens
        self.campaign.clicks = self.clicks
        self.campaign.unsubscribes = self.unsubscribes
        self.campaign.bounces = self.bounces
        if mark_sent and self.campaign.status != NewsletterCampaign.Status.SENT:
            self.campaign.mark_sent()
            fields.extend(["status", "sent_at"])
        self.campaign.save(update_fields=fields)

    def __str__(self):
        return f"{self.campaign} metrics import on {self.applied_at:%Y-%m-%d}"


class NewsletterSubscriber(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
        BOUNCED = "bounced", "Bounced"

    class Source(models.TextChoices):
        LEARN_HOME = "learn_home", "Learn homepage"
        LESSON = "lesson", "Lesson page"
        RESOURCE = "resource", "Resource download"
        PLAYGROUND = "playground", "Playground"
        IMPORT = "import", "Imported"
        STUDIO = "studio", "Studio"
        OTHER = "other", "Other"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    source = models.CharField(
        max_length=30, choices=Source.choices, default=Source.LEARN_HOME, db_index=True
    )
    source_url = models.CharField(max_length=300, blank=True)
    source_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_subscribers",
    )
    source_resource = models.ForeignKey(
        "LearningResource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_subscribers",
        help_text="Resource that captured this subscriber, especially PDF lead magnets.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_subscriptions",
    )
    consent_text = models.CharField(
        max_length=240,
        default="Send me beginner Python lessons, practice prompts, and Code with Michael updates.",
    )
    subscribed_at = models.DateTimeField(default=timezone.now, db_index=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    external_provider = models.CharField(
        max_length=30,
        choices=EmailProvider.choices,
        default=EmailProvider.NONE,
        db_index=True,
        help_text="Email service provider where this contact lives.",
    )
    external_contact_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Contact/subscriber ID from the email provider.",
    )
    external_list_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Provider list, audience, publication, or form ID for this subscriber.",
    )
    provider_sync_status = models.CharField(
        max_length=30,
        choices=ProviderSyncStatus.choices,
        default=ProviderSyncStatus.NOT_CONNECTED,
        db_index=True,
    )
    provider_last_synced_at = models.DateTimeField(null=True, blank=True)
    provider_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-subscribed_at", "email")
        indexes = [
            models.Index(fields=("status", "subscribed_at")),
            models.Index(fields=("source", "subscribed_at")),
            models.Index(fields=("external_provider", "provider_sync_status")),
        ]

    def mark_active(self):
        self.status = self.Status.ACTIVE
        self.unsubscribed_at = None
        self.subscribed_at = timezone.now()

    def mark_unsubscribed(self):
        self.status = self.Status.UNSUBSCRIBED
        self.unsubscribed_at = timezone.now()

    def __str__(self):
        return self.email


class SubscriberSegment(TimestampedModel):
    class StatusFilter(models.TextChoices):
        ANY = "any", "Any status"
        ACTIVE = "active", "Active"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
        BOUNCED = "bounced", "Bounced"

    class SkillLevelFilter(models.TextChoices):
        ANY = "any", "Any skill level"
        NEW = "new", "Brand new"
        BEGINNER = "beginner", "Beginner"
        RETURNING = "returning", "Returning learner"
        INTERMEDIATE = "intermediate", "Intermediate"

    name = models.CharField(max_length=140, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    status_filter = models.CharField(
        max_length=20,
        choices=StatusFilter.choices,
        default=StatusFilter.ACTIVE,
        blank=True,
        help_text="Subscriber status to include. Active is safest for campaigns.",
    )
    source_filter = models.CharField(
        max_length=30,
        choices=[("any", "Any source")] + list(NewsletterSubscriber.Source.choices),
        default="any",
        blank=True,
        help_text="Limit the segment to subscribers from a specific signup source.",
    )
    skill_level_filter = models.CharField(
        max_length=20,
        choices=SkillLevelFilter.choices,
        default=SkillLevelFilter.ANY,
        blank=True,
        help_text="Limit the segment to learners with this profile skill level.",
    )
    source_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriber_segments",
        help_text="Optional lesson that captured the subscriber.",
    )
    subscribed_after = models.DateField(null=True, blank=True)
    subscribed_before = models.DateField(null=True, blank=True)
    subscribed_within_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Optional rolling recency window, such as 30 for subscribers from the last month.",
    )
    search_text = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional keyword match across email, first name, notes, and source lesson title.",
    )
    notes = models.TextField(blank=True)
    external_provider = models.CharField(
        max_length=30,
        choices=EmailProvider.choices,
        default=EmailProvider.NONE,
        db_index=True,
        help_text="Email provider this saved segment is intended to map to.",
    )
    external_segment_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Segment, tag, audience, or saved filter ID from the provider.",
    )
    external_audience_id = models.CharField(
        max_length=160,
        blank=True,
        help_text="Provider audience/list/publication ID that contains this segment.",
    )
    provider_sync_status = models.CharField(
        max_length=30,
        choices=ProviderSyncStatus.choices,
        default=ProviderSyncStatus.NOT_CONNECTED,
        db_index=True,
    )
    provider_last_synced_at = models.DateTimeField(null=True, blank=True)
    provider_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriber_segments_created",
    )

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=("is_active", "status_filter")),
            models.Index(fields=("source_filter", "skill_level_filter")),
            models.Index(fields=("external_provider", "provider_sync_status")),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:135] or "segment"
            candidate = base
            suffix = 2
            while SubscriberSegment.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def matching_subscribers(self):
        queryset = NewsletterSubscriber.objects.select_related("user", "source_lesson")
        if self.status_filter and self.status_filter != self.StatusFilter.ANY:
            queryset = queryset.filter(status=self.status_filter)
        if self.source_filter and self.source_filter != "any":
            queryset = queryset.filter(source=self.source_filter)
        if self.skill_level_filter and self.skill_level_filter != self.SkillLevelFilter.ANY:
            queryset = queryset.filter(user__skill_level=self.skill_level_filter)
        if self.source_lesson_id:
            queryset = queryset.filter(source_lesson=self.source_lesson)
        if self.subscribed_after:
            queryset = queryset.filter(subscribed_at__date__gte=self.subscribed_after)
        if self.subscribed_before:
            queryset = queryset.filter(subscribed_at__date__lte=self.subscribed_before)
        if self.subscribed_within_days:
            cutoff = timezone.now() - timedelta(days=self.subscribed_within_days)
            queryset = queryset.filter(subscribed_at__gte=cutoff)
        if self.search_text:
            queryset = queryset.filter(
                Q(email__icontains=self.search_text)
                | Q(first_name__icontains=self.search_text)
                | Q(notes__icontains=self.search_text)
                | Q(source_lesson__title__icontains=self.search_text)
            )
        return queryset.order_by("email")

    @property
    def subscriber_count(self):
        if not self.pk:
            return 0
        return self.matching_subscribers().count()

    def __str__(self):
        return self.name


class LearningResource(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        READY = "ready", "Ready"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class ResourceType(models.TextChoices):
        CHEAT_SHEET = "cheat_sheet", "Cheat sheet"
        COMMON_ERROR = "common_error", "Common Python error"
        SETUP_GUIDE = "setup_guide", "Setup guide"
        PRACTICE_REFERENCE = "practice_reference", "Practice reference"
        GLOSSARY = "glossary", "Python vocabulary"
        DOWNLOAD = "download", "Downloadable reference"

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=230, unique=True, blank=True)
    summary = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=30, choices=ResourceType.choices, default=ResourceType.CHEAT_SHEET, db_index=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    difficulty = models.CharField(
        max_length=20, choices=Lesson.Difficulty.choices, default=Lesson.Difficulty.BEGINNER
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_resources"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="learning_resources")
    related_lessons = models.ManyToManyField(Lesson, blank=True, related_name="learning_resources")
    featured = models.BooleanField(default=False, db_index=True)
    content = models.TextField(
        blank=True,
        help_text="Main public resource content. Markdown-style headings and code fences are okay.",
    )
    beginner_tip = models.CharField(max_length=240, blank=True)
    downloadable_file = models.FileField(upload_to="resources/", blank=True)
    pdf_download_enabled = models.BooleanField(
        default=False,
        help_text="Show a generated branded PDF download on the public resource page.",
    )
    pdf_footer_note = models.CharField(
        max_length=180,
        blank=True,
        help_text="Optional short note printed in the footer of generated PDFs.",
    )
    pdf_requires_email = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Require newsletter signup before the generated PDF can be downloaded.",
    )
    pdf_lead_magnet_headline = models.CharField(
        max_length=140,
        blank=True,
        help_text="Optional headline for the email-gated PDF download page.",
    )
    pdf_lead_magnet_description = models.TextField(
        blank=True,
        help_text="Optional short description shown before the email signup form.",
    )
    external_url = models.URLField(blank=True)
    estimated_read_minutes = models.PositiveSmallIntegerField(default=5)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_resources_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_resources_updated",
    )

    class Meta:
        ordering = ("resource_type", "title")
        indexes = [
            models.Index(fields=("status", "resource_type")),
            models.Index(fields=("featured", "status")),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:210] or "resource"
            candidate = base
            suffix = 2
            while LearningResource.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("studio:resource-detail", kwargs={"slug": self.slug})

    @property
    def public_url(self):
        return reverse("learn:resource-detail", kwargs={"slug": self.slug})

    @property
    def is_public(self):
        return self.status in {self.Status.READY, self.Status.PUBLISHED}

    def __str__(self):
        return self.title


class RecommendationTuning(TimestampedModel):
    """Editable scoring weights for automatic resource CTA recommendations."""

    name = models.CharField(max_length=120, default="Default recommendation tuning")
    is_active = models.BooleanField(default=True, db_index=True)
    lesson_cta_bonus = models.IntegerField(default=20, validators=[MinValueValidator(-100), MaxValueValidator(200)])
    quiz_cta_bonus = models.IntegerField(default=35, validators=[MinValueValidator(-100), MaxValueValidator(200)])
    challenge_cta_bonus = models.IntegerField(default=40, validators=[MinValueValidator(-100), MaxValueValidator(200)])
    pdf_open_bonus = models.IntegerField(default=50, validators=[MinValueValidator(-100), MaxValueValidator(200)])
    pdf_lead_magnet_bonus = models.IntegerField(default=70, validators=[MinValueValidator(-100), MaxValueValidator(200)])
    newsletter_cta_bonus = models.IntegerField(default=35, validators=[MinValueValidator(-100), MaxValueValidator(200)])

    related_lesson_weight = models.IntegerField(default=80, validators=[MinValueValidator(0), MaxValueValidator(200)])
    category_match_weight = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(150)])
    difficulty_match_weight = models.IntegerField(default=18, validators=[MinValueValidator(0), MaxValueValidator(100)])
    topic_overlap_weight = models.IntegerField(default=8, validators=[MinValueValidator(0), MaxValueValidator(50)])
    topic_overlap_cap = models.IntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(300)])
    active_quiz_weight = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    active_challenge_weight = models.IntegerField(default=12, validators=[MinValueValidator(0), MaxValueValidator(100)])
    practice_code_weight = models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(100)])
    conversion_weight = models.IntegerField(default=6, validators=[MinValueValidator(0), MaxValueValidator(50)])
    conversion_cap = models.IntegerField(default=48, validators=[MinValueValidator(0), MaxValueValidator(300)])
    cta_click_weight = models.IntegerField(default=3, validators=[MinValueValidator(0), MaxValueValidator(50)])
    cta_click_cap = models.IntegerField(default=24, validators=[MinValueValidator(0), MaxValueValidator(300)])

    exact_accepted_boost = models.IntegerField(default=60, validators=[MinValueValidator(0), MaxValueValidator(200)])
    exact_dismissed_penalty = models.IntegerField(default=90, validators=[MinValueValidator(0), MaxValueValidator(250)])
    ignored_per_show_penalty = models.IntegerField(default=8, validators=[MinValueValidator(0), MaxValueValidator(50)])
    ignored_penalty_cap = models.IntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(200)])
    similar_accepted_boost = models.IntegerField(default=6, validators=[MinValueValidator(0), MaxValueValidator(50)])
    similar_accepted_cap = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(200)])
    similar_dismissed_penalty = models.IntegerField(default=8, validators=[MinValueValidator(0), MaxValueValidator(50)])
    similar_dismissed_cap = models.IntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(200)])
    similar_ignored_penalty = models.IntegerField(default=3, validators=[MinValueValidator(0), MaxValueValidator(50)])
    similar_ignored_cap = models.IntegerField(default=18, validators=[MinValueValidator(0), MaxValueValidator(200)])
    same_lesson_accepted_boost = models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(50)])
    same_lesson_accepted_cap = models.IntegerField(default=20, validators=[MinValueValidator(0), MaxValueValidator(200)])
    same_lesson_dismissed_penalty = models.IntegerField(default=6, validators=[MinValueValidator(0), MaxValueValidator(50)])
    same_lesson_dismissed_cap = models.IntegerField(default=24, validators=[MinValueValidator(0), MaxValueValidator(200)])
    feedback_adjustment_floor = models.IntegerField(default=-120, validators=[MinValueValidator(-500), MaxValueValidator(0)])
    feedback_adjustment_ceiling = models.IntegerField(default=90, validators=[MinValueValidator(0), MaxValueValidator(500)])

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-is_active", "name")
        verbose_name = "recommendation tuning"

    def __str__(self):
        return f"{self.name}{' (active)' if self.is_active else ''}"

    @classmethod
    def get_active(cls):
        tuning = cls.objects.filter(is_active=True).order_by("pk").first()
        if tuning:
            return tuning
        return cls.objects.create(name="Default recommendation tuning", is_active=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)


class RecommendationTuningChangeLog(TimestampedModel):
    """Audit trail for recommendation tuning changes, experiments, outcomes, and preset applications."""

    class Action(models.TextChoices):
        MANUAL_UPDATE = "manual_update", "Manual update"
        PRESET_APPLIED = "preset_applied", "Preset applied"
        ROLLBACK_RESTORED = "rollback_restored", "Rollback restored"

    class ExperimentStatus(models.TextChoices):
        NOT_EXPERIMENT = "not_experiment", "Not an experiment"
        PLANNED = "planned", "Planned"
        RUNNING = "running", "Running"
        KEEP = "keep", "Keep changes"
        ROLLBACK = "rollback", "Rollback recommended"
        COMPLETE = "complete", "Complete"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    class ExperimentOutcome(models.TextChoices):
        NOT_RECORDED = "not_recorded", "Not recorded"
        POSITIVE = "positive", "Positive"
        NEUTRAL = "neutral", "Neutral"
        NEGATIVE = "negative", "Negative"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    tuning = models.ForeignKey(
        RecommendationTuning,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_tuning_changes",
    )
    preset_key = models.CharField(max_length=80, blank=True)
    preset_name = models.CharField(max_length=120, blank=True)
    reason = models.TextField(blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    diff = models.JSONField(default=dict, blank=True)
    request_path = models.CharField(max_length=300, blank=True)
    experiment_label = models.CharField(
        max_length=160,
        blank=True,
        db_index=True,
        help_text="Optional label for a tuning experiment, such as August Instagram growth test.",
    )
    experiment_status = models.CharField(
        max_length=30,
        choices=ExperimentStatus.choices,
        default=ExperimentStatus.NOT_EXPERIMENT,
        db_index=True,
    )
    experiment_outcome = models.CharField(
        max_length=30,
        choices=ExperimentOutcome.choices,
        default=ExperimentOutcome.NOT_RECORDED,
        db_index=True,
    )
    experiment_notes = models.TextField(
        blank=True,
        help_text="Result notes, decision rationale, or follow-up observations for this tuning experiment.",
    )
    outcome_recorded_at = models.DateTimeField(null=True, blank=True)
    outcome_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_tuning_outcomes_recorded",
    )

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = "recommendation tuning change log"
        verbose_name_plural = "recommendation tuning change logs"

    def __str__(self):
        label = self.preset_name or self.get_action_display()
        return f"{label} · {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def changed_field_count(self):
        return len(self.diff or {})

    @property
    def is_experiment(self):
        return bool(self.experiment_label or self.experiment_status != self.ExperimentStatus.NOT_EXPERIMENT)

    @property
    def experiment_summary(self):
        if not self.is_experiment:
            return "Not tracked as experiment"
        return f"{self.experiment_label or 'Unnamed experiment'} · {self.get_experiment_status_display()} · {self.get_experiment_outcome_display()}"


class ResourceCTA(TimestampedModel):
    class TargetType(models.TextChoices):
        LESSON = "lesson", "Start matching lesson"
        QUIZ = "quiz", "Try quiz next"
        CHALLENGE = "challenge", "Practice with a challenge"
        PDF = "pdf", "Download resource PDF"
        NEWSLETTER = "newsletter", "Join the newsletter"
        EXTERNAL = "external", "External link"

    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="cta_blocks",
    )
    position = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    target_type = models.CharField(
        max_length=30, choices=TargetType.choices, default=TargetType.LESSON, db_index=True
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    button_label = models.CharField(max_length=80, default="Start now")
    target_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_ctas",
        help_text="Lesson to send learners to for lesson, quiz, and challenge CTA blocks.",
    )
    target_url = models.CharField(
        max_length=300,
        blank=True,
        help_text="External URL or custom path. Leave blank for lesson, PDF, and newsletter CTA types.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("resource", "position"), name="unique_resource_cta_position"
            )
        ]
        indexes = [
            models.Index(fields=("resource", "is_active", "position")),
            models.Index(fields=("target_type", "is_active")),
        ]

    def __str__(self):
        return f"{self.resource}: {self.title}"




class RecommendationTuningExperimentSnapshot(TimestampedModel):
    """Before/after performance snapshot for a recommendation tuning experiment."""

    change_log = models.ForeignKey(
        RecommendationTuningChangeLog,
        on_delete=models.CASCADE,
        related_name="performance_snapshots",
    )
    window_days = models.PositiveSmallIntegerField(default=14)
    before_start = models.DateTimeField(db_index=True)
    before_end = models.DateTimeField(db_index=True)
    after_start = models.DateTimeField(db_index=True)
    after_end = models.DateTimeField(db_index=True)
    before_metrics = models.JSONField(default=dict, blank=True)
    after_metrics = models.JSONField(default=dict, blank=True)
    deltas = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_tuning_experiment_snapshots",
    )
    generated_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-generated_at", "-pk")
        indexes = [
            models.Index(fields=("change_log", "generated_at")),
            models.Index(fields=("before_start", "after_end")),
        ]
        verbose_name = "recommendation tuning experiment snapshot"
        verbose_name_plural = "recommendation tuning experiment snapshots"

    @property
    def experiment_label(self):
        return self.change_log.experiment_label or self.change_log.preset_name or self.change_log.get_action_display()

    def __str__(self):
        return f"{self.experiment_label} · {self.window_days} day snapshot"


class ExperimentDecisionTuning(TimestampedModel):
    """Editable thresholds and metric weights for experiment decision recommendations."""

    name = models.CharField(max_length=120, default="Default experiment decision tuning")
    is_active = models.BooleanField(default=True, db_index=True)

    keep_score_threshold = models.FloatField(default=6.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    keep_primary_positive_min = models.PositiveSmallIntegerField(default=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    keep_high_confidence_score = models.FloatField(default=12.0, validators=[MinValueValidator(0), MaxValueValidator(200)])
    rollback_score_threshold = models.FloatField(default=-5.0, validators=[MinValueValidator(-100), MaxValueValidator(0)])
    rollback_primary_negative_min = models.PositiveSmallIntegerField(default=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    rollback_high_confidence_score = models.FloatField(default=-10.0, validators=[MinValueValidator(-200), MaxValueValidator(0)])
    low_confidence_abs_score = models.FloatField(default=4.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_metric_change_magnitude = models.FloatField(default=3.0, validators=[MinValueValidator(0.1), MaxValueValidator(100)])

    social_new_followers_weight = models.FloatField(default=2.0, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    social_engagements_weight = models.FloatField(default=1.4, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    social_reach_weight = models.FloatField(default=0.8, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    social_clicks_weight = models.FloatField(default=1.2, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    resources_pdf_downloads_weight = models.FloatField(default=1.6, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    resources_pdf_unlocks_weight = models.FloatField(default=1.3, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    resources_subscribers_weight = models.FloatField(default=2.0, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    newsletter_clicks_weight = models.FloatField(default=1.7, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    newsletter_open_rate_weight = models.FloatField(default=0.8, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    ctas_cta_clicks_weight = models.FloatField(default=1.8, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    conversions_total_conversions_weight = models.FloatField(default=2.5, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    conversions_lesson_views_weight = models.FloatField(default=1.2, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    conversions_quiz_attempts_weight = models.FloatField(default=1.5, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    conversions_challenge_attempts_weight = models.FloatField(default=1.7, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    conversions_lesson_completions_weight = models.FloatField(default=2.2, validators=[MinValueValidator(-20), MaxValueValidator(20)])

    newsletter_unsubscribes_penalty_weight = models.FloatField(default=2.0, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    newsletter_bounces_penalty_weight = models.FloatField(default=1.5, validators=[MinValueValidator(-20), MaxValueValidator(20)])

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-is_active", "name")
        verbose_name = "experiment decision tuning"
        verbose_name_plural = "experiment decision tuning"

    def __str__(self):
        return f"{self.name}{' (active)' if self.is_active else ''}"

    @classmethod
    def get_active(cls):
        tuning = cls.objects.filter(is_active=True).order_by("pk").first()
        if tuning:
            return tuning
        return cls.objects.create(name="Default experiment decision tuning", is_active=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    def positive_weight_items(self):
        return {
            ("social", "new_followers"): self.social_new_followers_weight,
            ("social", "engagements"): self.social_engagements_weight,
            ("social", "reach"): self.social_reach_weight,
            ("social", "clicks"): self.social_clicks_weight,
            ("resources", "pdf_downloads"): self.resources_pdf_downloads_weight,
            ("resources", "pdf_unlocks"): self.resources_pdf_unlocks_weight,
            ("resources", "subscribers"): self.resources_subscribers_weight,
            ("newsletter", "clicks"): self.newsletter_clicks_weight,
            ("newsletter", "open_rate"): self.newsletter_open_rate_weight,
            ("ctas", "cta_clicks"): self.ctas_cta_clicks_weight,
            ("conversions", "total_conversions"): self.conversions_total_conversions_weight,
            ("conversions", "lesson_views"): self.conversions_lesson_views_weight,
            ("conversions", "quiz_attempts"): self.conversions_quiz_attempts_weight,
            ("conversions", "challenge_attempts"): self.conversions_challenge_attempts_weight,
            ("conversions", "lesson_completions"): self.conversions_lesson_completions_weight,
        }

    def negative_weight_items(self):
        return {
            ("newsletter", "unsubscribes"): self.newsletter_unsubscribes_penalty_weight,
            ("newsletter", "bounces"): self.newsletter_bounces_penalty_weight,
        }


class ExperimentDecisionTuningChangeLog(TimestampedModel):
    """Audit trail for experiment decision-rule tuning changes, preset experiments, and outcomes."""

    class Action(models.TextChoices):
        MANUAL_UPDATE = "manual_update", "Manual update"
        PRESET_APPLIED = "preset_applied", "Preset applied"
        ROLLBACK_RESTORED = "rollback_restored", "Rollback restored"

    class ExperimentStatus(models.TextChoices):
        NOT_EXPERIMENT = "not_experiment", "Not an experiment"
        PLANNED = "planned", "Planned"
        RUNNING = "running", "Running"
        KEEP = "keep", "Keep changes"
        ROLLBACK = "rollback", "Rollback recommended"
        COMPLETE = "complete", "Complete"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    class ExperimentOutcome(models.TextChoices):
        NOT_RECORDED = "not_recorded", "Not recorded"
        POSITIVE = "positive", "Positive"
        NEUTRAL = "neutral", "Neutral"
        NEGATIVE = "negative", "Negative"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    tuning = models.ForeignKey(
        ExperimentDecisionTuning,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="experiment_decision_tuning_changes",
    )
    preset_key = models.CharField(max_length=80, blank=True)
    preset_name = models.CharField(max_length=120, blank=True)
    reason = models.TextField(blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    diff = models.JSONField(default=dict, blank=True)
    request_path = models.CharField(max_length=300, blank=True)
    experiment_label = models.CharField(
        max_length=160,
        blank=True,
        db_index=True,
        help_text="Optional label for a decision-rule experiment, such as August lead magnet decision test.",
    )
    experiment_status = models.CharField(
        max_length=30,
        choices=ExperimentStatus.choices,
        default=ExperimentStatus.NOT_EXPERIMENT,
        db_index=True,
    )
    experiment_outcome = models.CharField(
        max_length=30,
        choices=ExperimentOutcome.choices,
        default=ExperimentOutcome.NOT_RECORDED,
        db_index=True,
    )
    experiment_notes = models.TextField(
        blank=True,
        help_text="Result notes, hypothesis, decision rationale, or follow-up observations for this decision-rule experiment.",
    )
    outcome_recorded_at = models.DateTimeField(null=True, blank=True)
    outcome_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="experiment_decision_tuning_outcomes_recorded",
    )

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = "experiment decision tuning change log"
        verbose_name_plural = "experiment decision tuning change logs"

    def __str__(self):
        label = self.preset_name or self.get_action_display()
        return f"{label} · {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def changed_field_count(self):
        return len(self.diff or {})

    @property
    def is_experiment(self):
        return bool(self.experiment_label or self.experiment_status != self.ExperimentStatus.NOT_EXPERIMENT)

    @property
    def experiment_summary(self):
        if not self.is_experiment:
            return "Not tracked as experiment"
        return f"{self.experiment_label or 'Unnamed experiment'} · {self.get_experiment_status_display()} · {self.get_experiment_outcome_display()}"







class ExperimentDecisionTuningExperimentSnapshot(TimestampedModel):
    """Before/after performance snapshot for a decision-rule tuning experiment."""

    change_log = models.ForeignKey(
        ExperimentDecisionTuningChangeLog,
        on_delete=models.CASCADE,
        related_name="performance_snapshots",
    )
    window_days = models.PositiveSmallIntegerField(default=14)
    before_start = models.DateTimeField(db_index=True)
    before_end = models.DateTimeField(db_index=True)
    after_start = models.DateTimeField(db_index=True)
    after_end = models.DateTimeField(db_index=True)
    before_metrics = models.JSONField(default=dict, blank=True)
    after_metrics = models.JSONField(default=dict, blank=True)
    deltas = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="experiment_decision_tuning_experiment_snapshots",
    )
    generated_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-generated_at", "-pk")
        indexes = [
            models.Index(fields=("change_log", "generated_at")),
            models.Index(fields=("before_start", "after_end")),
        ]
        verbose_name = "experiment decision-rule snapshot"
        verbose_name_plural = "experiment decision-rule snapshots"

    @property
    def experiment_label(self):
        return self.change_log.experiment_label or self.change_log.preset_name or self.change_log.get_action_display()

    def __str__(self):
        return f"{self.experiment_label} · {self.window_days} day decision-rule snapshot"




class ExperimentDecisionTuningSnapshotComparisonReport(TimestampedModel):
    """Named, reusable comparison of decision-rule experiment snapshots."""

    class DecisionStatus(models.TextChoices):
        UNDECIDED = "undecided", "No decision yet"
        KEEP = "keep", "Keep"
        ROLL_BACK = "roll_back", "Roll back"
        WATCH = "watch", "Watch"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    decision_status = models.CharField(
        max_length=20,
        choices=DecisionStatus.choices,
        default=DecisionStatus.UNDECIDED,
        db_index=True,
        help_text="Final or current decision for this saved comparison report.",
    )
    decision_summary = models.CharField(
        max_length=240,
        blank=True,
        help_text="Short decision statement, such as keep the lead-magnet rules for another two weeks.",
    )
    decision_notes = models.TextField(
        blank=True,
        help_text="Decision rationale, follow-up actions, risks, or rollback/watch criteria.",
    )
    decision_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_reports_owned",
        help_text="Person responsible for following up on this report decision.",
    )
    decision_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_report_decisions_recorded",
        help_text="Staff user who last recorded a report decision.",
    )
    decision_recorded_at = models.DateTimeField(null=True, blank=True, db_index=True)
    snapshots = models.ManyToManyField(
        ExperimentDecisionTuningExperimentSnapshot,
        related_name="saved_comparison_reports",
        blank=True,
    )
    preset_keys = models.JSONField(
        default=list,
        blank=True,
        help_text="Decision-rule preset keys included when this comparison is rendered.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Observations, interpretation, and follow-up decisions for this saved comparison.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_reports_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_reports_updated",
    )
    cloned_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clones",
        help_text="Original saved comparison report this report was cloned from, when applicable.",
    )
    source_template = models.ForeignKey(
        "ExperimentDecisionTuningSnapshotComparisonReportTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
        help_text="Report template used to create this saved comparison report, when applicable.",
    )

    class Meta:
        ordering = ("-updated_at", "-pk")
        indexes = [
            models.Index(fields=("title", "updated_at")),
            models.Index(fields=("decision_status", "updated_at")),
            models.Index(fields=("source_template", "updated_at")),
        ]
        verbose_name = "decision-rule snapshot comparison report"
        verbose_name_plural = "decision-rule snapshot comparison reports"

    def __str__(self):
        return self.title

    @property
    def snapshot_count(self):
        return self.snapshots.count()

    @property
    def preset_count(self):
        return len(self.preset_keys or [])

    @property
    def decision_status_css(self):
        return {
            self.DecisionStatus.KEEP: "keep",
            self.DecisionStatus.ROLL_BACK: "rollback",
            self.DecisionStatus.WATCH: "inconclusive",
            self.DecisionStatus.ARCHIVED: "neutral",
        }.get(self.decision_status, "neutral")

    @property
    def has_recorded_decision(self):
        return self.decision_status != self.DecisionStatus.UNDECIDED


class ExperimentDecisionTuningSnapshotComparisonReportTemplate(TimestampedModel):
    """Reusable saved-report structure for recurring decision-rule comparison reviews."""

    class TemplateType(models.TextChoices):
        MONTHLY_GROWTH = "monthly_growth", "Monthly Growth Review"
        LEAD_MAGNET = "lead_magnet", "Lead Magnet Review"
        INSTAGRAM_EXPERIMENT = "instagram_experiment", "Instagram Experiment Review"
        LEARNING_CONVERSION = "learning_conversion", "Learning Conversion Review"
        CUSTOM = "custom", "Custom"

    title = models.CharField(max_length=180, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)
    template_type = models.CharField(
        max_length=40,
        choices=TemplateType.choices,
        default=TemplateType.CUSTOM,
        db_index=True,
    )
    description = models.TextField(blank=True)
    default_report_title = models.CharField(
        max_length=180,
        blank=True,
        help_text="Optional title seed used when creating a report from this template.",
    )
    default_description = models.TextField(blank=True)
    default_notes = models.TextField(
        blank=True,
        help_text="Default analysis prompts, checklist items, or review notes copied into new reports.",
    )
    default_preset_keys = models.JSONField(
        default=list,
        blank=True,
        help_text="Decision-rule preset keys included by default when a report is created from this template.",
    )
    recommended_snapshot_count = models.PositiveSmallIntegerField(
        default=3,
        help_text="Suggested number of recent snapshots to preselect when creating a report.",
    )
    recommended_window_days = models.PositiveSmallIntegerField(
        default=14,
        help_text="Recommended experiment snapshot window for this review type.",
    )
    focus_areas = models.JSONField(
        default=list,
        blank=True,
        help_text="Human-readable focus areas such as follower growth, PDF downloads, or learner conversions.",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_report_templates_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_rule_snapshot_comparison_report_templates_updated",
    )

    class Meta:
        ordering = ("template_type", "title")
        indexes = [
            models.Index(fields=("template_type", "is_active")),
            models.Index(fields=("slug",)),
        ]
        verbose_name = "decision-rule comparison report template"
        verbose_name_plural = "decision-rule comparison report templates"

    def __str__(self):
        return self.title

    @property
    def focus_area_count(self):
        return len(self.focus_areas or [])

    @property
    def preset_count(self):
        return len(self.default_preset_keys or [])

    def build_report_initial(self):
        return {
            "title": self.default_report_title or self.title,
            "description": self.default_description or self.description,
            "notes": self.default_notes,
            "preset_keys": list(self.default_preset_keys or []),
        }


class ExperimentDecisionTuningSnapshotComparisonReportTemplateRecommendationFeedback(TimestampedModel):
    """Staff feedback on saved report-template recommendations.

    This creates a lightweight feedback loop so Studio can learn whether a
    template recommendation was useful, dismissed, or worth revisiting later.
    """

    class Status(models.TextChoices):
        SHOWN = "shown", "Shown / ignored"
        USEFUL = "useful", "Useful"
        DISMISSED = "dismissed", "Dismissed"
        REVISIT = "revisit", "Revisit later"

    template = models.ForeignKey(
        ExperimentDecisionTuningSnapshotComparisonReportTemplate,
        on_delete=models.CASCADE,
        related_name="recommendation_feedback",
    )
    recommendation_key = models.CharField(max_length=180, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SHOWN, db_index=True)
    score = models.IntegerField(default=0)
    priority = models.CharField(max_length=20, blank=True)
    reasons = models.JSONField(default=list, blank=True)
    suggested_snapshot_ids = models.JSONField(default=list, blank=True)
    times_shown = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_template_recommendation_feedback_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_template_recommendation_feedback_updated",
    )

    class Meta:
        ordering = ("-last_seen_at", "template__title")
        unique_together = (("template", "recommendation_key", "created_by"),)
        indexes = [
            models.Index(fields=("status", "last_seen_at")),
            models.Index(fields=("template", "status")),
            models.Index(fields=("recommendation_key", "status")),
        ]
        verbose_name = "report-template recommendation feedback"
        verbose_name_plural = "report-template recommendation feedback"

    def __str__(self):
        return f"{self.template} · {self.get_status_display()}"

    @property
    def is_ignored_signal(self):
        return self.status == self.Status.SHOWN and self.times_shown >= 3



class ResourceCTARecommendationFeedback(TimestampedModel):
    class Status(models.TextChoices):
        SHOWN = "shown", "Shown / ignored"
        ACCEPTED = "accepted", "Accepted"
        DISMISSED = "dismissed", "Dismissed"

    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="cta_recommendation_feedback",
    )
    recommendation_key = models.CharField(max_length=120, db_index=True)
    target_type = models.CharField(max_length=30, choices=ResourceCTA.TargetType.choices)
    target_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_recommendation_feedback",
    )
    title = models.CharField(max_length=180)
    score = models.IntegerField(default=0)
    reasons = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SHOWN, db_index=True)
    times_shown = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    applied_cta = models.ForeignKey(
        ResourceCTA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_feedback",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_recommendations_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_recommendations_updated",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-last_seen_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("resource", "recommendation_key"),
                name="unique_resource_cta_recommendation_feedback",
            )
        ]
        indexes = [
            models.Index(fields=("resource", "status", "last_seen_at")),
            models.Index(fields=("target_type", "status")),
        ]

    @property
    def is_ignored(self):
        return self.status == self.Status.SHOWN and self.times_shown > 1

    def __str__(self):
        return f"{self.resource}: {self.title} ({self.get_status_display()})"


class ResourceCTAClickEvent(TimestampedModel):
    cta = models.ForeignKey(
        ResourceCTA,
        on_delete=models.CASCADE,
        related_name="click_events",
    )
    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="cta_click_events",
    )
    target_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_click_events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_click_events",
    )
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_cta_click_events",
    )
    email = models.EmailField(blank=True, db_index=True)
    source_url = models.CharField(max_length=300, blank=True)
    target_url = models.CharField(max_length=300, blank=True)
    referrer = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("resource", "occurred_at")),
            models.Index(fields=("cta", "occurred_at")),
            models.Index(fields=("target_lesson", "occurred_at")),
        ]

    def __str__(self):
        return f"CTA click · {self.cta.title} · {self.resource}"



class ResourcePerformanceEvent(TimestampedModel):
    class EventType(models.TextChoices):
        VIEW = "view", "Resource view"
        PDF_UNLOCK = "pdf_unlock", "PDF unlock"
        PDF_DOWNLOAD = "pdf_download", "PDF download"

    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="performance_events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_performance_events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_performance_events",
    )
    email = models.EmailField(blank=True, db_index=True)
    source_url = models.CharField(max_length=300, blank=True)
    referrer = models.CharField(max_length=300, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("resource", "event_type", "occurred_at")),
            models.Index(fields=("event_type", "occurred_at")),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} · {self.resource}"




class ResourceLessonConversionEvent(TimestampedModel):
    class EventType(models.TextChoices):
        LESSON_VIEW = "lesson_view", "Lesson view"
        ACCOUNT_SIGNUP = "account_signup", "Account signup"
        QUIZ_ATTEMPT = "quiz_attempt", "Quiz attempt"
        CHALLENGE_ATTEMPT = "challenge_attempt", "Challenge attempt"
        LESSON_COMPLETE = "lesson_complete", "Lesson complete"

    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="lesson_conversion_events",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_conversion_events",
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    source_event = models.ForeignKey(
        ResourcePerformanceEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_conversion_events",
        help_text="The resource view/unlock/download event that received attribution when available.",
    )
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_lesson_conversion_events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_lesson_conversion_events",
    )
    cta = models.ForeignKey(
        ResourceCTA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversion_events",
        help_text="Resource CTA block that received click attribution when available.",
    )
    cta_click = models.ForeignKey(
        ResourceCTAClickEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversion_events",
        help_text="Specific CTA click that received attribution when available.",
    )
    email = models.EmailField(blank=True, db_index=True)
    attribution_event_type = models.CharField(max_length=20, choices=ResourcePerformanceEvent.EventType.choices, blank=True)
    attribution_source_url = models.CharField(max_length=300, blank=True)
    referrer = models.CharField(max_length=300, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("resource", "event_type", "occurred_at")),
            models.Index(fields=("lesson", "event_type", "occurred_at")),
            models.Index(fields=("event_type", "occurred_at")),
            models.Index(fields=("email", "occurred_at")),
        ]

    def __str__(self):
        lesson = f" → {self.lesson}" if self.lesson_id else ""
        return f"{self.get_event_type_display()} · {self.resource}{lesson}"


class ResourceLeadMagnetAccess(TimestampedModel):
    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="lead_magnet_accesses",
    )
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_lead_magnet_accesses",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resource_lead_magnet_accesses",
    )
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    source_url = models.CharField(max_length=300, blank=True)
    access_granted_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-access_granted_at", "email")
        unique_together = (("resource", "email"),)
        indexes = [
            models.Index(fields=("resource", "access_granted_at")),
            models.Index(fields=("email", "access_granted_at")),
        ]

    def register_download(self):
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=["download_count", "last_downloaded_at", "updated_at"])

    def __str__(self):
        return f"{self.email} → {self.resource}"


class WebsiteExport(TimestampedModel):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="website_exports"
    )
    revision = models.PositiveIntegerField()
    schema_version = models.CharField(max_length=20, default="1.0")
    content_hash = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField()
    rendered_html = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="website_exports_created",
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("lesson", "revision"), name="unique_lesson_website_revision"
            )
        ]

    def __str__(self):
        return f"{self.lesson} website export r{self.revision}"
