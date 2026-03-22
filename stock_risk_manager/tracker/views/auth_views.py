from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ..models import Profile
from ..forms import UpdateProfileForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def register(request):
    """Handles secure user registration"""

    if request.method == "POST":
        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 1️⃣ Check empty fields
        if not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required", extra_tags="register")
            return render(request, 'register.html')
        # 2️⃣ Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match", extra_tags="register")
            return render(request, 'register.html')
        # 3️⃣ Username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken", extra_tags="register")
            return render(request, 'register.html')
        # 4️⃣ Email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered", extra_tags="register")
            return render(request, 'register.html')
        # 5️⃣ Strong password validation (VERY IMPORTANT)
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error, extra_tags="register")
            return render(request, 'register.html')
        # 6️⃣ Create User (password automatically hashed)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 7️⃣ Create Profile with wallet
        Profile.objects.create(user=user, wallet_balance=10000.00)

        # 8️⃣ Auto login
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


from django.contrib.auth.hashers import check_password
@login_required
def update_profile(request):

    if request.method == "POST":
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")

        user = request.user

        # ✅ 1. Check empty fields
        if not username or not email or not old_password:
            messages.error(request, "All fields are required")
            return render(request, "update_profile.html")

        # ✅ 2. Check old password is correct
        if not check_password(old_password, user.password):
            messages.error(request, "Old password is incorrect")
            return render(request, "update_profile.html")

        # ✅ 3. Check username uniqueness
        if User.objects.exclude(id=user.id).filter(username=username).exists():
            messages.error(request, "Username already taken")
            return render(request, "update_profile.html")

        # ✅ 4. Check email uniqueness
        if User.objects.exclude(id=user.id).filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "update_profile.html")

        # ✅ 5. Update username & email
        user.username = username
        user.email = email

        # ✅ 6. Handle password change (OPTIONAL but safe)
        if new_password:
            try:
                validate_password(new_password)
                user.set_password(new_password)

                # IMPORTANT → Keep user logged in
                update_session_auth_hash(request, user)

            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, "update_profile.html")

        # ✅ 7. Save changes
        user.save()

        messages.success(request, "Profile updated successfully")
        return redirect("profile")

    return render(request, "update_profile.html")