import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import SetEntryForm, PastSetEntryForm, ExerciseForm, ReminderForm
from .models import Exercise, WorkoutSession, SetEntry, Reminder


def timer_view(request):
    """Главная страница — таймер отдыха между подходами."""
    return render(request, 'tracker/timer.html', {'active_tab': 'timer'})


def _get_or_create_today_session():
    today = timezone.localdate()
    session, _ = WorkoutSession.objects.get_or_create(date=today)
    return session


def _recent_exercises(limit=3):
    """Последние N уникальных упражнений, использованных в подходах — для быстрого выбора."""
    seen_ids = []
    recent = []
    qs = (
        SetEntry.objects.exclude(exercise__isnull=True)
        .select_related('exercise')
        .order_by('-created_at')[:50]
    )
    for entry in qs:
        if entry.exercise_id not in seen_ids:
            seen_ids.append(entry.exercise_id)
            recent.append(entry.exercise)
        if len(recent) >= limit:
            break
    return recent


def counter_view(request):
    """Счётчик повторений + сохранение подходов."""
    session = _get_or_create_today_session()

    if request.method == 'POST':
        form = SetEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.session = session
            entry.save()
            messages.success(request, 'Подход сохранён')
            return redirect('tracker:counter')
    else:
        form = SetEntryForm(initial={'reps': 0, 'sets_count': 1, 'rest_seconds': 60})

    today_sets = session.sets.select_related('exercise').all()
    exercises = Exercise.objects.all()

    return render(request, 'tracker/counter.html', {
        'active_tab': 'counter',
        'form': form,
        'exercise_form': ExerciseForm(),
        'today_sets': today_sets,
        'exercises': exercises,
        'recent_exercises': _recent_exercises(),
        'session': session,
    })


@require_POST
def delete_set(request, pk):
    entry = get_object_or_404(SetEntry, pk=pk)
    entry.delete()
    messages.success(request, 'Подход удалён')
    return redirect('tracker:counter')


@require_POST
def add_exercise(request):
    """Добавление нового упражнения в справочник (модалка по шестерёнке)."""
    form = ExerciseForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Упражнение добавлено')
    else:
        messages.error(request, 'Не удалось добавить упражнение: проверь название')
    return redirect(request.POST.get('next') or 'tracker:counter')


def stats_view(request):
    """Статистика тренировок: объём, повторения, серии, графики."""
    today = timezone.localdate()
    start_14 = today - timedelta(days=13)
    start_8w = today - timedelta(weeks=7)

    all_sets = SetEntry.objects.select_related('session').all()
    sessions = WorkoutSession.objects.all()

    total_sessions = sessions.count()
    total_sets = sum(s.sets_count for s in all_sets)
    total_reps = sum(s.total_reps for s in all_sets)

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
        reps = sum(s.total_reps for s in all_sets if s.session.date == d)
        daily_labels.append(d.strftime('%d.%m'))
        daily_reps.append(reps)

    # Подходы по неделям за последние 8 недель
    weekly_labels, weekly_sets = [], []
    for i in range(8):
        week_start = start_8w + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        cnt = sum(s.sets_count for s in all_sets if week_start <= s.session.date <= week_end)
        weekly_labels.append(week_start.strftime('%d.%m'))
        weekly_sets.append(cnt)

    top_exercises = (
        Exercise.objects.all()
        .prefetch_related('sets')
    )
    top_exercise_stats = sorted(
        [(e.name, sum(s.total_reps for s in e.sets.all())) for e in top_exercises],
        key=lambda x: x[1], reverse=True
    )[:5]

    recent_sessions = sessions.prefetch_related('sets')[:10]

    context = {
        'active_tab': 'stats',
        'total_sessions': total_sessions,
        'total_sets': total_sets,
        'total_reps': total_reps,
        'streak': streak,
        'daily_labels_json': json.dumps(daily_labels),
        'daily_reps_json': json.dumps(daily_reps),
        'weekly_labels_json': json.dumps(weekly_labels),
        'weekly_sets_json': json.dumps(weekly_sets),
        'top_exercise_stats': top_exercise_stats,
        'recent_sessions': recent_sessions,
        'exercises': Exercise.objects.all(),
        'past_entry_form': PastSetEntryForm(initial={'reps': 0, 'sets_count': 1, 'rest_seconds': 60}),
    }
    return render(request, 'tracker/stats.html', context)


@require_POST
def add_past_entry(request):
    """Добавление тренировки задним числом (иконка тренировки на странице статистики)."""
    form = PastSetEntryForm(request.POST)
    if form.is_valid():
        session, _ = WorkoutSession.objects.get_or_create(date=form.cleaned_data['date'])
        entry = form.save(commit=False)
        entry.session = session
        entry.save()
        messages.success(request, f'Тренировка за {form.cleaned_data["date"].strftime("%d.%m.%Y")} добавлена')
    else:
        messages.error(request, 'Не удалось добавить тренировку: проверь поля')
    return redirect('tracker:stats')


@csrf_exempt
@require_POST
def import_workout_json(request):
    """
    JSON-импорт тренировки, например из iOS Shortcuts или скрипта.

    Формат тела запроса:
    {
      "date_train": "2026-08-01",
      "time_start": "18:00",
      "time_end": "19:00",
      "note": "необязательно",
      "exercises": [
        {"exercise_id": 1, "count": 10, "sets": 3},
        {"exercise_id": 2, "count": 12, "sets": 4}
      ]
    }

    "count" — число повторений в одном подходе (или другая величина,
    если у упражнения иная единица измерения — секунды/метры/кг).
    "sets" — количество подходов, необязателен, по умолчанию 1.
    Одно и то же exercise_id можно указывать несколько раз — каждый
    объект в "exercises" станет отдельной записью.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Некорректный JSON'}, status=400)

    date_str = payload.get('date_train')
    if not date_str:
        return JsonResponse({'ok': False, 'error': 'Поле date_train обязательно'}, status=400)
    try:
        date_train = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'date_train должен быть в формате YYYY-MM-DD'}, status=400)

    def _parse_time(value):
        if not value:
            return None
        for fmt in ('%H:%M:%S', '%H:%M'):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        return None

    exercises_payload = payload.get('exercises') or []
    if not isinstance(exercises_payload, list) or not exercises_payload:
        return JsonResponse({'ok': False, 'error': 'Поле exercises должно быть непустым списком'}, status=400)

    session, _ = WorkoutSession.objects.get_or_create(date=date_train)
    session.time_start = _parse_time(payload.get('time_start')) or session.time_start
    session.time_end = _parse_time(payload.get('time_end')) or session.time_end
    if payload.get('note'):
        session.note = payload['note']
    session.save()

    created, errors = 0, []
    for i, item in enumerate(exercises_payload):
        exercise_id = item.get('exercise_id')
        exercise = Exercise.objects.filter(pk=exercise_id).first() if exercise_id else None
        if not exercise:
            errors.append(f'exercises[{i}]: упражнение с id={exercise_id} не найдено')
            continue
        SetEntry.objects.create(
            session=session,
            exercise=exercise,
            exercise_name=exercise.name,
            reps=int(item.get('count') or 0),
            sets_count=int(item.get('sets') or 1),
            rest_seconds=int(item.get('rest_seconds') or 60),
        )
        created += 1

    return JsonResponse({
        'ok': True,
        'session_id': session.id,
        'created_entries': created,
        'errors': errors,
    })


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
