from decimal import Decimal
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from ..models import Profile, Transaction
from ..services import get_live_inr_price

@login_required
def dashboard(request):
    """Main hub for buying stocks and viewing balance."""
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        ticker = request.POST.get('ticker').upper().strip() #standardizes the stock symbol.(reliance.nse -> RELIANCE.NS)

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

        #This fetches the current user's profile from the database.
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