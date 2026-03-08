import json
import yfinance as yf
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from ..models import Profile, Watchlist

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