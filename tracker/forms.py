from django import forms
from .models import SetEntry, Reminder


class SetEntryForm(forms.ModelForm):
    exercise_name = forms.CharField(
        label='Упражнение', max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'ios-input', 'placeholder': 'Например, Жим лёжа', 'list': 'exercise-list', 'autocomplete': 'off',
        })
    )

    class Meta:
        model = SetEntry
        fields = ['exercise_name', 'reps', 'weight', 'rest_seconds']
        widgets = {
            'reps': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0}),
            'weight': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0, 'step': '0.5'}),
            'rest_seconds': forms.NumberInput(attrs={'class': 'ios-input', 'min': 0, 'step': 5}),
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
