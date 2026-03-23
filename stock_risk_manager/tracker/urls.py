from django.urls import path

from . import views
from .views import dashboard
urlpatterns = [

    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
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
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-dictionary/', views.manage_dictionary, name='manage_dictionary'),
    path('update-term/<int:term_id>/', views.update_term, name='update_term'),
    path('delete-term/<int:term_id>/', views.delete_term, name='delete_term'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('manage-quiz/', views.manage_quiz, name='manage_quiz'),
    path('delete-quiz-question/<int:question_id>/', views.delete_quiz_question, name='delete_quiz_question'),
    path('update-quiz-question/<int:question_id>/', views.update_quiz_question, name='update_quiz_question'),
]