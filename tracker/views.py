import json
import os
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import (
    SetEntryForm, PastSetEntryForm, ExerciseForm, GroupForm, ReminderForm,
    SportLoginForm, SportSignupForm,
)
from .models import Exercise, ExerciseGroup, WorkoutSession, SetEntry, Reminder, ApiKey

MONKEYTYPE_API = 'https://api.monkeytype.com'


# --- Авторизация -----------------------------------------------------------

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('tracker:timer')
    if request.method == 'POST':
        form = SportSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Первый зарегистрированный становится админом — управляет глобальным каталогом.
            if not User.objects.exists():
                user.is_staff = True
                user.is_superuser = True
            user.save()
            ApiKey.for_user(user)
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('tracker:timer')
    else:
        form = SportSignupForm()
    return render(request, 'tracker/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('tracker:timer')
    if request.method == 'POST':
        form = SportLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next') or 'tracker:timer')
    else:
        form = SportLoginForm(request)
    return render(request, 'tracker/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('tracker:login')


# --- Вспомогательное ---------------------------------------------------------

def _visible_exercises(user):
    return Exercise.objects.filter(Q(owner=user) | Q(owner__isnull=True)).order_by('name')


def _visible_groups(user):
    return ExerciseGroup.objects.filter(Q(owner=user) | Q(owner__isnull=True)).order_by('name')


def _get_or_create_today_session(user):
    today = timezone.localdate()
    session, _ = WorkoutSession.objects.get_or_create(date=today, owner=user)
    return session


def _recent_exercises(user, limit=3):
    """Последние N уникальных упражнений пользователя — для быстрого выбора."""
    seen_ids = []
    recent = []
    qs = (
        SetEntry.objects.filter(session__owner=user, exercise__isnull=False)
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


# --- Таймер ---------------------------------------------------------

@login_required
def timer_view(request):
    """Главная страница — таймер отдыха между подходами."""
    return render(request, 'tracker/timer.html', {'active_tab': 'timer'})


# --- Счётчик ---------------------------------------------------------

@login_required
def counter_view(request):
    """Счётчик повторений + сохранение подходов."""
    session = _get_or_create_today_session(request.user)
    exercise_qs = _visible_exercises(request.user)
    group_qs = _visible_groups(request.user)

    if request.method == 'POST':
        form = SetEntryForm(request.POST, exercise_queryset=exercise_qs)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.session = session
            entry.save()
            messages.success(request, 'Подход сохранён')
            return redirect('tracker:counter')
    else:
        form = SetEntryForm(
            initial={'reps': 0, 'sets_count': 1, 'rest_seconds': 60}, exercise_queryset=exercise_qs
        )

    today_sets = session.sets.select_related('exercise').all()

    return render(request, 'tracker/counter.html', {
        'active_tab': 'counter',
        'form': form,
        'exercise_form': ExerciseForm(group_queryset=group_qs, show_global=request.user.is_staff),
        'group_form': GroupForm(show_global=request.user.is_staff),
        'today_sets': today_sets,
        'exercises': exercise_qs,
        'groups': group_qs,
        'recent_exercises': _recent_exercises(request.user),
        'session': session,
    })


@login_required
@require_POST
def delete_set(request, pk):
    entry = get_object_or_404(SetEntry, pk=pk, session__owner=request.user)
    entry.delete()
    messages.success(request, 'Подход удалён')
    return redirect('tracker:counter')


@login_required
@require_POST
def add_exercise(request):
    """Добавление нового упражнения в справочник (модалка по шестерёнке)."""
    form = ExerciseForm(
        request.POST, group_queryset=_visible_groups(request.user), show_global=request.user.is_staff
    )
    if form.is_valid():
        exercise = form.save(commit=False)
        if request.user.is_staff and form.cleaned_data.get('is_global'):
            exercise.owner = None
        else:
            exercise.owner = request.user
        exercise.save()
        messages.success(request, 'Упражнение добавлено')
    else:
        messages.error(request, 'Не удалось добавить упражнение: проверь название')
    return redirect(request.POST.get('next') or 'tracker:counter')


@login_required
@require_POST
def add_group(request):
    """Добавление новой группы упражнений."""
    form = GroupForm(request.POST, show_global=request.user.is_staff)
    if form.is_valid():
        group = form.save(commit=False)
        if request.user.is_staff and form.cleaned_data.get('is_global'):
            group.owner = None
        else:
            group.owner = request.user
        group.save()
        messages.success(request, 'Группа добавлена')
    else:
        messages.error(request, 'Не удалось добавить группу: проверь название')
    return redirect(request.POST.get('next') or 'tracker:counter')


# --- Статистика ---------------------------------------------------------

@login_required
def stats_view(request):
    """Статистика тренировок: объём, повторения, серии, графики."""
    today = timezone.localdate()
    start_14 = today - timedelta(days=13)
    start_8w = today - timedelta(weeks=7)

    all_sets = list(SetEntry.objects.filter(session__owner=request.user).select_related('session', 'exercise'))
    sessions = WorkoutSession.objects.filter(owner=request.user)

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

    # Топ упражнений по повторениям (считаем только на своих подходах пользователя)
    totals = defaultdict(int)
    names = {}
    for s in all_sets:
        key = s.exercise_id or s.exercise_name
        names[key] = s.display_name
        totals[key] += s.total_reps
    top_exercise_stats = sorted(
        [(names[k], v) for k, v in totals.items()], key=lambda x: x[1], reverse=True
    )[:5]

    recent_sessions = sessions.prefetch_related('sets')[:10]
    exercise_qs = _visible_exercises(request.user)

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
        'exercises': exercise_qs,
        'past_entry_form': PastSetEntryForm(
            initial={'rest_seconds': 60}, exercise_queryset=exercise_qs
        ),
    }
    return render(request, 'tracker/stats.html', context)


@login_required
@require_POST
def add_past_entry(request):
    """
    Добавление тренировки задним числом (иконка тренировки на странице статистики).
    Подходы приходят списком в POST['reps'] — по одной строке повторений на подход,
    каждая строка становится отдельным SetEntry (sets_count=1).
    """
    form = PastSetEntryForm(request.POST, exercise_queryset=_visible_exercises(request.user))
    reps_values = []
    for raw in request.POST.getlist('reps'):
        raw = raw.strip()
        if not raw:
            continue
        try:
            reps_values.append(int(raw))
        except ValueError:
            continue

    if form.is_valid() and reps_values:
        session, _ = WorkoutSession.objects.get_or_create(
            date=form.cleaned_data['date'], owner=request.user
        )
        exercise = form.cleaned_data['exercise']
        rest_seconds = form.cleaned_data['rest_seconds']
        for reps in reps_values:
            SetEntry.objects.create(
                session=session, exercise=exercise, sets_count=1,
                reps=reps, rest_seconds=rest_seconds,
            )
        messages.success(
            request,
            f'Тренировка за {form.cleaned_data["date"].strftime("%d.%m.%Y")} добавлена: {len(reps_values)} подход(ов)'
        )
    else:
        messages.error(request, 'Не удалось добавить тренировку: проверь упражнение и хотя бы один подход')
    return redirect('tracker:stats')


def _authenticate_api_key(request):
    """Достаёт пользователя по заголовку Authorization: Bearer <ключ> (или X-Api-Key)."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    key = auth_header[len('Bearer '):].strip() if auth_header.startswith('Bearer ') else ''
    if not key:
        key = request.META.get('HTTP_X_API_KEY', '').strip()
    if not key:
        return None
    api_key = ApiKey.objects.filter(key=key).select_related('user').first()
    return api_key.user if api_key else None


@csrf_exempt
@require_POST
def import_workout_json(request):
    """
    JSON-импорт тренировки, например из iOS Shortcuts или скрипта.

    Требует заголовок: Authorization: Bearer <твой API-ключ>
    (ключ смотри в настройках приложения).

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
    exercise_id должен быть твоим собственным или глобальным упражнением.
    Одно и то же exercise_id можно указывать несколько раз — каждый
    объект в "exercises" станет отдельной записью.
    """
    user = _authenticate_api_key(request)
    if not user:
        return JsonResponse(
            {'ok': False, 'error': 'Неверный или отсутствующий API-ключ (заголовок Authorization: Bearer <ключ>)'},
            status=401,
        )

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

    exercise_qs = _visible_exercises(user)

    session, _ = WorkoutSession.objects.get_or_create(date=date_train, owner=user)
    session.time_start = _parse_time(payload.get('time_start')) or session.time_start
    session.time_end = _parse_time(payload.get('time_end')) or session.time_end
    if payload.get('note'):
        session.note = payload['note']
    session.save()

    created, errors = 0, []
    for i, item in enumerate(exercises_payload):
        exercise_id = item.get('exercise_id')
        exercise = exercise_qs.filter(pk=exercise_id).first() if exercise_id else None
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


# --- Настройки (API-ключ) ---------------------------------------------------------

@login_required
def settings_view(request):
    api_key = ApiKey.for_user(request.user)
    if request.method == 'POST' and request.POST.get('action') == 'regenerate':
        api_key.regenerate()
        messages.success(request, 'Ключ обновлён — старый больше не действителен')
        return redirect('tracker:settings')
    return render(request, 'tracker/settings.html', {
        'active_tab': 'settings',
        'api_key': api_key,
        'import_url': request.build_absolute_uri(reverse('tracker:import_workout_json')),
    })


# --- Напоминания ---------------------------------------------------------

@login_required
def reminders_view(request):
    """Список и создание напоминаний о тренировках."""
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.owner = request.user
            reminder.save()
            messages.success(request, 'Напоминание создано')
            return redirect('tracker:reminders')
    else:
        form = ReminderForm()

    reminders = Reminder.objects.filter(owner=request.user)
    return render(request, 'tracker/reminders.html', {
        'active_tab': 'reminders',
        'form': form,
        'reminders': reminders,
    })


@login_required
@require_POST
def toggle_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, owner=request.user)
    reminder.enabled = not reminder.enabled
    reminder.save(update_fields=['enabled'])
    return redirect('tracker:reminders')


@login_required
@require_POST
def delete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, owner=request.user)
    reminder.delete()
    messages.success(request, 'Напоминание удалено')
    return redirect('tracker:reminders')


@login_required
def reminders_api(request):
    """JSON со всеми включёнными напоминаниями пользователя — используется JS для проверки на клиенте."""
    data = [
        {
            'id': r.id,
            'title': r.title,
            'time': r.time.strftime('%H:%M'),
            'days': r.days_list(),
        }
        for r in Reminder.objects.filter(enabled=True, owner=request.user)
    ]
    return JsonResponse({'reminders': data})


# --- Тест печати (не связан с тренировками) ---------------------------------------------------------

@login_required
def typing_view(request):
    """Тест на скорость печати + статистика реального аккаунта MonkeyType."""
    return render(request, 'tracker/typing.html', {
        'active_tab': 'typing',
        'monkeytype_connected': bool(os.environ.get('MONKEYTYPE_APEKEY')),
    })


def _monkeytype_get(path):
    """GET-запрос к api.monkeytype.com с ApeKey из окружения. Возвращает (data, error)."""
    apekey = os.environ.get('MONKEYTYPE_APEKEY')
    if not apekey:
        return None, 'MONKEYTYPE_APEKEY не настроен на сервере'
    req = urllib.request.Request(
        f'{MONKEYTYPE_API}{path}',
        headers={
            'Authorization': f'ApeKey {apekey}',
            # Cloudflare перед api.monkeytype.com блокирует запросы с дефолтным
            # User-Agent библиотеки (Python-urllib/...) как бот-трафик.
            'User-Agent': 'Mozilla/5.0 (compatible; SportWebApp/1.0)',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            return body.get('data'), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode('utf-8'))
            msg = body.get('message', str(e))
        except Exception:
            msg = str(e)
        return None, msg
    except Exception as e:
        return None, str(e)


def _best_of(data):
    """personalBests иногда приходит списком (несколько заходов на тот же режим) — берём лучший по wpm."""
    if isinstance(data, list):
        return max(data, key=lambda x: x.get('wpm', 0)) if data else None
    return data


@login_required
def typing_stats_api(request):
    """Прокси к личной статистике MonkeyType (сервер хранит ApeKey, фронтенд его не видит)."""
    stats, err_stats = _monkeytype_get('/users/stats')
    streak, err_streak = _monkeytype_get('/users/streak')
    pb60, err_pb60 = _monkeytype_get('/users/personalBests?mode=time&mode2=60')
    pb30, err_pb30 = _monkeytype_get('/users/personalBests?mode=time&mode2=30')

    errors = [e for e in (err_stats, err_streak, err_pb60, err_pb30) if e]

    return JsonResponse({
        'ok': stats is not None,
        'stats': stats,
        'streak': streak,
        'personalBests': {
            'time30': _best_of(pb30),
            'time60': _best_of(pb60),
        },
        'errors': errors,
    })
