import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Название')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
            ],
            options={
                'verbose_name': 'Упражнение',
                'verbose_name_plural': 'Упражнения',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
                ('time', models.TimeField(verbose_name='Время')),
                ('days', models.CharField(blank=True, help_text='Через запятую: mon,tue,wed,thu,fri,sat,sun. Пусто = каждый день', max_length=50, verbose_name='Дни недели')),
                ('enabled', models.BooleanField(default=True, verbose_name='Включено')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
            ],
            options={
                'verbose_name': 'Напоминание',
                'verbose_name_plural': 'Напоминания',
                'ordering': ['time'],
            },
        ),
        migrations.CreateModel(
            name='WorkoutSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Дата')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Заметка')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
            ],
            options={
                'verbose_name': 'Тренировка',
                'verbose_name_plural': 'Тренировки',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SetEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exercise_name', models.CharField(blank=True, help_text='Заполняется автоматически, если упражнение выбрано из справочника', max_length=100, verbose_name='Название упражнения')),
                ('reps', models.PositiveIntegerField(default=0, verbose_name='Повторения')),
                ('weight', models.FloatField(default=0, verbose_name='Вес, кг')),
                ('rest_seconds', models.PositiveIntegerField(default=60, verbose_name='Отдых, сек')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время')),
                ('exercise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sets', to='tracker.exercise', verbose_name='Упражнение')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sets', to='tracker.workoutsession', verbose_name='Тренировка')),
            ],
            options={
                'verbose_name': 'Подход',
                'verbose_name_plural': 'Подходы',
                'ordering': ['-created_at'],
            },
        ),
    ]
