from django.conf.urls import patterns, include, url
from django.views.decorators.cache import cache_page
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns =patterns('frontend.views',
                      url(r'^$', 'index'),
                      url(r'^dashboard/$', 'dashboard'),
                      url(r'^about/$', 'about'),
                      url(r'^verify_code/$', 'verify_code'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/class_settings/$', 'class_settings'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/autocomplete_names/$', 'autocomplete_names'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/student_settings/$', 'student_settings'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/add_user/$', 'add_user'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/remove_user/$', 'remove_user'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/user_role_toggle/$', 'user_role_toggle'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/$', 'classview'),
                      url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/(?P<active_page>\w+)/$', 'classview'),
                      (r'^avatar/', include('avatar.urls')),
                      )