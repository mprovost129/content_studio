from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("help/", views.HelpView.as_view(), name="help"),
    path("lessons/", views.LessonListView.as_view(), name="lesson-list"),
    path("lessons/new/", views.LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/<slug:slug>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<slug:slug>/edit/", views.LessonUpdateView.as_view(), name="lesson-update"),
    path("lessons/<slug:slug>/blocks/new/", views.BlockCreateView.as_view(), name="block-create"),
    path("blocks/<int:pk>/edit/", views.BlockUpdateView.as_view(), name="block-update"),
    path("blocks/<int:pk>/delete/", views.BlockDeleteView.as_view(), name="block-delete"),
    path("blocks/<int:pk>/move/<str:direction>/", views.move_block, name="block-move"),
    path("lessons/<slug:slug>/captions/generate/", views.generate_captions, name="caption-generate"),
    path("captions/<int:pk>/edit/", views.CaptionUpdateView.as_view(), name="caption-update"),
    path("lessons/<slug:slug>/graphics/generate/", views.generate_graphic_assets, name="graphic-generate"),
    path("lessons/<slug:slug>/website/preview/", views.website_preview, name="website-preview"),
    path("lessons/<slug:slug>/website/export/", views.create_website_export_view, name="website-export"),
    path("website/exports/<int:pk>/<str:output_format>/", views.download_website_export, name="website-export-download"),
    path("branding/", views.BrandProfileUpdateView.as_view(), name="brand-update"),
]
