from .services import get_live_inr_price
from django.urls import reverse
from decimal import Decimal
import yfinance as yf # Ensure this is imported at top
import json
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from .models import Profile,Transaction
from .models import Watchlist  
from django.db.models import Sum

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
        ticker = request.POST.get('ticker').upper().strip()

        # 1. Sanitize Quantity to prevent 500 crashes
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity provided.")
            return redirect('dashboard')

        # --- NEW CLEAN SERVICE CALL ---
        try:
            price_in_inr, currency, raw_price = get_live_inr_price(ticker)
            total_cost = price_in_inr * Decimal(quantity)
        except Exception as e:
            print(f"CRITICAL API ERROR on BUY {ticker}: {e}")
            messages.error(request, f"Error checking market data for {ticker}. Please try again.")
            return redirect('dashboard')
        # ------------------------------

        # 6. Check Wallet & Execute
        if user_profile.wallet_balance >= total_cost:
            
            user_profile.wallet_balance -= total_cost
            user_profile.save()

            Transaction.objects.create(
                user=request.user,
                ticker=ticker,
                transaction_type="BUY",
                quantity=quantity,
                price_at_transaction=price_in_inr, # Ledger saved strictly in INR
                total_cost=total_cost,
                timestamp=timezone.now()
            )

            if currency == 'USD':
                messages.success(request, f"Success! Bought {quantity} {ticker} @ ₹{price_in_inr} (Converted from ${round(raw_price, 2)})")
            else:
                messages.success(request, f"Success! Bought {quantity} {ticker} @ ₹{price_in_inr}")
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

def history(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        context = {
            'is_guest': True,
            'message': 'Please login to view your transaction history.'
        }
        return render(request, 'history.html', context)
    
    # Fetch all transactions for this user, newest first
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    
    context = {
        'transactions': transactions,
        'is_guest': False
    }
    return render(request, 'history.html', context)

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

from decimal import Decimal

@login_required
def wallet(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        action = request.POST.get("action")   # ADD / WITHDRAW
        amount = request.POST.get("amount")

        try:
            amount = Decimal(amount)

            if amount <= 0:
                raise ValueError()

        except:
            messages.error(request, "Enter a valid amount")
            return redirect('wallet')

        # ✅ ADD MONEY
        if action == "ADD":
            profile.wallet_balance += amount
            profile.save()
            messages.success(request, f"₹{amount} added successfully!")

        # ✅ WITHDRAW MONEY
        elif action == "WITHDRAW":

            if profile.wallet_balance >= amount:
                profile.wallet_balance -= amount
                profile.save()
                messages.success(request, f"₹{amount} withdrawn successfully!")
            else:
                messages.error(request, "Insufficient wallet balance!")

        return redirect('wallet')

    return render(request, "wallet.html", {"profile": profile})

@login_required
def sell_stock(request):
    if request.method == "POST":
        ticker = request.POST.get("ticker").upper().strip()
        
        # 1. Sanitize Quantity
        try:
            quantity = int(request.POST.get("quantity"))
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
            # Dynamically resolves the base URL, then appends the query parameter
            return redirect(f"{reverse('report')}?ticker={ticker}")

        profile = Profile.objects.get(user=request.user)

        # 2. THE EXPLOIT FIX: Verify Actual Ownership
        # Sum all BUYs, subtract all SELLs to find current holdings
        bought = Transaction.objects.filter(
            user=request.user, ticker=ticker, transaction_type="BUY"
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        sold = Transaction.objects.filter(
            user=request.user, ticker=ticker, transaction_type="SELL"
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        owned_quantity = bought - sold

        if quantity > owned_quantity:
            messages.error(request, f"Trade Rejected: You are trying to sell {quantity} shares, but you only own {owned_quantity} shares of {ticker}.")
            # Dynamically resolves the base URL, then appends the query parameter
            return redirect(f"{reverse('report')}?ticker={ticker}")

        # 3. Fetch Price & Apply Forex (The Currency Fix)
        # 3. Fetch Price & Apply Forex (The Currency Fix)
        # --- NEW CLEAN SERVICE CALL ---
        try:
            price_in_inr, currency, raw_price = get_live_inr_price(ticker)
            total_value = price_in_inr * Decimal(quantity)
        except Exception as e:
            messages.error(request, str(e))
            return redirect(f"{reverse('report')}?ticker={ticker}")
        # ------------------------------

        # 4. Execute Trade & Update Ledger
        profile.wallet_balance += total_value
        profile.save()

        Transaction.objects.create(
            user=request.user,
            ticker=ticker,
            transaction_type="SELL",
            quantity=quantity,
            price_at_transaction=price_in_inr, # Save in INR
            total_cost=total_value
        )

        messages.success(request, f"Successfully sold {quantity} {ticker} @ ₹{price_in_inr} for a total of ₹{total_value}")

    return redirect('dashboard')

def watchlist(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        context = {
            'is_guest': True,
            'message': 'Please login to view and manage your watchlist.'
        }
        return render(request, 'watchlist.html', context)
    
    # 1. Fetch user's watchlist from Database
    saved_stocks = Watchlist.objects.filter(user=request.user).order_by('-added_at')
    
    # If the watchlist is empty, skip the API entirely
    if not saved_stocks:
        return render(request, 'watchlist.html', {'watchlist': [], 'is_guest': False})

    # 2. THE SHIELD: Compile the Grocery List
    # Extract just the symbols into a list: ['AAPL', 'TSLA', 'RELIANCE.NS']
    ticker_symbols = [item.ticker for item in saved_stocks]
    # Join them into a single string: "AAPL TSLA RELIANCE.NS"
    tickers_string = " ".join(ticker_symbols)

    watchlist_data = []

    try:
        # 3. ONE NETWORK CALL. We ask Yahoo once for everything.
        print(f"DEBUG [WATCHLIST]: Fetching batch data for: {tickers_string}")
        batch_data = yf.Tickers(tickers_string)

        # 4. Loop through the local memory, NOT the internet
        for item in saved_stocks:
            try:
                # Access the pre-downloaded data from memory
                stock = batch_data.tickers[item.ticker]
                current_price = stock.fast_info.last_price
                previous_close = stock.fast_info.previous_close
                
                if current_price is None or previous_close is None:
                    raise ValueError("Incomplete data")

                # Calculate Change %
                change_percent = ((current_price - previous_close) / previous_close) * 100
                risk_status = "RISKY" if abs(change_percent) > 2 else "SAFE"

                watchlist_data.append({
                    'id': item.id,
                    'symbol': item.ticker,
                    'price': round(current_price, 2),
                    'change': round(change_percent, 2),
                    'risk': risk_status
                })
            except Exception as e:
                # If one stock fails (e.g. delisted), catch it and let the others load
                print(f"DEBUG [WATCHLIST]: Failed to parse {item.ticker} - {e}")
                watchlist_data.append({
                    'id': item.id,
                    'symbol': item.ticker,
                    'price': "Error",
                    'change': 0,
                    'risk': "Unknown"
                })

    except Exception as e:
        # If the single network call completely fails
        print(f"CRITICAL [WATCHLIST BATCH ERROR]: {e}")
        messages.error(request, "Failed to load live market data. Showing partial list.")
        # Fallback: Still show the tickers so the user can delete them if needed
        for item in saved_stocks:
            watchlist_data.append({
                'id': item.id, 'symbol': item.ticker, 'price': "---", 'change': 0, 'risk': "---"
            })

    return render(request, 'watchlist.html', {'watchlist': watchlist_data, 'is_guest': False})

@login_required
def add_to_watchlist(request):
    if request.method == "POST":
        ticker = request.POST.get('ticker').upper().strip()
        
        # Check if already exists to prevent duplicates
        if not Watchlist.objects.filter(user=request.user, ticker=ticker).exists():
            # Verify if it's a real stock (optional check, good for safety)
            try:
                stock = yf.Ticker(ticker)
                # We check fast_info or info to ensure it exists
                if stock.fast_info.last_price:
                    Watchlist.objects.create(user=request.user, ticker=ticker)
                    messages.success(request, f"Added {ticker} to watchlist.")
            except:
                messages.error(request, f"Could not find stock {ticker}")
        else:
            messages.info(request, f"{ticker} is already in your watchlist.")
    
    # SMART REDIRECT:
    # If the form sent a 'next' parameter (like from report page), go there.
    # Otherwise, go to the default watchlist page.
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
        
    return redirect('watchlist')

@login_required
def remove_from_watchlist(request, item_id):
    # Get the item or 404 (Security: Ensure it belongs to request.user)
    try:
        item = Watchlist.objects.get(id=item_id, user=request.user)
        item.delete()
        messages.success(request, "Stock removed.")
    except Watchlist.DoesNotExist:
        messages.error(request, "Item not found.")
        
    return redirect('watchlist')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UpdateProfileForm


from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def update_profile(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")

        user = request.user

        # ✅ VERIFY OLD PASSWORD (MANDATORY)
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("update_profile")

        # ✅ UPDATE BASIC DETAILS
        user.username = username
        user.email = email

        # ✅ CHANGE PASSWORD (IF PROVIDED)
        if new_password:
            user.set_password(new_password)

        user.save()

        # ✅ KEEP USER LOGGED IN (CRITICAL)
        update_session_auth_hash(request, user)

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "update_profile.html")

@login_required
def reset_account(request):
    # SECURITY: Only accept POST requests to prevent accidental/malicious URL triggering
    if request.method == "POST":
        # 1. Wipe the immutable ledger for this specific user
        Transaction.objects.filter(user=request.user).delete()

        # 2. Reset the bank
        profile = Profile.objects.get(user=request.user)
        profile.wallet_balance = Decimal('10000.00')
        profile.save()

        messages.success(request, "SYSTEM RESET: Your ledger has been wiped and wallet restored to ₹10,000.00.")
        return redirect('history')
    
    # If they try to navigate here via the URL bar (GET request), kick them away
    return redirect('history')
