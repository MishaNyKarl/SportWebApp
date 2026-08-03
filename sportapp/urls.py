from django.conf import settings
from django.contrib import admin
from django.urls import path, include

_prefix = f'{settings.URL_PREFIX}/' if settings.URL_PREFIX else ''

urlpatterns = [
    path(f'{_prefix}admin/', admin.site.urls),
    path(_prefix, include('tracker.urls')),
]
