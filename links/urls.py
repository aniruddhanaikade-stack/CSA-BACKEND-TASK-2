from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("stats/<str:code>/", views.stats, name="stats"),
    path("<str:code>/", views.go, name="go"),
]
