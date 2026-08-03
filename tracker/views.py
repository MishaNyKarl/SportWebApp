import json
from datetime import timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import SetEntryForm, ReminderForm
from .models import Exercise, WorkoutSession, SetEntry, Reminder


def timer_view(request):
    """Главная страница — таймер отдыха между подходами."""
    return render(request, 'tracker/timer.html', {'active_tab': 'timer'})


def _get_or_create_today_session():
    today = timezone.localdate()
    session, _ = WorkoutSession.objects.get_or_create(date=today)
    return session


def counter_view(request):
    """Счётчик повторений + сохранение подходов."""
    session = _get_or_create_today_session()

    if request.method == 'POST':
        form = SetEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.session = session
            name = form.cleaned_data['exercise_name'].strip()
            if name:
                exercise, _ = Exercise.objects.get_or_create(name=name)
                entry.exercise = exercise
                entry.exercise_name = name
            entry.save()
            messages.success(request, 'Подход сохранён')
            return redirect('tracker:counter')
    else:
        form = SetEntryForm(initial={'reps': 0, 'weight': 0, 'rest_seconds': 60})

    today_sets = session.sets.select_related('exercise').all()
    exercises = Exercise.objects.all()

    return render(request, 'tracker/counter.html', {
        'active_tab': 'counter',
        'form': form,
        'today_sets': today_sets,
        'exercises': exercises,
        'session': session,
    })


@require_POST
def delete_set(request, pk):
    entry = get_object_or_404(SetEntry, pk=pk)
    entry.delete()
    messages.success(request, 'Подход удалён')
    return redirect('tracker:counter')


def clock_view(request):
    """Часы + секундомер."""
    return render(request, 'tracker/clock.html', {'active_tab': 'clock'})


def stats_view(request):
    """Статистика тренировок: объём, повторения, серии, графики."""
    today = timezone.localdate()
    start_14 = today - timedelta(days=13)
    start_8w = today - timedelta(weeks=7)

    all_sets = SetEntry.objects.select_related('session').all()
    sessions = WorkoutSession.objects.all()

    total_sessions = sessions.count()
    total_sets = all_sets.count()
    total_reps = sum(s.reps for s in all_sets)
    total_volume = round(sum(s.volume for s in all_sets), 1)

    # Streak: подряд идущие дни с тренировками, считая от сегодня назад
    session_dates = set(sessions.values_list('date', flat=True))
    streak = 0
    cursor = today
    while cursor in session_dates:
        streak += 1
        cursor -= timedelta(days=1)

    # Повторения по дням за последние 14 дней
    daily_labels, daily_reps = [], []
    for i in range(14):
        d = start_14 + timedelta(days=i)
        reps = sum(s.reps for s in all_sets if s.session.date == d)
        daily_labels.append(d.strftime('%d.%m'))
        daily_reps.append(reps)

    # Объём по неделям за последние 8 недель
    weekly_labels, weekly_volume = [], []
    for i in range(8):
        week_start = start_8w + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        vol = sum(s.volume for s in all_sets if week_start <= s.session.date <= week_end)
        weekly_labels.append(week_start.strftime('%d.%m'))
        weekly_volume.append(round(vol, 1))

    top_exercises = (
        Exercise.objects.all()
        .prefetch_related('sets')
    )
    top_exercise_stats = sorted(
        [(e.name, sum(s.reps for s in e.sets.all())) for e in top_exercises],
        key=lambda x: x[1], reverse=True
    )[:5]

    context = {
        'active_tab': 'stats',
        'total_sessions': total_sessions,
        'total_sets': total_sets,
        'total_reps': total_reps,
        'total_volume': total_volume,
        'streak': streak,
        'daily_labels_json': json.dumps(daily_labels),
        'daily_reps_json': json.dumps(daily_reps),
        'weekly_labels_json': json.dumps(weekly_labels),
        'weekly_volume_json': json.dumps(weekly_volume),
        'top_exercise_stats': top_exercise_stats,
    }
    return render(request, 'tracker/stats.html', context)


def reminders_view(request):
    """Список и создание напоминаний о тренировках."""
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Напоминание создано')
            return redirect('tracker:reminders')
    else:
        form = ReminderForm()

    reminders = Reminder.objects.all()
    return render(request, 'tracker/reminders.html', {
        'active_tab': 'reminders',
        'form': form,
        'reminders': reminders,
    })


@require_POST
def toggle_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    reminder.enabled = not reminder.enabled
    reminder.save(update_fields=['enabled'])
    return redirect('tracker:reminders')


@require_POST
def delete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    reminder.delete()
    messages.success(request, 'Напоминание удалено')
    return redirect('tracker:reminders')


def reminders_api(request):
    """JSON со всеми включёнными напоминаниями — используется JS для проверки на клиенте."""
    data = [
        {
            'id': r.id,
            'title': r.title,
            'time': r.time.strftime('%H:%M'),
            'days': r.days_list(),
        }
        for r in Reminder.objects.filter(enabled=True)
    ]
    return JsonResponse({'reminders': data})
