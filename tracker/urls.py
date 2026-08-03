from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.timer_view, name='timer'),
    path('counter/', views.counter_view, name='counter'),
    path('counter/<int:pk>/delete/', views.delete_set, name='delete_set'),
    path('exercises/add/', views.add_exercise, name='add_exercise'),
    path('stats/', views.stats_view, name='stats'),
    path('stats/add-past/', views.add_past_entry, name='add_past_entry'),
    path('reminders/', views.reminders_view, name='reminders'),
    path('reminders/<int:pk>/toggle/', views.toggle_reminder, name='toggle_reminder'),
    path('reminders/<int:pk>/delete/', views.delete_reminder, name='delete_reminder'),
    path('api/reminders/', views.reminders_api, name='reminders_api'),
    path('api/workouts/import/', views.import_workout_json, name='import_workout_json'),
    path('typing/', views.typing_view, name='typing'),
    path('api/typing/stats/', views.typing_stats_api, name='typing_stats_api'),
]
