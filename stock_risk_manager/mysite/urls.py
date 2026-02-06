
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path("tracker/",include("tracker.urls")),
    path('admin/', admin.site.urls),
]
