from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView

from studio.models import (
    LearningResource,
    ResourceLessonConversionEvent,
    ResourcePerformanceEvent,
)

from .forms import LearnerProfileForm, LearnerRegistrationForm


def _track_signup_resource_conversion(request, user):
    data = request.session.get("resource_conversion_attribution") or {}
    resource_id = data.get("resource_id")
    if not resource_id:
        return None
    source_event = None
    event_id = data.get("event_id")
    if event_id:
        source_event = (
            ResourcePerformanceEvent.objects.filter(
                pk=event_id, resource_id=resource_id
            )
            .select_related("resource", "subscriber")
            .first()
        )
    resource = (
        source_event.resource
        if source_event
        else LearningResource.objects.filter(pk=resource_id).first()
    )
    if not resource:
        return None
    occurred_at = source_event.occurred_at if source_event else None
    if not occurred_at and data.get("occurred_at"):
        try:
            occurred_at = datetime.fromisoformat(data["occurred_at"])
        except (TypeError, ValueError):
            occurred_at = None
    if occurred_at and timezone.is_naive(occurred_at):
        occurred_at = timezone.make_aware(occurred_at)
    if occurred_at and occurred_at < timezone.now() - timedelta(days=30):
        return None
    key = f"{resource.pk}:none:{ResourceLessonConversionEvent.EventType.ACCOUNT_SIGNUP}:{user.pk}"
    seen = request.session.get("resource_conversion_keys", [])
    if key in seen:
        return None
    conversion = ResourceLessonConversionEvent.objects.create(
        resource=resource,
        event_type=ResourceLessonConversionEvent.EventType.ACCOUNT_SIGNUP,
        source_event=source_event,
        subscriber=source_event.subscriber if source_event else None,
        user=user,
        email=(
            getattr(user, "email", "") or (source_event.email if source_event else "")
        )[:254],
        attribution_event_type=(
            source_event.event_type if source_event else data.get("event_type", "")
        )[:20],
        attribution_source_url=(source_event.source_url if source_event else "")[:300],
        referrer=request.META.get("HTTP_REFERER", "")[:300],
        metadata={"source": "learner_registration"},
    )
    request.session["resource_conversion_keys"] = (seen + [key])[-100:]
    return conversion


class LearnerRegistrationView(CreateView):
    form_class = LearnerRegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("learn:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        _track_signup_resource_conversion(self.request, self.object)
        messages.success(self.request, "Your learner account is ready.")
        return response


class LearnerProfileView(UpdateView):
    form_class = LearnerProfileForm
    template_name = "registration/profile.html"
    success_url = reverse_lazy("learn:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile settings saved.")
        return super().form_valid(form)
