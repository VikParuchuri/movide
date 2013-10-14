from django.conf.urls import patterns, url, include
from django.views.decorators.cache import cache_page
from django.conf import settings

from rest_framework import viewsets, routers
from views import (MessageView, MessageDetailView, ClassgroupView, ClassgroupDetailView,
                   UserView, UserDetail, EmailSubscription, MessageNotificationView, NotificationView,
                   ClassSettingsView, StudentClassSettingsView, ClassgroupStatsView, RatingView,
                   ResourceAuthorView, ResourceView, ResourceDetail, SkillView, SkillDetail,
                   SectionView, SectionDetail)


urlpatterns = patterns('',
                       url(r'^users/$', UserView.as_view()),
                       url(r'^users/(?P<pk>[0-9]+)/$', UserDetail.as_view()),
                       url(r'^classes/$', ClassgroupView.as_view(), name="class_list"),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/$', ClassgroupDetailView.as_view(), name='class_detail'),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/settings/$', ClassSettingsView.as_view(), name="class_settings"),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/student_settings/$', StudentClassSettingsView.as_view(), name="student_class_settings"),
                       url(r'^classes/(?P<classgroup>[0-9A-Za-z]+)/stats/$', ClassgroupStatsView.as_view(), name="class_stats"),
                       url(r'^messages/$', MessageView.as_view(), name="messages"),
                       url(r'^ratings/$', RatingView.as_view(), name="ratings"),
                       url(r'^messages/(?P<pk>[0-9]+)/$', MessageDetailView.as_view(), name="message_detail"),
                       url(r'^messages/notifications/$', MessageNotificationView.as_view(), name="message_notifications"),
                       url(r'^subscribe/$', EmailSubscription.as_view()),
                       url(r'^notifications/$', NotificationView.as_view(), name="notifications"),
                       url(r'^resources/author/$', ResourceAuthorView.as_view(), name="resource_author"),
                       url(r'^resources/$', ResourceView.as_view(), name='resources'),
                       url(r'^resources/(?P<pk>[0-9]+)/$', ResourceDetail.as_view(), name="resource_detail"),
                       url(r'^skills/$', SkillView.as_view(), name="skills"),
                       url(r'^skills/(?P<pk>[0-9]+)/$', SkillDetail.as_view(), name="skill_detail"),
                       url(r'^sections/$', SectionView.as_view(), name="sections"),
                       url(r'^sections/(?P<pk>[0-9]+)/$', SectionDetail.as_view(), name="section_detail"),
                       )

