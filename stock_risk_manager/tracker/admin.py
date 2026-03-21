from django.contrib import admin
from .models import Dictionary, Profile, Transaction, Watchlist, DiaryNote, QuizQuestion

# Register your models here so they show up in the Admin Panel
admin.site.register(Profile)
admin.site.register(Transaction)
admin.site.register(Watchlist)
admin.site.register(DiaryNote)
admin.site.register(Dictionary)
admin.site.register(QuizQuestion)