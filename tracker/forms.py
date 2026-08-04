from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Exercise, ExerciseGroup, SetEntry, Reminder


class SetEntryForm(forms.ModelForm):
    class Meta:
        model = SetEntry
        fields = ['exercise', 'sets_count', 'reps', 'rest_seconds']
        widgets = {
            'exercise': forms.Select(attrs={'class': 'ios-input'}),
            'sets_count': forms.NumberInput(attrs={'class': 'ios-input', 'min': 1}),
            'reps': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0}),
            'rest_seconds': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0, 'step': 5}),
        }

    def __init__(self, *args, exercise_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if exercise_queryset is not None:
            self.fields['exercise'].queryset = exercise_queryset
        self.fields['exercise'].label = 'Упражнение'
        self.fields['exercise'].empty_label = 'Выбери упражнение'
        self.fields['exercise'].required = True


class PastSetEntryForm(forms.ModelForm):
    """Та же форма подхода, но с явной датой — для добавления тренировки из прошлого."""
    date = forms.DateField(
        label='Дата тренировки',
        widget=forms.DateInput(attrs={'class': 'ios-input', 'type': 'date'})
    )

    class Meta:
        model = SetEntry
        fields = ['exercise', 'sets_count', 'reps', 'rest_seconds']
        widgets = {
            'exercise': forms.Select(attrs={'class': 'ios-input'}),
            'sets_count': forms.NumberInput(attrs={'class': 'ios-input', 'min': 1}),
            'reps': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0}),
            'rest_seconds': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0, 'step': 5}),
        }

    def __init__(self, *args, exercise_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if exercise_queryset is not None:
            self.fields['exercise'].queryset = exercise_queryset
        self.fields['exercise'].label = 'Упражнение'
        self.fields['exercise'].empty_label = 'Выбери упражнение'
        self.fields['exercise'].required = True


class ExerciseForm(forms.ModelForm):
    is_global = forms.BooleanField(
        label='Глобальное (видно всем пользователям)', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'switch-input'})
    )

    class Meta:
        model = Exercise
        fields = ['name', 'unit', 'group']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ios-input', 'placeholder': 'Например, Жим лёжа'}),
            'unit': forms.Select(attrs={'class': 'ios-input'}),
            'group': forms.Select(attrs={'class': 'ios-input'}),
        }

    def __init__(self, *args, group_queryset=None, show_global=False, **kwargs):
        super().__init__(*args, **kwargs)
        if group_queryset is not None:
            self.fields['group'].queryset = group_queryset
        self.fields['group'].required = False
        self.fields['group'].empty_label = 'Без группы'
        if not show_global:
            del self.fields['is_global']


class GroupForm(forms.ModelForm):
    is_global = forms.BooleanField(
        label='Глобальная (видна всем пользователям)', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'switch-input'})
    )

    class Meta:
        model = ExerciseGroup
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ios-input', 'placeholder': 'Например, Ноги'}),
        }

    def __init__(self, *args, show_global=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not show_global:
            del self.fields['is_global']


class ReminderForm(forms.ModelForm):
    days = forms.MultipleChoiceField(
        label='Дни недели', choices=Reminder.DAY_CHOICES, required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Reminder
        fields = ['title', 'time', 'days', 'enabled']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'ios-input', 'placeholder': 'Например, Тренировка ног'}),
            'time': forms.TimeInput(attrs={'class': 'ios-input', 'type': 'time'}),
        }

    def clean_days(self):
        return ','.join(self.cleaned_data['days'])

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.days = self.cleaned_data['days']
        if commit:
            instance.save()
        return instance


class SportLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'ios-input', 'placeholder': 'Логин', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'ios-input', 'placeholder': 'Пароль'}))


class SportSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'ios-input', 'placeholder': 'Логин', 'autofocus': True})
        self.fields['password1'].widget.attrs.update({'class': 'ios-input', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'ios-input', 'placeholder': 'Повтори пароль'})
        for f in self.fields.values():
            f.help_text = None
