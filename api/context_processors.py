from django.conf import settings

def google_analytics(request):
    return {
    'ga_key': settings.GOOGLE_ANALYTICS_KEY,
    }