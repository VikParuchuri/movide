from django.conf import settings

def google_analytics(request):
    """
    Allow for the google analytics key to be present as a template variable.
    """
    return {
    'ga_key': settings.GOOGLE_ANALYTICS_KEY,
    }