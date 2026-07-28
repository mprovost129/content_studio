from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('robots.txt', views.robots_txt, name='robots'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('feed.xml', views.feed, name='feed'),
]
