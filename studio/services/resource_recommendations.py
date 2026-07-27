from __future__ import annotations

from dataclasses import dataclass, field, replace
from django.db.models import Q
from django.utils import timezone

from studio.models import (
    LearningResource,
    Lesson,
    ResourceCTA,
    ResourceCTAClickEvent,
    ResourceCTARecommendationFeedback,
    ResourceLessonConversionEvent,
    RecommendationTuning,
)


@dataclass(frozen=True)
class ResourceCTARecommendation:
    """A lightweight, deterministic CTA suggestion for a learning resource."""

    key: str
    target_type: str
    title: str
    description: str
    button_label: str
    target_lesson: Lesson | None = None
    score: int = 0
    base_score: int = 0
    feedback_adjustment: int = 0
    reasons: tuple[str, ...] = field(default_factory=tuple)
    ranking_notes: tuple[str, ...] = field(default_factory=tuple)
    already_exists: bool = False
    feedback_status: str = ""
    feedback_id: int | None = None
    times_shown: int = 0

    @property
    def target_type_label(self) -> str:
        return dict(ResourceCTA.TargetType.choices).get(self.target_type, self.target_type)

    @property
    def can_apply(self) -> bool:
        return not self.already_exists and self.feedback_status != ResourceCTARecommendationFeedback.Status.DISMISSED

    @property
    def is_dismissed(self) -> bool:
        return self.feedback_status == ResourceCTARecommendationFeedback.Status.DISMISSED

    @property
    def is_accepted(self) -> bool:
        return self.feedback_status == ResourceCTARecommendationFeedback.Status.ACCEPTED

    @property
    def is_ignored(self) -> bool:
        return self.feedback_status == ResourceCTARecommendationFeedback.Status.SHOWN and self.times_shown > 1


_PUBLIC_LESSON_STATUSES = [Lesson.Status.READY, Lesson.Status.PUBLISHED]


def _public_lesson_queryset():
    return Lesson.objects.filter(website_status__in=_PUBLIC_LESSON_STATUSES).exclude(
        status=Lesson.Status.ARCHIVED
    )


def _tokenize(value: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "for",
        "from",
        "how",
        "in",
        "intro",
        "introduction",
        "is",
        "of",
        "on",
        "python",
        "the",
        "to",
        "with",
    }
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in value or "")
    return {token for token in cleaned.split() if len(token) > 2 and token not in stop_words}


def _resource_terms(resource: LearningResource) -> set[str]:
    parts = [resource.title, resource.summary, resource.content, resource.beginner_tip, resource.category.name if resource.category_id else ""]
    return set().union(*(_tokenize(part) for part in parts))


def _lesson_score(resource: LearningResource, lesson: Lesson, related_ids: set[int], resource_terms: set[str], tuning: RecommendationTuning | None = None) -> tuple[int, list[str]]:
    tuning = tuning or RecommendationTuning.get_active()
    score = 0
    reasons: list[str] = []

    if lesson.pk in related_ids:
        score += tuning.related_lesson_weight
        reasons.append(f"already related to this resource (+{tuning.related_lesson_weight})")
    if resource.category_id and lesson.category_id == resource.category_id:
        score += tuning.category_match_weight
        reasons.append(f"same category (+{tuning.category_match_weight})")
    if lesson.difficulty == resource.difficulty:
        score += tuning.difficulty_match_weight
        reasons.append(f"same learner level (+{tuning.difficulty_match_weight})")

    lesson_terms = _tokenize(" ".join([lesson.title, lesson.summary, lesson.learning_objective, lesson.beginner_takeaway, lesson.practice_prompt]))
    overlap = resource_terms & lesson_terms
    if overlap:
        overlap_score = min(len(overlap) * tuning.topic_overlap_weight, tuning.topic_overlap_cap)
        score += overlap_score
        sample = ", ".join(sorted(overlap)[:4])
        reasons.append(f"topic overlap: {sample} (+{overlap_score})")

    if lesson.quiz_questions.filter(is_active=True).exists():
        score += tuning.active_quiz_weight
        reasons.append(f"has an active quiz (+{tuning.active_quiz_weight})")
    if lesson.code_challenges.filter(is_active=True).exists():
        score += tuning.active_challenge_weight
        reasons.append(f"has an active challenge (+{tuning.active_challenge_weight})")
    if lesson.expected_output or lesson.solution_code or lesson.starter_code:
        score += tuning.practice_code_weight
        reasons.append(f"has practice code (+{tuning.practice_code_weight})")

    conversions = ResourceLessonConversionEvent.objects.filter(resource=resource, lesson=lesson).count()
    if conversions:
        conversion_score = min(conversions * tuning.conversion_weight, tuning.conversion_cap)
        score += conversion_score
        reasons.append(f"{conversions} prior resource-attributed conversion{'s' if conversions != 1 else ''} (+{conversion_score})")

    cta_clicks = ResourceCTAClickEvent.objects.filter(resource=resource, target_lesson=lesson).count()
    if cta_clicks:
        click_score = min(cta_clicks * tuning.cta_click_weight, tuning.cta_click_cap)
        score += click_score
        reasons.append(f"{cta_clicks} prior CTA click{'s' if cta_clicks != 1 else ''} (+{click_score})")

    return score, reasons


def _rank_lessons(resource: LearningResource, limit: int = 8, tuning: RecommendationTuning | None = None) -> list[tuple[Lesson, int, list[str]]]:
    tuning = tuning or RecommendationTuning.get_active()
    related_lessons = list(resource.related_lessons.all())
    related_ids = {lesson.pk for lesson in related_lessons}
    resource_terms = _resource_terms(resource)

    queryset = _public_lesson_queryset().select_related("category").prefetch_related("quiz_questions", "code_challenges")
    filters = Q(pk__in=related_ids)
    if resource.category_id:
        filters |= Q(category_id=resource.category_id)
    for term in sorted(resource_terms)[:12]:
        filters |= Q(title__icontains=term) | Q(summary__icontains=term) | Q(learning_objective__icontains=term) | Q(beginner_takeaway__icontains=term)

    candidates = list(queryset.filter(filters).distinct()[:80])
    if not candidates:
        candidates = list(queryset[:40])

    ranked = []
    for lesson in candidates:
        score, reasons = _lesson_score(resource, lesson, related_ids, resource_terms, tuning=tuning)
        if score > 0:
            ranked.append((lesson, score, reasons))
    ranked.sort(key=lambda item: (-item[1], item[0].title.lower()))
    return ranked[:limit]


def _cta_exists(resource: LearningResource, target_type: str, target_lesson: Lesson | None = None) -> bool:
    qs = ResourceCTA.objects.filter(resource=resource, target_type=target_type)
    if target_lesson:
        qs = qs.filter(target_lesson=target_lesson)
    else:
        qs = qs.filter(target_lesson__isnull=True)
    return qs.exists()


def _ignored_feedback_queryset():
    return ResourceCTARecommendationFeedback.objects.filter(
        status=ResourceCTARecommendationFeedback.Status.SHOWN,
        times_shown__gt=1,
    )


def _bounded(value: int, floor: int, ceiling: int) -> int:
    return max(floor, min(value, ceiling))


def _feedback_adjustment(
    resource: LearningResource,
    recommendation: ResourceCTARecommendation,
    tuning: RecommendationTuning | None = None,
) -> tuple[int, list[str], str, int]:
    tuning = tuning or RecommendationTuning.get_active()
    """Convert prior feedback into a deterministic ranking adjustment.

    Exact feedback is strongest. Similar-resource and same-target patterns are weaker,
    but they let the system learn from accepted/dismissed CTA types across the studio.
    """
    adjustment = 0
    notes: list[str] = []
    feedback_status = recommendation.feedback_status
    times_shown = recommendation.times_shown

    exact = ResourceCTARecommendationFeedback.objects.filter(
        resource=resource,
        recommendation_key=recommendation.key,
    ).first()
    if exact:
        feedback_status = exact.status
        times_shown = exact.times_shown
        if exact.status == ResourceCTARecommendationFeedback.Status.ACCEPTED:
            adjustment += tuning.exact_accepted_boost
            notes.append(f"+{tuning.exact_accepted_boost} because this exact suggestion was accepted")
        elif exact.status == ResourceCTARecommendationFeedback.Status.DISMISSED:
            adjustment -= tuning.exact_dismissed_penalty
            notes.append(f"-{tuning.exact_dismissed_penalty} because this exact suggestion was dismissed")
        elif exact.times_shown > 1:
            penalty = min((exact.times_shown - 1) * tuning.ignored_per_show_penalty, tuning.ignored_penalty_cap)
            adjustment -= penalty
            notes.append(f"deprioritized because it was shown {exact.times_shown} times without action")

    same_resource_type = ResourceCTARecommendationFeedback.objects.filter(
        resource__resource_type=resource.resource_type,
        target_type=recommendation.target_type,
    ).exclude(resource=resource)
    if resource.difficulty:
        same_resource_type = same_resource_type.filter(resource__difficulty=resource.difficulty)
    if resource.category_id:
        same_resource_type = same_resource_type.filter(resource__category_id=resource.category_id)

    accepted_similar = same_resource_type.filter(status=ResourceCTARecommendationFeedback.Status.ACCEPTED).count()
    dismissed_similar = same_resource_type.filter(status=ResourceCTARecommendationFeedback.Status.DISMISSED).count()
    ignored_similar = same_resource_type.filter(status=ResourceCTARecommendationFeedback.Status.SHOWN, times_shown__gt=1).count()

    if accepted_similar:
        boost = min(accepted_similar * tuning.similar_accepted_boost, tuning.similar_accepted_cap)
        adjustment += boost
        notes.append(f"+{boost} from accepted {recommendation.target_type_label.lower()} CTAs on similar resources")
    if dismissed_similar:
        penalty = min(dismissed_similar * tuning.similar_dismissed_penalty, tuning.similar_dismissed_cap)
        adjustment -= penalty
        notes.append(f"-{penalty} from dismissed {recommendation.target_type_label.lower()} CTAs on similar resources")
    if ignored_similar:
        penalty = min(ignored_similar * tuning.similar_ignored_penalty, tuning.similar_ignored_cap)
        adjustment -= penalty
        notes.append(f"-{penalty} from ignored {recommendation.target_type_label.lower()} CTAs on similar resources")

    if recommendation.target_lesson:
        same_lesson = ResourceCTARecommendationFeedback.objects.filter(
            target_lesson=recommendation.target_lesson,
            target_type=recommendation.target_type,
        ).exclude(resource=resource)
        accepted_lesson = same_lesson.filter(status=ResourceCTARecommendationFeedback.Status.ACCEPTED).count()
        dismissed_lesson = same_lesson.filter(status=ResourceCTARecommendationFeedback.Status.DISMISSED).count()
        if accepted_lesson:
            boost = min(accepted_lesson * tuning.same_lesson_accepted_boost, tuning.same_lesson_accepted_cap)
            adjustment += boost
            notes.append(f"+{boost} because this lesson has been accepted as a CTA elsewhere")
        if dismissed_lesson:
            penalty = min(dismissed_lesson * tuning.same_lesson_dismissed_penalty, tuning.same_lesson_dismissed_cap)
            adjustment -= penalty
            notes.append(f"-{penalty} because this lesson has been dismissed as a CTA elsewhere")

    adjustment = _bounded(adjustment, tuning.feedback_adjustment_floor, tuning.feedback_adjustment_ceiling)
    return adjustment, notes, feedback_status, times_shown


def _apply_feedback_adjustments(
    resource: LearningResource,
    recommendations: list[ResourceCTARecommendation],
    tuning: RecommendationTuning | None = None,
) -> list[ResourceCTARecommendation]:
    tuning = tuning or RecommendationTuning.get_active()
    adjusted: list[ResourceCTARecommendation] = []
    for recommendation in recommendations:
        base_score = recommendation.score
        adjustment, notes, feedback_status, times_shown = _feedback_adjustment(resource, recommendation, tuning=tuning)
        adjusted.append(
            replace(
                recommendation,
                base_score=base_score,
                feedback_adjustment=adjustment,
                score=base_score + adjustment,
                ranking_notes=tuple(notes),
                feedback_status=feedback_status,
                times_shown=times_shown,
            )
        )
    return adjusted


def build_resource_cta_recommendations(resource: LearningResource, limit: int = 8) -> list[ResourceCTARecommendation]:
    """Return prioritized CTA suggestions that can be shown on the Studio resource page."""
    tuning = RecommendationTuning.get_active()
    recommendations: list[ResourceCTARecommendation] = []
    ranked_lessons = _rank_lessons(resource, limit=limit, tuning=tuning)

    for lesson, score, reasons in ranked_lessons[:5]:
        recommendations.append(
            ResourceCTARecommendation(
                key=f"lesson:{lesson.pk}",
                target_type=ResourceCTA.TargetType.LESSON,
                title=f"Start the matching lesson: {lesson.title}",
                description=(
                    f"Use this resource as the quick reference, then send learners into the full lesson. {lesson.summary or lesson.learning_objective}".strip()
                ),
                button_label="Start the lesson",
                target_lesson=lesson,
                score=score + tuning.lesson_cta_bonus,
                reasons=tuple(reasons),
                already_exists=_cta_exists(resource, ResourceCTA.TargetType.LESSON, lesson),
            )
        )

    quiz_candidates = [(lesson, score, reasons) for lesson, score, reasons in ranked_lessons if lesson.quiz_questions.filter(is_active=True).exists()]
    for lesson, score, reasons in quiz_candidates[:2]:
        recommendations.append(
            ResourceCTARecommendation(
                key=f"quiz:{lesson.pk}",
                target_type=ResourceCTA.TargetType.QUIZ,
                title=f"Try the quiz: {lesson.title}",
                description="Use this when the resource explains a concept and the next best step is a quick knowledge check.",
                button_label="Try the quiz",
                target_lesson=lesson,
                score=score + tuning.quiz_cta_bonus,
                reasons=tuple([*reasons, "quiz CTA available"]),
                already_exists=_cta_exists(resource, ResourceCTA.TargetType.QUIZ, lesson),
            )
        )

    challenge_candidates = [(lesson, score, reasons) for lesson, score, reasons in ranked_lessons if lesson.code_challenges.filter(is_active=True).exists()]
    for lesson, score, reasons in challenge_candidates[:2]:
        recommendations.append(
            ResourceCTARecommendation(
                key=f"challenge:{lesson.pk}",
                target_type=ResourceCTA.TargetType.CHALLENGE,
                title=f"Practice with a challenge: {lesson.title}",
                description="Use this when learners should move from reading the resource to writing code immediately.",
                button_label="Practice now",
                target_lesson=lesson,
                score=score + tuning.challenge_cta_bonus,
                reasons=tuple([*reasons, "challenge CTA available"]),
                already_exists=_cta_exists(resource, ResourceCTA.TargetType.CHALLENGE, lesson),
            )
        )

    if resource.pdf_download_enabled:
        recommendations.append(
            ResourceCTARecommendation(
                key="pdf:download",
                target_type=ResourceCTA.TargetType.PDF,
                title="Download the branded PDF",
                description="Offer the resource as a printable reference or lead magnet when learners want to save it for later.",
                button_label="Download PDF" if not resource.pdf_requires_email else "Unlock the PDF",
                score=tuning.pdf_lead_magnet_bonus if resource.pdf_requires_email else tuning.pdf_open_bonus,
                reasons=("PDF download is enabled", "email gate is enabled" if resource.pdf_requires_email else "open download"),
                already_exists=_cta_exists(resource, ResourceCTA.TargetType.PDF),
            )
        )

    recommendations.append(
        ResourceCTARecommendation(
            key="newsletter:join",
            target_type=ResourceCTA.TargetType.NEWSLETTER,
            title="Get more beginner Python tips",
            description="Invite resource readers onto the Code with Michael email list for weekly lessons and practice prompts.",
            button_label="Join the newsletter",
            score=tuning.newsletter_cta_bonus,
            reasons=("works for every resource", "captures high-intent readers"),
            already_exists=_cta_exists(resource, ResourceCTA.TargetType.NEWSLETTER),
        )
    )

    recommendations = _apply_feedback_adjustments(resource, recommendations, tuning=tuning)
    recommendations.sort(key=lambda item: (-item.score, item.already_exists, item.title.lower()))
    return recommendations[:limit]


def attach_recommendation_feedback(resource: LearningResource, recommendations: list[ResourceCTARecommendation], user=None) -> list[ResourceCTARecommendation]:
    """Record that recommendations were shown and return copies annotated with feedback state."""
    if not recommendations:
        return recommendations

    now = timezone.now()
    user_obj = user if getattr(user, "is_authenticated", False) else None
    feedback_by_key = {
        item.recommendation_key: item
        for item in ResourceCTARecommendationFeedback.objects.filter(
            resource=resource,
            recommendation_key__in=[recommendation.key for recommendation in recommendations],
        )
    }

    annotated: list[ResourceCTARecommendation] = []
    for recommendation in recommendations:
        feedback = feedback_by_key.get(recommendation.key)
        if feedback:
            if feedback.status == ResourceCTARecommendationFeedback.Status.SHOWN:
                feedback.times_shown += 1
                feedback.last_seen_at = now
                feedback.score = recommendation.score
                feedback.title = recommendation.title[:180]
                feedback.reasons = list(recommendation.reasons) + list(recommendation.ranking_notes)
                feedback.updated_by = user_obj or feedback.updated_by
                feedback.save(update_fields=["times_shown", "last_seen_at", "score", "title", "reasons", "updated_by", "updated_at"])
        else:
            feedback = ResourceCTARecommendationFeedback.objects.create(
                resource=resource,
                recommendation_key=recommendation.key,
                target_type=recommendation.target_type,
                target_lesson=recommendation.target_lesson,
                title=recommendation.title[:180],
                score=recommendation.score,
                reasons=list(recommendation.reasons) + list(recommendation.ranking_notes),
                status=ResourceCTARecommendationFeedback.Status.SHOWN,
                first_seen_at=now,
                last_seen_at=now,
                created_by=user_obj,
                updated_by=user_obj,
            )
        annotated.append(
            ResourceCTARecommendation(
                key=recommendation.key,
                target_type=recommendation.target_type,
                title=recommendation.title,
                description=recommendation.description,
                button_label=recommendation.button_label,
                target_lesson=recommendation.target_lesson,
                score=recommendation.score,
                base_score=recommendation.base_score or recommendation.score - recommendation.feedback_adjustment,
                feedback_adjustment=recommendation.feedback_adjustment,
                reasons=recommendation.reasons,
                ranking_notes=recommendation.ranking_notes,
                already_exists=recommendation.already_exists,
                feedback_status=feedback.status,
                feedback_id=feedback.pk,
                times_shown=feedback.times_shown,
            )
        )
    return annotated


def mark_recommendation_dismissed(resource: LearningResource, recommendation_key: str, user=None) -> ResourceCTARecommendationFeedback:
    recommendations = {item.key: item for item in build_resource_cta_recommendations(resource, limit=20)}
    recommendation = recommendations.get(recommendation_key)
    if not recommendation:
        raise ValueError("Recommendation is no longer available for this resource.")
    now = timezone.now()
    user_obj = user if getattr(user, "is_authenticated", False) else None
    feedback, _ = ResourceCTARecommendationFeedback.objects.get_or_create(
        resource=resource,
        recommendation_key=recommendation.key,
        defaults={
            "target_type": recommendation.target_type,
            "target_lesson": recommendation.target_lesson,
            "title": recommendation.title[:180],
            "score": recommendation.score,
            "reasons": list(recommendation.reasons),
            "created_by": user_obj,
        },
    )
    feedback.status = ResourceCTARecommendationFeedback.Status.DISMISSED
    feedback.dismissed_at = now
    feedback.last_seen_at = now
    feedback.updated_by = user_obj
    feedback.save(update_fields=["status", "dismissed_at", "last_seen_at", "updated_by", "updated_at"])
    return feedback


def mark_recommendation_accepted(resource: LearningResource, recommendation: ResourceCTARecommendation, cta: ResourceCTA, user=None) -> ResourceCTARecommendationFeedback:
    now = timezone.now()
    user_obj = user if getattr(user, "is_authenticated", False) else None
    feedback, _ = ResourceCTARecommendationFeedback.objects.get_or_create(
        resource=resource,
        recommendation_key=recommendation.key,
        defaults={
            "target_type": recommendation.target_type,
            "target_lesson": recommendation.target_lesson,
            "title": recommendation.title[:180],
            "score": recommendation.score,
            "reasons": list(recommendation.reasons),
            "created_by": user_obj,
        },
    )
    feedback.status = ResourceCTARecommendationFeedback.Status.ACCEPTED
    feedback.accepted_at = now
    feedback.last_seen_at = now
    feedback.applied_cta = cta
    feedback.updated_by = user_obj
    feedback.save(update_fields=["status", "accepted_at", "last_seen_at", "applied_cta", "updated_by", "updated_at"])
    return feedback


def create_cta_from_recommendation(resource: LearningResource, recommendation_key: str, user=None) -> ResourceCTA:
    recommendations = {item.key: item for item in build_resource_cta_recommendations(resource, limit=20)}
    recommendation = recommendations.get(recommendation_key)
    if not recommendation:
        raise ValueError("Recommendation is no longer available for this resource.")
    if recommendation.already_exists:
        raise ValueError("A matching CTA already exists for this resource.")

    current_max = resource.cta_blocks.order_by("-position").values_list("position", flat=True).first()
    next_position = (current_max or 0) + 1

    cta = ResourceCTA.objects.create(
        resource=resource,
        position=next_position,
        target_type=recommendation.target_type,
        title=recommendation.title[:160],
        description=recommendation.description,
        button_label=recommendation.button_label,
        target_lesson=recommendation.target_lesson,
        is_active=True,
        internal_notes="Created from automatic Studio recommendation.",
    )
    mark_recommendation_accepted(resource, recommendation, cta, user=user)
    return cta
