from django.conf.urls import patterns, url, include
from django.views.decorators.cache import cache_page
from django.conf import settings

from rest_framework import viewsets, routers
from views import (TagView, TagDetailView, TweetView, TweetDetailView, UserList, UserDetail, UserRegistration)


urlpatterns = patterns('',
                       url(r'^users/$', UserList.as_view()),
                       url(r'^users/(?P<pk>[0-9]+)/$', UserDetail.as_view()),
                       url(r'^users/register/$', UserRegistration.as_view()),
                       url(r'^tags/$', TagView.as_view()),
                       url(r'^tags/(?P<pk>[0-9]+)/$', TagDetailView.as_view()),
                       url(r'^tweets/$', TweetView.as_view()),
                       url(r'^tweets/(?P<pk>[0-9]+)/$', TweetDetailView.as_view()),
                       )

