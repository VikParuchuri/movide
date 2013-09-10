from django.conf.urls import patterns, url, include
from django.views.decorators.cache import cache_page
from django.conf import settings

from rest_framework import viewsets, routers
from views import (TagView, TagDetailView, TweetView, TweetDetailView,
                   UserView, UserDetail, UserRegistration, EmailSubscription, TweetReply)


urlpatterns = patterns('',
                       url(r'^users/$', UserView.as_view()),
                       url(r'^users/(?P<pk>[0-9]+)/$', UserDetail.as_view()),
                       url(r'^users/register/$', UserRegistration.as_view()),
                       url(r'^tags/$', TagView.as_view()),
                       url(r'^tags/(?P<tag>[0-9A-Za-z]+)/$', TagDetailView.as_view()),
                       url(r'^tweets/$', TweetView.as_view()),
                       url(r'^tweets/(?P<pk>[0-9]+)/$', TweetDetailView.as_view()),
                       url(r'^subscribe/$', EmailSubscription.as_view()),
                       url(r'^tweet_reply/$', TweetReply.as_view()),
                       )

