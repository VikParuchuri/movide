from django import forms
from models import EMAIL_FREQUENCY_CHOICES, StudentClassSettings, ClassSettings
from django.utils.safestring import mark_safe
from django.forms.extras import widgets

class PlainTextWidget(forms.Widget):
    input_type = 'text'

    def render(self, name, value, attrs=None):
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
    allow_signups = forms.BooleanField(help_text="Allow students to sign up for the course using the access.", label="Allow signups", required=False)
    enable_posting = forms.BooleanField(help_text="Allow students to make discussion posts (if this is disabled, they will still be able to reply).", label="Enable posting", required=False)

    class Meta:
        model = ClassSettings
        fields = ["access_key", "allow_signups", "enable_posting", "welcome_message", "description", ]

    def clean_access_key(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.access_key
        else:
            return self.cleaned_data['access_key']