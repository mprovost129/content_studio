from django.urls import path

from .views import LearnerProfileView, LearnerRegistrationView

app_name = "users"

urlpatterns = [
    path("signup/", LearnerRegistrationView.as_view(), name="signup"),
    path("profile/", LearnerProfileView.as_view(), name="profile"),
]
