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

def optimize_portfolio(wallet_capacity, stocks_data):
    """
    0/1 Knapsack Dynamic Programming approach to optimize portfolio allocation.
    wallet_capacity: float or int (total budget)
    stocks_data: list of dicts [{'symbol': 'TCS', 'price': 2500.5, 'target': 2800.0}, ...]
    """
    # 1. Prepare data (cast floats to ints for array indices)
    capacity = int(float(wallet_capacity))
    
    items = []
    for stock in stocks_data:
        try:
            p = float(stock['price'])
            t = float(stock['target'])
            weight = int(p)
            value = int(t - p)
            if value > 0 and weight <= capacity:
                items.append({
                    'symbol': stock['symbol'],
                    'weight': weight,
                    'value': value,
                    'original_price': p,
                    'original_target': t
                })
        except (ValueError, TypeError):
            continue
            
    n = len(items)
    
    # 2. Build the DP matrix (n+1 rows, capacity+1 cols)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        w_i = items[i-1]['weight']
        v_i = items[i-1]['value']
        for w in range(1, capacity + 1):
            if w_i <= w:
                dp[i][w] = max(dp[i-1][w], v_i + dp[i-1][w - w_i])
            else:
                dp[i][w] = dp[i-1][w]
                
    # 3. Traceback to find the selected stocks
    selected_stocks = []
    w = capacity
    total_cost = 0
    total_profit = 0
    
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            item = items[i-1]
            selected_stocks.append(item)
            w -= item['weight']
            total_cost += item['original_price']
            total_profit += (item['original_target'] - item['original_price'])
            
    return {
        'max_profit_projected': round(total_profit, 2),
        'total_cost': round(total_cost, 2),
        'recommended_buys': selected_stocks
    }