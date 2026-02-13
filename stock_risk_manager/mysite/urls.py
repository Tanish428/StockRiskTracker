
from django.contrib import admin
from django.urls import path, include
from tracker import views as tracker_views

urlpatterns = [
    # Root serves guest homepage
    path('', tracker_views.guest, name='guest'),
    # Expose dictionary at top-level so guests visit /dictionary (not /tracker/dictionary)
    path('dictionary/', tracker_views.dictionary, name='dictionary'),
    path("tracker/", include("tracker.urls")),
    path('admin/', admin.site.urls),
]
