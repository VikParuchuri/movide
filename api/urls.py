from django.conf.urls import patterns, url, include
from django.views.decorators.cache import cache_page
from django.conf import settings

from rest_framework import viewsets, routers
from views import (MessageView, MessageDetailView, ClassgroupView, ClassgroupDetailView,
                   UserView, UserDetail, EmailSubscription, MessageNotificationView, NotificationView,
                   ClassSettingsView, StudentClassSettingsView, ClassgroupStatsView, RatingView)


urlpatterns = patterns('',
                       url(r'^users/$', UserView.as_view()),
                       url(r'^users/(?P<pk>[0-9]+)/$', UserDetail.as_view()),
                       url(r'^classes/$', ClassgroupView.as_view(), name="class_list"),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/$', ClassgroupDetailView.as_view()),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/settings/$', ClassSettingsView.as_view()),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/student_settings/$', StudentClassSettingsView.as_view()),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/stats/$', ClassgroupStatsView.as_view()),
                       url(r'^messages/$', MessageView.as_view()),
                       url(r'^ratings/$', RatingView.as_view()),
                       url(r'^messages/(?P<pk>[0-9]+)/$', MessageDetailView.as_view()),
                       url(r'^messages/notifications/$', MessageNotificationView.as_view()),
                       url(r'^subscribe/$', EmailSubscription.as_view()),
                       url(r'^notifications/$', NotificationView.as_view()),
                       )

