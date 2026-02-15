from decimal import Decimal
import yfinance as yf # Ensure this is imported at top
import json
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from .models import Profile,Transaction # Make sure this is imported at the top

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

@login_required
def dashboard(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        ticker = request.POST.get('ticker')
        quantity = int(request.POST.get('quantity'))

        try:
            # 1. Fetch Live Price
            stock = yf.Ticker(ticker)
            
            # fast_info is often faster/more reliable than .info for price
            price_float = stock.fast_info.last_price 
            
            if price_float is None:
                # Fallback to history if fast_info fails
                data = stock.history(period="1d")
                if data.empty:
                    raise ValueError("No data found")
                price_float = data['Close'].iloc[-1]

            # 2. THE FIX: Convert Float to Decimal for Money Math
            current_price = Decimal(str(price_float))  # Convert to string first to avoid float artifacts
            
            # Round to 2 decimal places (standard for currency)
            current_price = round(current_price, 2)

        except Exception as e:
            messages.error(request, f"Error checking price for {ticker}. Try again.")
            return redirect('dashboard')

        # 3. Calculate Cost (Now both are Decimals)
        total_cost = current_price * Decimal(quantity)

        # 4. Check Wallet & Buy
        if user_profile.wallet_balance >= total_cost:
            
            # A. Deduct Money (Decimal - Decimal = OK!)
            user_profile.wallet_balance -= total_cost
            user_profile.save()

            # B. Save Transaction
            Transaction.objects.create(
                user=request.user,
                ticker=ticker,
                transaction_type="BUY",
                quantity=quantity,
                price_at_transaction=current_price,
                total_cost=total_cost,
                timestamp=timezone.now()
            )

            # Success Message with ₹ Symbol
            messages.success(request, f"Success! Bought {quantity} {ticker} @ ₹{current_price}")
        else:
            messages.error(request, f"Insufficient funds! Needed ₹{total_cost}, have ₹{user_profile.wallet_balance}")

        return redirect('dashboard')

    # GET Request (Normal Page Load)
    context = {
        'profile': user_profile,
        'wallet_balance': user_profile.wallet_balance,
        'user_risk': user_profile.risk_category
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

@login_required
def report(request):
    # 1. Get Ticker from URL (e.g., /report/?ticker=RELIANCE.NS)
    ticker = request.GET.get('ticker', 'RELIANCE.NS').upper().strip()

    try:
        # 2. Initialize API
        stock = yf.Ticker(ticker)
        
        # We use .info to get the main data. 
        # Note: Sometimes .info is slow, but it contains the 'longBusinessSummary' we need.
        info = stock.info

        # 3. Check if valid (Current Price is usually missing for invalid stocks)
        if 'currentPrice' not in info:
            messages.error(request, f"Could not find stock '{ticker}'. Try adding .NS (e.g. TCS.NS)")
            return redirect('dashboard')

        # 4. Determine Currency Symbol (₹ for India, $ for US)
        currency_code = info.get('currency', 'INR')
        currency_symbol = '₹' if currency_code == 'INR' else '$'

        # 5. Prepare Data for Template
        stock_data = {
            'symbol': ticker,
            'name': info.get('longName', ticker),
            'current_price': info.get('currentPrice'),
            'currency': currency_code,
            'currency_symbol': currency_symbol,  # <--- vital for display
            'summary': info.get('longBusinessSummary', 'No summary available.'),
            'market_cap': info.get('marketCap', 'N/A'),
            'high_52': info.get('fiftyTwoWeekHigh'),
            'low_52': info.get('fiftyTwoWeekLow'),
            'recommendation': info.get('recommendationKey', 'hold').upper(),
            'target_price': info.get('targetMeanPrice', 'N/A'),
        }

        # 6. Fetch History for Chart (1 Year)
        hist = stock.history(period="1y")
        
        # Convert Timestamp index to string dates for Chart.js
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        prices = hist['Close'].tolist()

        # 7. Calculate Risk/Upside Logic manually
        upside = 0
        if stock_data['target_price'] != 'N/A' and stock_data['current_price']:
            try:
                upside = ((stock_data['target_price'] - stock_data['current_price']) / stock_data['current_price']) * 100
            except:
                upside = 0
        
        stock_data['upside'] = round(upside, 2)

        context = {
            'stock': stock_data,
            'chart_dates': json.dumps(dates),  # Pass as JSON string for JS
            'chart_prices': json.dumps(prices) # Pass as JSON string for JS
        }

        return render(request, 'report.html', context)

    except Exception as e:
        print(f"API Error: {e}")
        messages.error(request, "Error connecting to Stock Market API. Please try again.")
        return redirect('dashboard')

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


def guest(request):
    """Render the public guest homepage (guest.html)."""
    return render(request, 'guest.html')

from django.shortcuts import render, redirect, get_object_or_404
from .models import DiaryNote

@login_required
def investment_diary(request):
    notes = DiaryNote.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'investment_diary.html', {'notes': notes})


@login_required
def add_note(request):
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']

        DiaryNote.objects.create(user=request.user, title=title, content=content)
        return redirect('investment_diary')

    return redirect('investment_diary')


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(DiaryNote, id=note_id, user=request.user)

    if request.method == 'POST':
        note.title = request.POST['title']
        note.content = request.POST['content']
        note.save()
        return redirect('investment_diary')

    return render(request, 'edit_note.html', {'note': note})


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(DiaryNote, id=note_id, user=request.user)
    note.delete()
    return redirect('investment_diary')