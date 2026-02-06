from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [
    path("tracker/", views.dashboard, name="dashboard"),
    path("", views.index, name="index"),
]