from django import forms
from .models import Exercise, SetEntry, Reminder


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exercise'].label = 'Упражнение'
        self.fields['exercise'].empty_label = 'Выбери упражнение'
        self.fields['exercise'].required = True


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['name', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ios-input', 'placeholder': 'Например, Жим лёжа'}),
            'unit': forms.Select(attrs={'class': 'ios-input'}),
        }


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
