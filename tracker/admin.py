from django.contrib import admin
from .models import Exercise, ExerciseGroup, WorkoutSession, SetEntry, Reminder, ApiKey


class SetEntryInline(admin.TabularInline):
    model = SetEntry
    extra = 0


@admin.register(ExerciseGroup)
class ExerciseGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_global', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'group', 'owner', 'is_global', 'created_at')
    list_filter = ('owner', 'group', 'unit')
    search_fields = ('name',)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'owner', 'time_start', 'time_end', 'note', 'total_sets', 'total_reps')
    list_filter = ('date', 'owner')
    inlines = [SetEntryInline]


@admin.register(SetEntry)
class SetEntryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'sets_count', 'reps', 'rest_seconds', 'session', 'created_at')
    list_filter = ('created_at',)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'time', 'days_display', 'enabled')
    list_filter = ('enabled', 'owner')


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    search_fields = ('user__username',)
