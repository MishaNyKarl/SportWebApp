from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.timer_view, name='timer'),
    path('counter/', views.counter_view, name='counter'),
    path('counter/<int:pk>/delete/', views.delete_set, name='delete_set'),
    path('clock/', views.clock_view, name='clock'),
    path('stats/', views.stats_view, name='stats'),
    path('reminders/', views.reminders_view, name='reminders'),
    path('reminders/<int:pk>/toggle/', views.toggle_reminder, name='toggle_reminder'),
    path('reminders/<int:pk>/delete/', views.delete_reminder, name='delete_reminder'),
    path('api/reminders/', views.reminders_api, name='reminders_api'),
]
