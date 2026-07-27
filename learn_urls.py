from django.urls import path

from studio import views

app_name = "learn"

urlpatterns = [
    path("", views.PublicLearnHomeView.as_view(), name="home"),
    path("dashboard/", views.LearnerDashboardView.as_view(), name="dashboard"),
    path("activity/", views.LearnerActivityView.as_view(), name="activity"),
    path("newsletter/signup/", views.newsletter_signup, name="newsletter-signup"),
    path("lessons/", views.PublicLessonListView.as_view(), name="lesson-list"),
    path("paths/<slug:slug>/", views.PublicSeriesDetailView.as_view(), name="series-detail"),
    path("playground/", views.PublicPlaygroundView.as_view(), name="playground"),
    path("resources/", views.PublicResourceListView.as_view(), name="resource-list"),
    path("resources/<slug:slug>/unlock-pdf/", views.PublicResourcePDFGateView.as_view(), name="resource-pdf-gate"),
    path("resources/<slug:resource_slug>/cta/<int:pk>/", views.PublicResourceCTAClickView.as_view(), name="resource-cta-click"),
    path("resources/<slug:slug>/download.pdf", views.PublicResourcePDFDownloadView.as_view(), name="resource-pdf"),
    path("resources/<slug:slug>/", views.PublicResourceDetailView.as_view(), name="resource-detail"),
    path("quiz/<int:question_pk>/submit/", views.submit_quiz_answer, name="quiz-submit"),
    path("challenge/<int:challenge_pk>/submit/", views.submit_challenge_attempt, name="challenge-submit"),
    path("challenge-attempts/<int:pk>/", views.ChallengeAttemptDetailView.as_view(), name="challenge-attempt-detail"),
    path("<slug:slug>/complete/", views.mark_lesson_complete, name="lesson-complete"),
    path("<slug:slug>/", views.PublicLessonDetailView.as_view(), name="lesson-detail"),
]
