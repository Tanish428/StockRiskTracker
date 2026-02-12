from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login

# --- 1. REAL LOGIN LOGIC ---
def login(request):
    if request.method == 'POST':
        # Get data from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if user exists
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')  # Redirects to the dashboard view below
        else:
            messages.error(request, "Invalid username or password")
            
    return render(request, 'login.html')

# --- LOGOUT VIEW ---
def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('login')

# --- 2. PLACEHOLDER VIEWS (So urls.py doesn't crash) ---

def index(request):
    return render(request, 'index.html')

@login_required  # Protect this so only logged-in users can see it
def dashboard(request):
    # Provide the user's profile, wallet balance and risk category to the template
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    context = {
        'profile': user_profile,
        'wallet_balance': user_profile.wallet_balance,
        'user_risk': (user_profile.risk_category or '').upper()
    }
    return render(request, "index.html", context)

from django.contrib.auth.models import User
from .models import Profile

def register(request):
    if request.method == "POST":
        # ... (Get data and validation logic remains the same) ...
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        # Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Create Profile
        Profile.objects.create(user=user, wallet_balance=10000.00)

        # --- NEW PART START ---
        # 1. Auto-login the user immediately
        auth_login(request, user)
        
        # 2. Redirect to the Quiz instead of Login
        messages.success(request, "Account created! Let's check your risk profile.")
        return redirect('quiz')
        # --- NEW PART END ---

    return render(request, 'register.html')

def watchlist(request):
    return render(request, 'watchlist.html')

def history(request):
    return render(request, 'history.html')

def dictionary(request):
    return render(request, 'dictionary.html')

def report(request):
    return render(request, 'report.html')

from .models import Profile # Make sure this is imported at the top

@login_required
def profile(request):
    # 1. Get the user's profile (or create one if it doesn't exist)
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    # 2. Send data to the template
    context = {
        'profile': user_profile
    }
    return render(request, 'profile.html', context)

@login_required
def quiz(request):
    if request.method == "POST":
        # Get the result from the HTML form
        score = request.POST.get('risk_score')
        category = request.POST.get('risk_category')

        # Update the User's Profile
        profile = Profile.objects.get(user=request.user)
        profile.risk_score = int(score)
        profile.risk_category = category
        profile.save()

        messages.success(request, f"Profile Updated! You are a {category} investor.")
        return redirect('dashboard') # Redirect to Dashboard (Logic: They are already logged in)

    return render(request, 'quiz.html')