from .auth_views import *
from .trading_views import *
from .stock_views import *
from .watchlist_views import *
from .diary_views import *
from .admin_views import *
from .misc_views import *

__all__ = [
    # Auth views
    'register', 'login', 'logout', 'profile', 'update_profile',
    # Trading views
    'dashboard', 'sell_stock', 'wallet', 'reset_account',
    # Stock views
    'report',
    # Watchlist views
    'watchlist', 'add_to_watchlist', 'remove_from_watchlist',
    # Diary views
    'investment_diary', 'add_note', 'edit_note', 'delete_note',
    # Admin views
    'admin_dashboard', 'manage_users', 'manage_dictionary', 'delete_term', 'update_term', 'delete_user',
    # Misc views
    'index', 'guest', 'quiz', 'history', 'dictionary'
]