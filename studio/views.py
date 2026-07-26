import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    BrandProfileForm,
    CaptionDraftForm,
    CaptionGenerationForm,
    GraphicGenerationForm,
    LessonBlockForm,
    LessonForm,
)
from .models import (
    AIGeneration,
    BrandProfile,
    CaptionDraft,
    Lesson,
    LessonBlock,
    WebsiteExport,
)
from .services.graphics import GraphicGenerationError, generate_graphics
from .services.openai import OpenAIServiceError, generate_caption
from .services.website import (
    create_website_export,
    render_website_page,
    seo_diagnostics,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "studio/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson_counts"] = Lesson.objects.values("status").annotate(total=Count("id"))
        context["recent_lessons"] = Lesson.objects.select_related("category", "series")[:8]
        context["total_ai_cost"] = (
            AIGeneration.objects.filter(status=AIGeneration.Status.SUCCEEDED).aggregate(
                total=Sum("estimated_cost_usd")
            )["total"]
            or 0
        )
        context["recent_generations"] = AIGeneration.objects.select_related("lesson")[:6]
        first_lesson = Lesson.objects.order_by("created_at").first()
        lesson_url = first_lesson.get_absolute_url() if first_lesson else reverse(
            "studio:lesson-create"
        )
        steps = [
            {
                "label": "Sign in to your private studio",
                "description": "Your email-only account protects every studio screen.",
                "complete": True,
                "url": reverse("studio:dashboard"),
            },
            {
                "label": "Create your first lesson",
                "description": "Start with a title, summary, difficulty, and Draft status.",
                "complete": first_lesson is not None,
                "url": reverse("studio:lesson-create"),
            },
            {
                "label": "Add lesson content blocks",
                "description": "Build the explanation, code, output, quiz, or challenge.",
                "complete": LessonBlock.objects.exists(),
                "url": lesson_url,
            },
            {
                "label": "Generate a social graphic",
                "description": "Choose a template and one or more platform sizes.",
                "complete": Lesson.objects.filter(assets__status="ready").exists(),
                "url": lesson_url,
            },
            {
                "label": "Generate and review a caption",
                "description": "Create platform drafts, then edit or approve the copy.",
                "complete": CaptionDraft.objects.exists(),
                "url": lesson_url,
            },
            {
                "label": "Preview the website lesson",
                "description": "Resolve SEO warnings and inspect the standalone page.",
                "complete": WebsiteExport.objects.exists(),
                "url": lesson_url,
            },
        ]
        completed = sum(step["complete"] for step in steps)
        context["onboarding_steps"] = steps
        context["onboarding_completed"] = completed
        context["onboarding_total"] = len(steps)
        context["onboarding_percent"] = round(completed / len(steps) * 100)
        return context


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = "studio/help.html"


class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = "studio/lesson_list.html"
    context_object_name = "lessons"
    paginate_by = 30

    def get_queryset(self):
        queryset = Lesson.objects.select_related("category", "series")
        status = self.request.GET.get("status")
        if status in Lesson.Status.values:
            queryset = queryset.filter(status=status)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(seo_title__icontains=query)
                | Q(seo_description__icontains=query)
                | Q(internal_notes__icontains=query)
                | Q(blocks__title__icontains=query)
                | Q(blocks__content__icontains=query)
                | Q(category__name__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(series__title__icontains=query)
            )
        return queryset.distinct()


class LessonCreateView(LoginRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "studio/lesson_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Lesson created. Add its content blocks next.")
        return super().form_valid(form)


class LessonUpdateView(LoginRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = "studio/lesson_form.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Lesson saved.")
        return super().form_valid(form)


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "studio/lesson_detail.html"

    def get_queryset(self):
        return Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks",
            "captions__generation",
            "assets__template",
            "ai_generations",
            "website_exports",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["caption_form"] = CaptionGenerationForm()
        context["graphic_form"] = GraphicGenerationForm()
        context["seo_diagnostics"] = seo_diagnostics(self.object)
        context["lesson_workflow"] = [
            {
                "label": "Details",
                "complete": bool(self.object.summary),
                "url": reverse("studio:lesson-update", args=[self.object.slug]),
            },
            {
                "label": "Content",
                "complete": self.object.blocks.exists(),
                "url": reverse("studio:block-create", args=[self.object.slug]),
            },
            {
                "label": "Graphics",
                "complete": self.object.assets.filter(status="ready").exists(),
                "url": "#graphics",
            },
            {
                "label": "Captions",
                "complete": self.object.captions.exists(),
                "url": "#captions",
            },
            {
                "label": "Website",
                "complete": self.object.website_exports.exists(),
                "url": "#website",
            },
        ]
        return context


class BlockCreateView(LoginRequiredMixin, CreateView):
    model = LessonBlock
    form_class = LessonBlockForm
    template_name = "studio/block_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        form.instance.position = (
            self.lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
        ) + 1
        messages.success(self.request, "Content block added.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.lesson.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.lesson
        return context


class BlockUpdateView(LoginRequiredMixin, UpdateView):
    model = LessonBlock
    form_class = LessonBlockForm
    template_name = "studio/block_form.html"

    def get_success_url(self):
        messages.success(self.request, "Content block updated.")
        return self.object.lesson.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object.lesson
        return context


class BlockDeleteView(LoginRequiredMixin, DeleteView):
    model = LessonBlock
    template_name = "studio/block_confirm_delete.html"

    def get_success_url(self):
        return self.object.lesson.get_absolute_url()


class CaptionUpdateView(LoginRequiredMixin, UpdateView):
    model = CaptionDraft
    form_class = CaptionDraftForm
    template_name = "studio/caption_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Caption draft saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.lesson.get_absolute_url()


class BrandProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = BrandProfile
    form_class = BrandProfileForm
    template_name = "studio/brand_form.html"
    success_url = reverse_lazy("studio:brand-update")

    def get_object(self, queryset=None):
        return BrandProfile.get_default()

    def form_valid(self, form):
        messages.success(self.request, "Brand settings saved.")
        return super().form_valid(form)


@login_required
def move_block(request, pk, direction):
    block = get_object_or_404(LessonBlock, pk=pk)
    if request.method != "POST" or direction not in {"up", "down"}:
        return redirect(block.lesson)

    candidates = block.lesson.blocks.exclude(pk=block.pk)
    if direction == "up":
        neighbor = candidates.filter(position__lt=block.position).order_by("-position").first()
    else:
        neighbor = candidates.filter(position__gt=block.position).order_by("position").first()

    if neighbor:
        with transaction.atomic():
            temporary_position = (
                block.lesson.blocks.aggregate(maximum=Max("position"))["maximum"] or 0
            ) + 1
            original_position = block.position
            LessonBlock.objects.filter(pk=block.pk).update(position=temporary_position)
            LessonBlock.objects.filter(pk=neighbor.pk).update(position=original_position)
            LessonBlock.objects.filter(pk=block.pk).update(position=neighbor.position)
        messages.success(request, "Content block order updated.")
    return redirect(block.lesson)


@login_required
def generate_captions(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = CaptionGenerationForm(request.POST)
    if form.is_valid():
        created = 0
        for platform in form.cleaned_data["platforms"]:
            try:
                generate_caption(lesson, platform)
                created += 1
            except OpenAIServiceError as exc:
                messages.error(request, f"Could not generate {platform} caption: {exc}")
        if created:
            messages.success(request, f"Generated {created} caption draft(s).")
    else:
        messages.error(request, "Choose at least one caption platform.")
    return redirect(lesson)


@login_required
def generate_graphic_assets(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method != "POST":
        return redirect(lesson)
    form = GraphicGenerationForm(request.POST)
    if form.is_valid():
        try:
            assets = generate_graphics(
                lesson,
                form.cleaned_data["template"],
                form.cleaned_data["output_formats"],
            )
            messages.success(request, f"Generated {len(assets)} graphic asset(s).")
        except GraphicGenerationError as exc:
            messages.error(request, f"Graphic generation failed: {exc}")
    else:
        messages.error(request, "Choose a template and at least one output format.")
    return redirect(lesson)


@login_required
def website_preview(request, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks", "tags", "assets"
        ),
        slug=slug,
    )
    html, _ = render_website_page(lesson, request=request, is_preview=True)
    return HttpResponse(html)


@login_required
def create_website_export_view(request, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("category", "series").prefetch_related(
            "blocks", "tags", "assets"
        ),
        slug=slug,
    )
    if request.method != "POST":
        return redirect(lesson)
    export = create_website_export(lesson, request.user, request=request)
    messages.success(request, f"Created website export revision {export.revision}.")
    return redirect(lesson)


@login_required
def download_website_export(request, pk, output_format):
    export = get_object_or_404(WebsiteExport.objects.select_related("lesson"), pk=pk)
    if output_format == "json":
        content = json.dumps(export.payload, ensure_ascii=False, indent=2)
        content_type = "application/json"
        extension = "json"
    elif output_format == "html":
        content = export.rendered_html
        content_type = "text/html"
        extension = "html"
    else:
        return HttpResponse("Unsupported export format.", status=404)
    response = HttpResponse(content, content_type=f"{content_type}; charset=utf-8")
    filename = f"{export.lesson.slug}-r{export.revision}.{extension}"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
