from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path("tracker/", views.dashboard, name="dashboard"),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('history/', views.history, name='history'),
    path('dictionary/', views.dictionary, name='dictionary'),  
    path('report/', views.report, name='report'),
    path('profile/', views.profile, name='profile'),
    path('quiz/', views.quiz, name='quiz'),
    path("", views.index, name="index"),
]