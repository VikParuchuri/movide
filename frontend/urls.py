from django.conf.urls import patterns, include, url
from django.views.decorators.cache import cache_page
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns =patterns('frontend.views',
                      url(r'^$', 'index'),
                      #url(r'^articles/', 'articles'),
                      )

urlpatterns += patterns('',
                        (r'^accounts/', include('allauth.urls')),
                        )