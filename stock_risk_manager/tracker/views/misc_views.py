from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Transaction, Dictionary, Profile, QuizQuestion

def index(request):
    return render(request, 'index.html')

def guest(request):
    return render(request, 'guest.html')

@login_required
def quiz(request):
    """Risk Assessment Quiz logic."""
    if request.method == "POST":
        score = request.POST.get('risk_score')
        category = request.POST.get('risk_category')

        profile = Profile.objects.get(user=request.user)
        profile.risk_score = int(score)
        profile.risk_category = category
        profile.save()

        messages.success(request, f"Profile Updated! You are a {category} investor.")
        return redirect('dashboard')

    # Get 3 random questions from database
    questions = QuizQuestion.objects.order_by('?')[:3]
    return render(request, 'quiz.html', {'questions': questions})

def history(request):
    """Displays all past transactions."""
    if not request.user.is_authenticated:
        return render(request, 'history.html', {'is_guest': True, 'message': 'Please login to view history.'})
    
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'history.html', {'transactions': transactions, 'is_guest': False})

def dictionary(request):
    terms = Dictionary.objects.all().order_by('term')
    return render(request, 'dictionary.html', {'terms': terms})