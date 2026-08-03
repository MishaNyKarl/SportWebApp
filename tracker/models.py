from django.db import models
from django.utils import timezone


class Exercise(models.Model):
    """Упражнение из справочника (пресет для быстрого выбора)."""
    UNIT_CHOICES = [
        ('reps', 'повторения'),
        ('kg', 'кг'),
        ('sec', 'секунды'),
        ('m', 'метры'),
    ]

    name = models.CharField('Название', max_length=100, unique=True)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES, default='reps')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkoutSession(models.Model):
    """Тренировочная сессия (один день тренировки)."""
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
    """Напоминание о тренировке."""
    DAY_CHOICES = [
        ('mon', 'Пн'), ('tue', 'Вт'), ('wed', 'Ср'), ('thu', 'Чт'),
        ('fri', 'Пт'), ('sat', 'Сб'), ('sun', 'Вс'),
    ]

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
