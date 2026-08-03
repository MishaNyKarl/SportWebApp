from django.contrib import admin
from .models import Exercise, WorkoutSession, SetEntry, Reminder


class SetEntryInline(admin.TabularInline):
    model = SetEntry
    extra = 0


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'created_at')
    search_fields = ('name',)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'time_start', 'time_end', 'note', 'total_reps', 'total_volume')
    list_filter = ('date',)
    inlines = [SetEntryInline]


@admin.register(SetEntry)
class SetEntryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'reps', 'weight', 'volume', 'rest_seconds', 'session', 'created_at')
    list_filter = ('created_at',)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'time', 'days_display', 'enabled')
    list_filter = ('enabled',)
