from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ..models import Profile
from ..forms import UpdateProfileForm

def register(request):
    """Handles new user creation and initializes their wallet."""
    if request.method == "POST":
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

        # Create Profile with initial virtual balance
        Profile.objects.create(user=user, wallet_balance=10000.00)

        # Auto-login and redirect to Risk Quiz
        auth_login(request, user)
        messages.success(request, "Account created! Let's check your risk profile.")
        return redirect('quiz')

    return render(request, 'register.html')

def login(request):
    """Standard login logic."""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        # user found and credentials correct
        if user is not None:
            auth_login(request, user)

            # check if admin
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def logout(request):
    """Logs out user and redirects to login page."""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('login')

@login_required
def profile(request):
    """Displays user's profile and risk category."""
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    context = {'profile': user_profile}
    return render(request, 'profile.html', context)

@login_required
def update_profile(request):
    """Allows user to update username, email, or password."""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        user = request.user

        # Verify password before allowing changes
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("update_profile")

        user.username = username
        user.email = email

        if new_password:
            user.set_password(new_password)

        user.save()
        # Keep the session active after password change
        update_session_auth_hash(request, user)

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "update_profile.html")