from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path("tracker/", views.dashboard, name="dashboard"),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('investment_diary/', views.investment_diary, name='investment_diary'),
    path('add-note/', views.add_note, name='add_note'),
    path('edit-note/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete-note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('history/', views.history, name='history'),
    path('dictionary/', views.dictionary, name='dictionary'),  
    path('report/', views.report, name='report'),
    path('profile/', views.profile, name='profile'),
    path('quiz/', views.quiz, name='quiz'),
    path("", views.index, name="index"),
]