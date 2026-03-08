import yfinance as yf
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Watchlist

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