import sys
import os
from path import path
import json
import djcelery
djcelery.setup_loader()

# Django settings for article_site project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

#Celery settings
BROKER_URL = 'redis://localhost:6379/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

BASE_DIR = os.path.abspath(os.path.join(__file__, "..", "..", ".."))

ROOT_PATH = path(__file__).dirname()
REPO_PATH = ROOT_PATH.dirname()
ENV_ROOT = REPO_PATH.dirname()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db/movide.db',    # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'cache',
        }
}
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.abspath(REPO_PATH / "staticfiles")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(REPO_PATH / "static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '31lkp8hoe-#000px$bl_35gs)v!^=%1gs+(i*=y5oxw$n(m2d9'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'movide.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'movide.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    str(os.path.abspath(REPO_PATH / 'templates/')),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'api.context_processors.google_analytics'
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)



INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'djcelery',
    'south',
    'rest_framework',
    'bootstrapform',
    'seacucumber',
    'api',
    'frontend'
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day'
    }
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
syslog_format = ("[%(name)s][env:{logging_env}] %(levelname)s "
                 "[{hostname}  %(process)d] [%(filename)s:%(lineno)d] "
                 "- %(message)s").format(
    logging_env="", hostname="")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(process)d '
                      '[%(name)s] %(filename)s:%(lineno)d - %(message)s',
            },
        'syslog_format': {'format': syslog_format},
        'raw': {'format': '%(message)s'},
        },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stdout,
            },
        'null':
            {
                'level' : 'DEBUG',
                'class' : 'django.utils.log.NullHandler'
            }
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
            },
        'requests.packages.urllib3.connectionpool': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
            },
        'boto': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
            },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
        }
}

SOCIALACCOUNT_PROVIDERS = {

}

AUTH_PROFILE_MODULE = 'api.UserProfile'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

#Authentication settings
ACCOUNT_AUTHENTICATION_METHOD="username_email"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"

GOOGLE_ANALYTICS_KEY = None

TWITTER_STREAM_EVERY = 2 * 60 #Seconds
CACHE_TIMEOUT = 10* 60 * 60 #seconds
TWITTER_STREAM_CACHE_TIMEOUT = 10* 365 * 24 * 60 * 60 #seconds
TWITTER_STREAM = True

#Email verification settings
EMAIL_BACKEND = 'seacucumber.backend.SESBackend'
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Movide] "
DEFAULT_FROM_EMAIL = "info@movide.com"
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = False

TWITTER_ACCESS_TOKEN = ""
TWITTER_SECRET_ACCESS_TOKEN = ""
TWITTER_APP_KEY = ""
TWITTER_SECRET_APP_KEY = ""
TWITTER_HASHTAG = "#movide"

TWITTER_AUTH_APP_KEY = ""
TWITTER_AUTH_SECRET_APP_KEY = ""

LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/dashboard/"

LOGIN_URL = "/"

try:
    from .private import *
except Exception:
    pass
