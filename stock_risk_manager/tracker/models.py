from django.db import models
from django.contrib.auth.models import User

# 1. EXTENDED USER PROFILE (Wallet & Risk Score)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    risk_score = models.IntegerField(default=0)
    risk_category = models.CharField(max_length=20, default="Neutral") # "Safe" or "Risky"
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)

    def __str__(self):
        return f"{self.user.username} ({self.risk_category})"

# 2. TRANSACTION HISTORY
class Transaction(models.Model):
    TRANSACTION_TYPES = [('BUY', 'Buy'), ('SELL', 'Sell')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price_at_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.ticker}"

# 3. WATCHLIST
class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticker} ({self.user.username})"
    
class DiaryNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title