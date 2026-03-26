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

import json
from django.http import JsonResponse
from ..services import optimize_portfolio

@login_required
def optimize_portfolio_api(request):
    """API endpoint to run 0/1 Knapsack portfolio optimization."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            capital = data.get('capital')
            tickers = data.get('tickers', [])
            
            if not capital or not tickers:
                return JsonResponse({"error": "Missing capital or tickers"}, status=400)
                
            stocks_data = []
            
            if tickers:
                tickers_string = " ".join(tickers)
                batch_data = yf.Tickers(tickers_string)
                for ticker in tickers:
                    try:
                        stock = batch_data.tickers[ticker]
                        current_price = stock.fast_info.last_price
                        
                        # info can be slow, but required for targetMeanPrice
                        info = stock.info
                        target_price = info.get('targetMeanPrice')
                        
                        # Currency conversion to INR
                        try:
                            currency = stock.fast_info.currency.upper()
                        except AttributeError:
                            currency = info.get('currency', 'INR').upper()
                            
                        exchange_rate = 1.0
                        if currency == 'USD':
                            from django.core.cache import cache
                            cached_rate = cache.get('USD_INR_RATE')
                            if cached_rate:
                                exchange_rate = float(cached_rate)
                            else:
                                forex = yf.Ticker("INR=X")
                                exchange_rate = float(forex.fast_info.last_price)
                                cache.set('USD_INR_RATE', exchange_rate, 300)
                                
                        current_price = current_price * exchange_rate
                        
                        # Fallback if no target is provided by analysts:
                        if target_price is None:
                            target_price = current_price * 1.10 # 10% default target
                        else:
                            target_price = target_price * exchange_rate
                            
                        if current_price and target_price:
                            stocks_data.append({
                                'symbol': ticker,
                                'price': round(current_price, 2),
                                'target': round(target_price, 2)
                            })
                    except Exception as e:
                        print(f"Error fetching data for {ticker}: {e}")
            
            result = optimize_portfolio(capital, stocks_data)
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)