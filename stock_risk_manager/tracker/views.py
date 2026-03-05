import json
import yfinance as yf
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.core.cache import cache

# Local imports from your app
from .models import Profile, Transaction, Watchlist, DiaryNote
from .services import get_live_inr_price
from .forms import UpdateProfileForm

# ==========================================
# 1. AUTHENTICATION & PROFILE VIEWS
# ==========================================

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

        if user is not None:
            auth_login(request, user)
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

# ==========================================
# 2. CORE TRADING & WALLET VIEWS
# ==========================================

@login_required
def dashboard(request):
    """Main hub for buying stocks and viewing balance."""
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        ticker = request.POST.get('ticker').upper().strip()

        # Sanitize Quantity
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity provided.")
            return redirect('dashboard')

        # Fetch live price via service
        try:
            price_in_inr, currency, raw_price = get_live_inr_price(ticker)
            total_cost = price_in_inr * Decimal(quantity)
        except Exception as e:
            print(f"CRITICAL API ERROR on BUY {ticker}: {e}")
            messages.error(request, f"Error checking market data for {ticker}. Please try again.")
            return redirect('dashboard')

        # Transaction Execution
        if user_profile.wallet_balance >= total_cost:
            user_profile.wallet_balance -= total_cost
            user_profile.save()

            Transaction.objects.create(
                user=request.user,
                ticker=ticker,
                transaction_type="BUY",
                quantity=quantity,
                price_at_transaction=price_in_inr,
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

    context = {
        'profile': user_profile,
        'wallet_balance': user_profile.wallet_balance,
        'user_risk': user_profile.risk_category
    }
    return render(request, "index.html", context)

@login_required
def sell_stock(request):
    """Handles logic for selling owned shares."""
    if request.method == "POST":
        ticker = request.POST.get("ticker").upper().strip()
        
        try:
            quantity = int(request.POST.get("quantity"))
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
            return redirect(f"{reverse('report')}?ticker={ticker}")

        profile = Profile.objects.get(user=request.user)

        # Verify Ownership (Total Buy - Total Sell)
        bought = Transaction.objects.filter(
            user=request.user, ticker=ticker, transaction_type="BUY"
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        sold = Transaction.objects.filter(
            user=request.user, ticker=ticker, transaction_type="SELL"
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        owned_quantity = bought - sold

        if quantity > owned_quantity:
            messages.error(request, f"Trade Rejected: You only own {owned_quantity} shares of {ticker}.")
            return redirect(f"{reverse('report')}?ticker={ticker}")

        # Fetch current price for sale
        try:
            price_in_inr, currency, raw_price = get_live_inr_price(ticker)
            total_value = price_in_inr * Decimal(quantity)
        except Exception as e:
            messages.error(request, str(e))
            return redirect(f"{reverse('report')}?ticker={ticker}")

        # Update Wallet and Ledger
        profile.wallet_balance += total_value
        profile.save()

        Transaction.objects.create(
            user=request.user,
            ticker=ticker,
            transaction_type="SELL",
            quantity=quantity,
            price_at_transaction=price_in_inr,
            total_cost=total_value
        )

        messages.success(request, f"Successfully sold {quantity} {ticker} @ ₹{price_in_inr}")

    return redirect('dashboard')

@login_required
def wallet(request):
    """Deposit or Withdraw virtual currency."""
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        amount = request.POST.get("amount")

        try:
            amount = Decimal(amount)
            if amount <= 0: raise ValueError()
        except:
            messages.error(request, "Enter a valid amount")
            return redirect('wallet')

        if action == "ADD":
            profile.wallet_balance += amount
            profile.save()
            messages.success(request, f"₹{amount} added successfully!")

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
def reset_account(request):
    """Wipes all transaction history and resets balance to ₹10,000."""
    if request.method == "POST":
        Transaction.objects.filter(user=request.user).delete()
        profile = Profile.objects.get(user=request.user)
        profile.wallet_balance = Decimal('10000.00')
        profile.save()

        messages.success(request, "SYSTEM RESET: Ledger wiped and wallet restored.")
        return redirect('history')
    
    return redirect('history')

# ==========================================
# 3. STOCK ANALYSIS & WATCHLIST
# ==========================================

@login_required
def report(request):
    """Detailed stock analysis with personalized risk assessment."""
    ticker = request.GET.get('ticker', 'RELIANCE.NS').upper().strip()

    try:
        # Check Cache to reduce API overhead
        cache_key = f"stock_report_data_{ticker}"
        cached_data = cache.get(cache_key)

        if cached_data:
            info = cached_data['info']
            dates = cached_data['dates']
            prices = cached_data['prices']
        else:
            stock = yf.Ticker(ticker)
            info = stock.info 
            hist = stock.history(period="1y")
            dates = hist.index.strftime('%Y-%m-%d').tolist()
            prices = hist['Close'].tolist()

            cache.set(cache_key, {'info': info, 'dates': dates, 'prices': prices}, 900)

        if 'currentPrice' not in info:
            messages.error(request, f"Could not find stock '{ticker}'.")
            return redirect('dashboard')

        currency_code = info.get('currency', 'INR')
        currency_symbol = '₹' if currency_code == 'INR' else '$'

        stock_data = {
            'symbol': ticker,
            'name': info.get('longName', ticker),
            'current_price': info.get('currentPrice'),
            'currency': currency_code,
            'currency_symbol': currency_symbol,
            'summary': info.get('longBusinessSummary', 'No summary available.'),
            'market_cap': info.get('marketCap', 'N/A'),
            'high_52': info.get('fiftyTwoWeekHigh'),
            'low_52': info.get('fiftyTwoWeekLow'),
            'recommendation': info.get('recommendationKey', 'hold').upper(),
            'target_price': info.get('targetMeanPrice', 'N/A'),
        }

        # Calculate Upside
        upside = 0
        if stock_data['target_price'] != 'N/A' and stock_data['current_price']:
            try:
                upside = ((stock_data['target_price'] - stock_data['current_price']) / stock_data['current_price']) * 100
            except: upside = 0
        stock_data['upside'] = round(upside, 2)

        # Risk Analysis Logic
        profile, _ = Profile.objects.get_or_create(user=request.user)
        user_risk_profile = profile.risk_category 

        try:
            high_52 = float(stock_data.get('high_52') or 0)
            low_52 = float(stock_data.get('low_52') or 0)
            volatility_swing = ((high_52 - low_52) / low_52) * 100 if low_52 > 0 else 0
        except: volatility_swing = 0

        stock_inherent_risk = "Risky" if volatility_swing > 60 else "Safe"

        # Compatibility Matrix
        if user_risk_profile == "Safe":
            if stock_inherent_risk == "Risky":
                stock_data.update({'verdict_title': "HIGH DANGER", 'verdict_msg': f"Violates your conservative profile ({round(volatility_swing)}% swing).", 'verdict_color': "#e74c3c"})
            else:
                stock_data.update({'verdict_title': "STRONG MATCH", 'verdict_msg': "Aligns perfectly with your low-risk strategy.", 'verdict_color': "#2ecc71"})
        elif user_risk_profile == "Risky":
            if stock_inherent_risk == "Risky":
                stock_data.update({'verdict_title': "STRATEGIC MATCH", 'verdict_msg': "High volatility aligns with your aggressive growth strategy.", 'verdict_color': "#2ecc71"})
            else:
                stock_data.update({'verdict_title': "LOW VOLATILITY", 'verdict_msg': "Safe asset, but may underperform aggressive expectations.", 'verdict_color': "#f39c12"})
        else:
            stock_data.update({'verdict_title': "NEUTRAL STANCE", 'verdict_msg': "Take the Risk Quiz to unlock personalized insights.", 'verdict_color': "#3498db"})

        context = {'stock': stock_data, 'chart_dates': json.dumps(dates), 'chart_prices': json.dumps(prices)}
        return render(request, 'report.html', context)

    except Exception as e:
        messages.error(request, "Error connecting to Stock Market API.")
        return redirect('dashboard')

def watchlist(request):
    """Displays real-time updates for user's watched stocks."""
    if not request.user.is_authenticated:
        return render(request, 'watchlist.html', {'is_guest': True, 'message': 'Please login to manage watchlist.'})
    
    saved_stocks = Watchlist.objects.filter(user=request.user).order_by('-added_at')
    if not saved_stocks:
        return render(request, 'watchlist.html', {'watchlist': [], 'is_guest': False})

    ticker_symbols = [item.ticker for item in saved_stocks]
    tickers_string = " ".join(ticker_symbols)
    watchlist_data = []

    try:
        batch_data = yf.Tickers(tickers_string)
        for item in saved_stocks:
            try:
                stock = batch_data.tickers[item.ticker]
                current_price = stock.fast_info.last_price
                previous_close = stock.fast_info.previous_close
                change_percent = ((current_price - previous_close) / previous_close) * 100
                
                watchlist_data.append({
                    'id': item.id, 'symbol': item.ticker, 'price': round(current_price, 2),
                    'change': round(change_percent, 2), 'risk': "RISKY" if abs(change_percent) > 2 else "SAFE"
                })
            except:
                watchlist_data.append({'id': item.id, 'symbol': item.ticker, 'price': "Error", 'change': 0, 'risk': "Unknown"})
    except Exception as e:
        messages.error(request, "Failed to load live market data.")
        for item in saved_stocks:
            watchlist_data.append({'id': item.id, 'symbol': item.ticker, 'price': "---", 'change': 0, 'risk': "---"})

    return render(request, 'watchlist.html', {'watchlist': watchlist_data, 'is_guest': False})

@login_required
def add_to_watchlist(request):
    """Adds a ticker to the user's personal watchlist."""
    if request.method == "POST":
        ticker = request.POST.get('ticker').upper().strip()
        if not Watchlist.objects.filter(user=request.user, ticker=ticker).exists():
            try:
                stock = yf.Ticker(ticker)
                if stock.fast_info.last_price:
                    Watchlist.objects.create(user=request.user, ticker=ticker)
                    messages.success(request, f"Added {ticker} to watchlist.")
            except:
                messages.error(request, f"Could not find stock {ticker}")
        else:
            messages.info(request, f"{ticker} is already in your watchlist.")
    
    next_url = request.POST.get('next')
    return redirect(next_url) if next_url else redirect('watchlist')

@login_required
def remove_from_watchlist(request, item_id):
    """Removes a ticker from the user's watchlist."""
    try:
        item = Watchlist.objects.get(id=item_id, user=request.user)
        item.delete()
        messages.success(request, "Stock removed.")
    except Watchlist.DoesNotExist:
        messages.error(request, "Item not found.")
    return redirect('watchlist')

# ==========================================
# 4. UTILITY & MISC VIEWS
# ==========================================

def index(request):
    return render(request, 'index.html')

def guest(request):
    return render(request, 'guest.html')

def dictionary(request):
    return render(request, 'dictionary.html')

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

    return render(request, 'quiz.html')

def history(request):
    """Displays all past transactions."""
    if not request.user.is_authenticated:
        return render(request, 'history.html', {'is_guest': True, 'message': 'Please login to view history.'})
    
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'history.html', {'transactions': transactions, 'is_guest': False})

# ==========================================
# 5. INVESTMENT DIARY (CRUD)
# ==========================================

@login_required
def investment_diary(request):
    notes = DiaryNote.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'investment_diary.html', {'notes': notes})

@login_required
def add_note(request):
    if request.method == 'POST':
        DiaryNote.objects.create(user=request.user, title=request.POST['title'], content=request.POST['content'])
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