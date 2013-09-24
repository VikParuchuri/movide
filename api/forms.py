from django import forms
from models import EMAIL_FREQUENCY_CHOICES, StudentClassSettings

class StudentClassSettingsForm(forms.ModelForm):
    email_frequency = forms.ChoiceField(choices=EMAIL_FREQUENCY_CHOICES, label="Email Frequency", help_text='Control how often we email you about this class.')
    class Meta:
        model = StudentClassSettings
        fields = ["email_frequency",]