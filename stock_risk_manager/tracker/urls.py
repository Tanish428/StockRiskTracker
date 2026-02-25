from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('guest/', views.guest, name='guest'),
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
    path('wallet/', views.wallet, name='wallet'),
    path('sell/', views.sell_stock, name='sell_stock'),
    path('watchlist/add/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/<int:item_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('reset-account/', views.reset_account, name='reset_account'),
    
]