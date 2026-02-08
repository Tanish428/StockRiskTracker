from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')

def dashboard(request): 
    return render(request, "index.html")

def watchlist(request):
    return render(request, 'watchlist.html')

def history(request):
    return render(request, 'history.html')

def dictionary(request):
    return render(request, 'dictionary.html')

def report(request):
    return render(request, 'report.html')

def profile(request):
    return render(request, 'profile.html')

def quiz(request):
    return render(request, 'quiz.html')

def index(request):
    return render(request,'index.html')