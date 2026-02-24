import yfinance as yf
from decimal import Decimal
from django.core.cache import cache

def get_live_inr_price(ticker):
    """
    Fetches live stock price, detects currency, and converts to INR safely.
    Caches the Forex rate for 5 minutes to prevent IP bans.
    Returns: (price_in_inr, original_currency, raw_price)
    """
    stock = yf.Ticker(ticker)
    
    price_float = stock.fast_info.last_price
    if price_float is None:
        raise ValueError(f"Price data unavailable for {ticker}")
        
    raw_price = Decimal(str(price_float))

    try:
        currency = stock.fast_info.currency.upper()
    except AttributeError:
        currency = stock.info.get('currency', 'INR').upper()

    exchange_rate = Decimal('1.0')

    if currency == 'USD':
        # --- THE SHIELD: Check cache before hitting Yahoo ---
        cached_rate = cache.get('USD_INR_RATE')
        
        if cached_rate:
            exchange_rate = cached_rate
            print(f"DEBUG [SERVICES]: Using CACHED Forex Rate: {exchange_rate}")
        else:
            forex = yf.Ticker("INR=X")
            exchange_rate = Decimal(str(forex.fast_info.last_price))
            # Save to memory for 300 seconds (5 minutes)
            cache.set('USD_INR_RATE', exchange_rate, 300)
            print(f"DEBUG [SERVICES]: Fetched FRESH Forex Rate: {exchange_rate}")
            
    elif currency != 'INR':
        raise ValueError(f"Trading in {currency} is unsupported.")

    price_in_inr = round(raw_price * exchange_rate, 2)
    
    return price_in_inr, currency, round(raw_price, 2)