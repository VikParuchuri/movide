from __future__ import division
from django.contrib.auth.models import User
from models import (Tag, Message, UserProfile, Classgroup, MessageNotification,
                    RatingNotification, StudentClassSettings, Resource, UserResourceState)
from rest_framework.views import APIView
from serializers import (TagSerializer, MessageSerializer, UserSerializer,
                         EmailSubscriptionSerializer, ResourceSerializer,
                         ClassgroupSerializer, RatingSerializer, PaginatedMessageSerializer,
                         NotificationSerializer, PaginatedNotificationSerializer, StudentClassSettingsSerializer,
                         ClassSettingsSerializer, ClassgroupStatsSerializer, alphanumeric_name,
                         PaginatedResourceSerializer)
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework import status, generics, permissions
from django.db.models import Q, Count
from django.http import Http404
import logging
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import re
from django.views.generic.base import View
from dateutil import parser
from notifications import NotificationText
import datetime
import calendar
import pytz
import json
from django.forms.models import model_to_dict
from resources import ResourceRenderer
from permissions import ClassGroupPermissions
log = logging.getLogger(__name__)

RESULTS_PER_PAGE = 20

class QueryView(APIView):
    query_attributes = []
    required_attributes = []

    def get_query_params(self):
        self.query_dict = {}
        for attrib in self.query_attributes:
            val = self.request.QUERY_PARAMS.get(attrib, None)
            if val is not None:
                self.query_dict[attrib] = val
                if isinstance(self.query_dict[attrib], list):
                    self.query_dict[attrib] = self.query_dict[attrib][0]
        for attrib_set in self.required_attributes:
            has_value = 0
            for attrib in attrib_set:
                if attrib in self.query_dict and self.query_dict[attrib] is not None:
                    has_value += 1
            if has_value == 0:
                error_msg = "Need to specify {0}.".format(attrib_set)
                log.error(error_msg)
                raise PermissionDenied(error_msg)

    def get_post_params(self):
        self.post_dict = {}
        for attrib in self.post_attributes:
            val = self.request.POST.get(attrib, None)
            if val is not None:
                self.post_dict[attrib] = val
        for attrib_set in self.required_attributes:
            has_value = 0
            for attrib in attrib_set:
                if attrib in self.post_dict and self.post_dict[attrib] is not None:
                    has_value += 1
            if has_value == 0:
                error_msg = "Need to specify {0}.".format(attrib_set)
                log.error(error_msg)
                raise PermissionDenied(error_msg)

    def filter_query_params(self, queryset):
        for attrib in self.query_attributes:
            if attrib in self.query_dict:
                val = self.query_dict[attrib]
                if val is not None:
                    queryset = getattr(self, "filter_" + attrib)(queryset, val)
        return queryset

    def verify_user(self):
        if "user" in self.query_dict and "classgroup" not in self.query_dict:
            if self.request.user.username != self.query_dict['user']:
                error_msg = "User {0} for query does not match queried user {1}.".format(self.request.user.username, self.query_dict['user'])
                log.error(error_msg)
                raise PermissionDenied(error_msg)

    def verify_classgroup(self):
        if "classgroup" in self.query_dict:
            cg = Classgroup.objects.get(name=self.query_dict['classgroup'])
            if not ClassGroupPermissions.is_student(cg, self.request.user):
                error_msg = "Attempting to query a class that you are not part of."
                log.error(error_msg)
                raise PermissionDenied(error_msg)

    def verify_membership(self):
        try:
            self.cg = Classgroup.objects.get(name=self.query_dict['classgroup'])
        except Classgroup.DoesNotExist:
            error_msg = "Invalid class name given."
            log.error(error_msg)
            raise PermissionDenied(error_msg)

        if not ClassGroupPermissions.is_student(self.cg, self.request.user):
            error_msg = "User not authorized to see given class."
            log.error(error_msg)
            raise PermissionDenied(error_msg)

    def verify_ownership(self):
        if not ClassGroupPermissions.is_teacher(self.cg, self.request.user):
            error_msg = "User is not a teacher for the given class."
            log.error(error_msg)
            raise PermissionDenied(error_msg)

class ClassgroupView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        owned_classgroups = list(Classgroup.objects.filter(owner=request.user).order_by('-modified'))
        participating_classgroups = [l for l in list(request.user.classgroups.all()) if l not in owned_classgroups]
        serializer = ClassgroupSerializer(owned_classgroups + participating_classgroups, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ClassgroupSerializer(data=request.DATA, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RatingView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        serializer = RatingSerializer(data=request.DATA, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClassgroupDetailView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, classgroup, format=None):
        self.query_dict = {
            'classgroup': classgroup
        }
        self.verify_membership()

        serializer = ClassgroupSerializer(self.cg)
        if self.cg.class_settings is not None:
            serializer.data['class_settings'] = ClassSettingsSerializer(self.cg.class_settings).data
        return Response(serializer.data)

def add_likes_to_data(data, user):
    for m in data:
        m['has_been_rated'] = (user.ratings.filter(message__id=m['pk']).count() > 0)
    return data

class MessageView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["tag", "classgroup", "user", "in_reply_to_id", "message_type",]
    required_attributes = [("classgroup", "user"),]

    def filter_tag(self, queryset, tag):
        return queryset.filter(tags__name=tag)

    def filter_user(self, queryset, user):
        return queryset.filter(user__username=user)

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(classgroup__name=classgroup)

    def filter_in_reply_to_id(self, queryset, in_reply_to_id):
        return queryset.filter(reply_to=in_reply_to_id)

    def filter_message_type(self, queryset, message_type):
        return queryset.filter(message_type=message_type)

    def get(self, request, format=None):
        self.get_query_params()
        self.verify_user()
        self.verify_classgroup()

        queryset = Message.objects.all()
        if "in_reply_to_id" not in self.query_dict :
            queryset = queryset.filter(reply_to__isnull=True)
        queryset = self.filter_query_params(queryset).order_by("-modified")
        paginator = Paginator(queryset, RESULTS_PER_PAGE)

        page = request.QUERY_PARAMS.get("page")

        try:
            serializer = PaginatedMessageSerializer(paginator.page(page), context={'request' : request})
            add_likes_to_data(serializer.data['results'], request.user)
        except PageNotAnInteger:
            serializer = MessageSerializer(queryset, context={'request': request}, many=True)
            add_likes_to_data(serializer.data, request.user)
        except EmptyPage:
            serializer = PaginatedMessageSerializer(paginator.page(paginator.num_pages), context={'request' : request})
            add_likes_to_data(serializer.data['results'], request.user)

        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup"]
    required_attributes = [("classgroup",),]

    def filter_user(self, queryset, user):
        return queryset.filter(receiving_user__username=user)

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(receiving_message__classgroup__name=classgroup)

    def get(self, request, format=None):
        self.get_query_params()
        self.verify_classgroup()

        message_notifications = MessageNotification.objects.all()
        message_notifications = self.filter_query_params(message_notifications).filter(receiving_user=request.user).order_by("-modified")

        rating_notifications = RatingNotification.objects.all()
        rating_notifications = self.filter_query_params(rating_notifications).filter(receiving_user=request.user).order_by("-modified")

        notifications = list(message_notifications) + list(rating_notifications)
        for n in notifications:
            if not n.cleared:
                n.cleared = True
                n.save()
        notification_text = NotificationText(notifications)
        notification_text.generate_text()
        messages = notification_text.get_messages()
        messages.sort(key=lambda x: x['notification'].created, reverse=True)
        message_objects = []
        for i,m in enumerate(messages):
            m['message'].notification_text = m['notification_text']
            m['message'].notification_created = m['notification'].created
            m['message'].notification_created_timestamp = calendar.timegm(m['notification'].created.utctimetuple())
            message_objects.append(m['message'])
        paginator = Paginator(message_objects, RESULTS_PER_PAGE)

        page = request.QUERY_PARAMS.get("page")
        if page is None:
            page = 1

        try:
            paginator_page = paginator.page(page)
        except PageNotAnInteger:
            paginator_page = paginator.page(1)
        except EmptyPage:
            paginator_page = paginator.page(paginator.num_pages)

        serializer = PaginatedNotificationSerializer(paginator_page, context={'request' : request})

        return Response(serializer.data)

class MessageDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Message.objects.get(pk=pk)
        except Message.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        message = self.get_object(pk)
        if request.user == message.user:
            serializer = MessageSerializer(message)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        message = self.get_object(pk)

        if not ClassGroupPermissions.is_teacher(message.classgroup, request.user):
            error_msg = "User not authorized to delete this message."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        message.classgroup = None
        message.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

class UserView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup",]
    required_attributes = [("classgroup",),]

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(classgroups__name=classgroup)

    def get(self, request, format=None):
        self.get_query_params()
        self.verify_membership()

        queryset = User.objects.all()
        queryset = self.filter_query_params(queryset)
        serializer = UserSerializer(queryset.order_by("date_joined"), many=True)
        serializer = self.add_user_data(serializer)
        return Response(serializer.data)

    def add_user_data(self, serializer):
        for user in serializer.data:
            user['message_count_today'] = Classgroup.objects.get(name=self.query_dict['classgroup']).messages.filter(user=user['pk'], modified__gt=now() - timedelta(days=1)).count()
            user['message_count'] = Classgroup.objects.get(name=self.query_dict['classgroup']).messages.filter(user=user['pk']).count()
            user['role'] = ClassGroupPermissions.access_level(self.cg, User.objects.get(id=user['pk']))
        return serializer

    def post(self, request, format=None):
        username = self.request.DATA.get('username', None)
        if username is None:
            error_msg = "Need to specify a username."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        if user == request.user:
            serializer = UserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        classgroup = request.DATA.get('classgroup', None)
        if classgroup is None:
            error_msg = "Need a classgroup in order to delete a user."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if classgroup.startswith("#"):
            classgroup = classgroup[1:]

        try:
            classgroup_model = Classgroup.objects.get(name=classgroup)
        except Classgroup.DoesNotExist:
            error_msg = "Cannot find the specified tag."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        if not ClassGroupPermissions.is_teacher(classgroup_model, request.user):
            error_msg = "User not authorized to delete others."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        user.classgroups.remove(classgroup_model)

        return Response(status=status.HTTP_204_NO_CONTENT)

class EmailSubscription(APIView):
    def post(self, request, format=None):
        serializer = EmailSubscriptionSerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

class MessageNotificationView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup", "start_time",]
    required_attributes = [("classgroup",),("start_time",)]

    def get(self, request):
        self.get_query_params()
        self.verify_membership()

        start_time = datetime.datetime.utcfromtimestamp(int(self.query_dict['start_time']))
        start_time = start_time.replace(tzinfo=pytz.utc)
        messages = Message.objects.filter(classgroup=self.cg, created__gt=start_time, reply_to__isnull=True)

        return Response({'message_count': max(0,messages.count()-1)})

class StudentClassSettingsView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, classgroup):
        self.query_dict = {'classgroup': classgroup}
        self.verify_membership()
        settings, created = StudentClassSettings.objects.get_or_create(user=request.user, classgroup=self.cg)

        serializer = StudentClassSettingsSerializer(settings, context={'request' : request})
        return Response(serializer.data)

class ClassSettingsView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, classgroup):
        self.query_dict = {'classgroup': classgroup}
        self.verify_membership()

        if not ClassGroupPermissions.is_teacher(self.cg, request.user):
            error_msg = "You are not a teacher in this class, and cannot edit class settings."
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        settings = self.cg.class_settings

        serializer = ClassSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)

class ClassgroupStatsView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, classgroup, format=None):
        self.query_dict = {'classgroup': classgroup}
        self.verify_membership()

        serializer = ClassgroupStatsSerializer(self.cg, context={'request': request})
        return Response(serializer.data)

class ResourceDetail(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    post_attributes = ["action", "data"]

    def get_object(self, pk):
        return Resource.objects.get(pk=pk)

    def get(self, request, pk):
        view_type = request.GET.get('view_type', 'user')
        resource = self.get_object(pk)
        self.query_dict = {
            'classgroup': resource.classgroup.name
        }
        self.verify_membership()

        if view_type == "user":
            user_state, created = UserResourceState.objects.get_or_create(
                user=request.user,
                resource=resource
            )

            renderer = ResourceRenderer(resource, user_state, static_data={
                'request': request,
            })

            html = renderer.user_view().get_html()
        else:
            self.verify_ownership()
            renderer = ResourceRenderer(resource, static_data={
                'request': request,
                'author_post_link': '/api/resources/author/'
                })

            html = renderer.author_view().get_html()

        return Response({'html': html, 'display_name': resource.display_name})

    def delete(self, request, pk):
        resource = self.get_object(pk)
        self.query_dict = {
            'classgroup': resource.classgroup.name
        }
        self.verify_membership()
        self.verify_ownership()

        resource.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, pk):
        resource = self.get_object(pk)
        self.query_dict = {
            'classgroup': resource.classgroup.name
        }
        self.verify_membership()
        self.get_post_params()

        user_state, created = UserResourceState.objects.get_or_create(
            user=request.user,
            resource=resource
        )

        data = {}
        for k in request.POST:
            if k.endswith("[]"):
                data[k.replace("[]", "")] = request.POST.getlist(k)
            else:
                data[k] = request.POST[k]

        data = json.dumps(data)

        renderer = ResourceRenderer(resource, user_state, static_data={
            'request': request,
            })
        ajax_response = renderer.handle_ajax(self.post_dict['action'], data)
        return Response(ajax_response)

class ResourceView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup"]
    required_attributes = [("classgroup",), ]
    post_attributes = ["resource_type"]

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(classgroup__name=classgroup)

    def get(self, request):
        self.get_query_params()
        self.verify_membership()
        queryset = Resource.objects.all()
        queryset = self.filter_query_params(queryset).filter(name__isnull=False, resource_type="vertical").order_by("-created")
        paginator = Paginator(queryset, RESULTS_PER_PAGE)
        page = request.QUERY_PARAMS.get("page")

        try:
            serializer = PaginatedResourceSerializer(paginator.page(page), context={'request' : request})
        except PageNotAnInteger:
            serializer = ResourceSerializer(queryset, context={'request': request}, many=True)
        except EmptyPage:
            serializer = PaginatedResourceSerializer(paginator.page(paginator.num_pages), context={'request' : request})

        return Response(serializer.data)


    def post(self, request):
        self.query_dict = {
            'classgroup': request.DATA.get('classgroup')
        }

        self.verify_membership()

        resource_type=request.DATA.get('resource_type')

        if resource_type != "vertical":
            raise Http404

        resource = Resource(
            resource_type=resource_type,
            user=request.user,
            classgroup=self.cg
        )
        resource.save()

        renderer = ResourceRenderer(resource, static_data={
            'request': request,
            'author_post_link': '/api/resources/author/'
        })

        html = renderer.author_view().get_html()

        return Response({'html': html, 'display_name': resource.display_name})

class ResourceAuthorView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup", "resource_type", "vertical_id"]
    required_attributes = [("classgroup",), ("resource_type",), ]
    post_attributes = ["classgroup", "resource_type", "csrfmiddlewaretoken", "resource_id"]

    def get(self, request):
        self.get_query_params()
        self.verify_membership()

        parent = Resource.objects.get(pk=int(self.query_dict['vertical_id']))
        resource = Resource(
            user=request.user,
            classgroup=self.cg,
            resource_type=self.query_dict['resource_type'],
            parent=parent
        )
        resource.save()

        renderer = ResourceRenderer(resource, static_data={
            'request': request,
            'author_post_link': '/api/resources/author/'
        })

        html = renderer.author_view().get_html()

        return Response({'html': html, 'display_name': resource.display_name})

    def post(self, request):
        self.get_post_params()
        self.query_dict = {
            'classgroup': self.post_dict['classgroup']
        }
        self.verify_membership()

        data = json.dumps({k:request.POST[k] for k in request.POST if k not in self.post_attributes})

        resource_id = self.post_dict.get('resource_id')
        if resource_id is None:
            resource = Resource(
                user=request.user,
                classgroup=self.cg,
                resource_type=self.post_dict['resource_type'],
                data=data
            )
        else:
            resource = Resource.objects.get(
                pk=int(resource_id)
            )

        renderer = ResourceRenderer(resource, static_data={
            'request': request,
            'author_post_link': '/api/resources/author/'
        })
        response = renderer.handle_ajax("save_form_values", data)
        renderer.save_module_data()

        resource.display_name = renderer.module.name
        resource.name = alphanumeric_name(renderer.module.name)
        resource.save()

        return Response(response,status=status.HTTP_201_CREATED)
