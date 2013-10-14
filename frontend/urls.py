from django.conf.urls import patterns, include, url
from django.views.decorators.cache import cache_page
from django.conf import settings
from redactor.forms import FileForm, ImageForm

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns =patterns('frontend.views',
                      url(r'^$', 'index', name="index"),
                      url(r'^dashboard/$', 'dashboard'),
                      url(r'^about/$', 'about', name="about"),
                      url(r'^verify_code/$', 'verify_code', name="verify_code"),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/class_settings/$', 'class_settings', name="class_settings_post"),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/autocomplete_names/$', 'autocomplete_names'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/student_settings/$', 'student_settings', name="student_class_settings_post"),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/add_user/$', 'add_user'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/remove_user/$', 'remove_user'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/user_role_toggle/$', 'user_role_toggle'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/$', 'classview'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/help/$', 'help'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/(?P<active_page>\w+)/$', 'classview'),
                      (r'^avatar/', include('avatar.urls')),
                      )

# Add in upload urls for redactor editing.
urlpatterns += patterns(
    'frontend.views',
    url('^classes/(?P<classgroup>[0-9A-Za-z]+)/upload/image/(?P<upload_to>.*)', 'redactor_upload',
        {
            'form_class': ImageForm,
            'response': lambda name, url: '<img src="{0}" alt="{1}" />'.format(url, name),
            },
        name='redactor_upload_image'),

    url('^classes/(?P<classgroup>[0-9A-Za-z]+)/upload/file/(?P<upload_to>.*)', 'redactor_upload',
        {
            'form_class': FileForm,
            'response': lambda name, url: '<a href="{0}">{1}</a>'.format(url, name),
            },
        name='redactor_upload_file'),
    )