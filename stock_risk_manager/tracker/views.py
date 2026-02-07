from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

def dashboard(request): 
    return render(request, "index.html")

def watchlist(request):
    return render(request, 'watchlist.html')

def history(request):
    return render(request, 'history.html')

def index(request):
    return render(request,'index.html')