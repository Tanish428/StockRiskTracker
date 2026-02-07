from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [
    path("tracker/", views.dashboard, name="dashboard"),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('history/', views.history, name='history'),
    path('dictionary/', views.dictionary, name='dictionary'),   
    path("", views.index, name="index"),
]