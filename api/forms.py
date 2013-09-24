from django import forms
from models import EMAIL_FREQUENCY_CHOICES, StudentClassSettings, ClassSettings
from django.utils.safestring import mark_safe
from django.forms.extras import widgets

class PlainTextWidget(forms.Widget):
    def render(self, name, value, **kwargs):
        return mark_safe(value) if value is not None else ''

    def _has_changed(self, initial, data):
        return False

class StudentClassSettingsForm(forms.ModelForm):
    email_frequency = forms.ChoiceField(choices=EMAIL_FREQUENCY_CHOICES, label="Email Frequency", help_text='Control how often we email you about this class.')
    class Meta:
        model = StudentClassSettings
        fields = ["email_frequency",]

class ClassSettingsForm(forms.ModelForm):
    access_key = forms.CharField(widget=PlainTextWidget, required=False)
    description = forms.CharField()
    class Meta:
        model = ClassSettings
        fields = ["access_key", "allow_signups", "welcome_message", "description", ]