import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class ExerciseGroup(models.Model):
    """Группа (категория) упражнений: своя у пользователя или глобальная (owner=None)."""
    name = models.CharField('Название', max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='exercise_groups', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Владелец',
        help_text='Пусто — глобальная группа, видна всем пользователям'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Группа упражнений'
        verbose_name_plural = 'Группы упражнений'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_global(self):
        return self.owner_id is None


class Exercise(models.Model):
    """Упражнение из справочника (пресет для быстрого выбора): своё или глобальное (owner=None)."""
    UNIT_CHOICES = [
        ('reps', 'повторения'),
        ('kg', 'кг'),
        ('sec', 'секунды'),
        ('m', 'метры'),
    ]

    name = models.CharField('Название', max_length=100)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='reps')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='exercises', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Владелец',
        help_text='Пусто — глобальное упражнение, видно всем пользователям'
    )
    group = models.ForeignKey(
        ExerciseGroup, related_name='exercises', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Группа'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_global(self):
        return self.owner_id is None


class WorkoutSession(models.Model):
    """Тренировочная сессия (один день тренировки) конкретного пользователя."""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='workout_sessions', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Владелец'
    )
    date = models.DateField('Дата', default=timezone.localdate)
    time_start = models.TimeField('Начало', null=True, blank=True)
    time_end = models.TimeField('Окончание', null=True, blank=True)
    note = models.CharField('Заметка', max_length=255, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Тренировка'
        verbose_name_plural = 'Тренировки'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'Тренировка {self.date.isoformat()}'

    @property
    def total_reps(self):
        return sum(s.total_reps for s in self.sets.all())

    @property
    def total_sets(self):
        return sum(s.sets_count for s in self.sets.all())


class SetEntry(models.Model):
    """Запись подхода(ов): сколько подходов, по сколько повторений, и сколько отдыхали после."""
    session = models.ForeignKey(
        WorkoutSession, related_name='sets', on_delete=models.CASCADE, verbose_name='Тренировка'
    )
    exercise = models.ForeignKey(
        Exercise, related_name='sets', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Упражнение'
    )
    exercise_name = models.CharField(
        'Название упражнения', max_length=100, blank=True,
        help_text='Заполняется автоматически, если упражнение выбрано из справочника'
    )
    sets_count = models.PositiveIntegerField('Подходов', default=1)
    reps = models.PositiveIntegerField('Повторения', default=0)
    rest_seconds = models.PositiveIntegerField('Отдых, сек', default=60)
    created_at = models.DateTimeField('Время', auto_now_add=True)

    class Meta:
        verbose_name = 'Подход'
        verbose_name_plural = 'Подходы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.display_name}: {self.sets_count}×{self.reps}'

    @property
    def display_name(self):
        return self.exercise.name if self.exercise else (self.exercise_name or 'Упражнение')

    @property
    def total_reps(self):
        return self.sets_count * self.reps

    def save(self, *args, **kwargs):
        if self.exercise and not self.exercise_name:
            self.exercise_name = self.exercise.name
        super().save(*args, **kwargs)


class Reminder(models.Model):
    """Напоминание о тренировке конкретного пользователя."""
    DAY_CHOICES = [
        ('mon', 'Пн'), ('tue', 'Вт'), ('wed', 'Ср'), ('thu', 'Чт'),
        ('fri', 'Пт'), ('sat', 'Сб'), ('sun', 'Вс'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='reminders', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Владелец'
    )
    title = models.CharField('Название', max_length=100)
    time = models.TimeField('Время')
    days = models.CharField(
        'Дни недели', max_length=50, blank=True,
        help_text='Через запятую: mon,tue,wed,thu,fri,sat,sun. Пусто = каждый день'
    )
    enabled = models.BooleanField('Включено', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        ordering = ['time']

    def __str__(self):
        return f'{self.title} в {self.time.strftime("%H:%M")}'

    def days_list(self):
        return [d for d in self.days.split(',') if d.strip()]

    def days_display(self):
        labels = dict(self.DAY_CHOICES)
        days = self.days_list()
        if not days:
            return 'Каждый день'
        return ', '.join(labels.get(d, d) for d in days)


class ApiKey(models.Model):
    """Личный API-ключ пользователя для защищённых внешних вызовов (JSON-импорт тренировок)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='api_key', on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    key = models.CharField('Ключ', max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'API-ключ'
        verbose_name_plural = 'API-ключи'

    def __str__(self):
        return f'API-ключ {self.user}'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @classmethod
    def for_user(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj

    def regenerate(self):
        self.key = secrets.token_urlsafe(32)
        self.save(update_fields=['key'])
        return self.key
