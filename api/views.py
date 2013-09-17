from __future__ import division
from django.contrib.auth.models import User
from models import Tag, Message, UserProfile, Classgroup
from rest_framework.views import APIView
from serializers import (TagSerializer, MessageSerializer, UserSerializer,
                         EmailSubscriptionSerializer, ResourceSerializer,
                         ClassgroupSerializer, RatingSerializer)
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.db.models import Q, Count
from django.http import Http404
import logging
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
log = logging.getLogger(__name__)
import re

class QueryView(APIView):
    query_attributes = []
    required_attributes = []

    def get_query_params(self):
        self.query_dict = {}
        for attrib in self.query_attributes:
            self.query_dict[attrib] = self.request.QUERY_PARAMS.get(attrib, None)
            if isinstance(self.query_dict[attrib], list):
                self.query_dict[attrib] = self.query_dict[attrib][0]
        for attrib_set in self.required_attributes:
            has_value = 0
            for attrib in attrib_set:
                if self.query_dict[attrib] is not None:
                    has_value += 1
            if has_value == 0:
                error_msg = "Need to specify {0}.".format(attrib_set)
                log.error(error_msg)
                return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

    def filter_query_params(self, queryset):
        for attrib in self.query_attributes:
            val = self.query_dict[attrib]
            if val is not None:
                queryset = getattr(self, "filter_" + attrib)(queryset, val)
        return queryset

class ClassgroupView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        classgroups = Classgroup.objects.filter(owner=request.user).order_by('-modified')
        serializer = ClassgroupSerializer(classgroups, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ClassgroupSerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClassgroupDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, classgroup):
        try:
            return Classgroup.objects.get(name=classgroup)
        except Tag.DoesNotExist:
            raise Http404

    def get(self, request, classgroup, format=None):
        classgroup = self.get_object(classgroup)
        if classgroup.owner != request.user:
            error_msg = "Class owner is not the user making the request."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = ClassgroupSerializer(classgroup)
        return Response(serializer.data)

class MessageView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["tag", "classgroup", "user"]
    required_attributes = [("classgroup", "user"),]

    def filter_tag(self, queryset, tag):
        return queryset.filter(tags__name=tag)

    def filter_user(self, queryset, user):
        return queryset.filter(user=user)

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(classgroup__name=classgroup)

    def get(self, request, format=None):
        self.get_query_params()

        queryset = Message.objects.all()
        queryset = self.filter_query_params(queryset)
        serializer = MessageSerializer(queryset.order_by("-modified"), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MessageSerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

class MessageDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Message.objects.get(pk=pk)
        except Message.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        message = self.get_object(pk)
        serializer = MessageSerializer(message)
        return Response(serializer.data)

class UserView(QueryView):
    permission_classes = (permissions.IsAuthenticated,)
    query_attributes = ["classgroup",]
    required_attributes = [("classgroup",),]

    def filter_classgroup(self, queryset, classgroup):
        return queryset.filter(classgroups__name=classgroup)

    def get(self, request, format=None):
        self.get_query_params()

        queryset = User.objects.all()
        queryset = self.filter_query_params(queryset)
        serializer = UserSerializer(queryset.order_by("date_joined"), many=True)
        serializer = self.add_user_data(serializer)
        return Response(serializer.data)

    def add_user_data(self, serializer):
        for user in serializer.data:
            user['message_count_today'] = Classgroup.objects.get(name=self.query_dict['classgroup']).messages.filter(user=user['pk'], modified__gt=now() - timedelta(days=1)).count()
            user['message_count'] = Classgroup.objects.get(name=self.query_dict['classgroup']).messages.filter(user=user['pk']).count()
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
        serializer = UserSerializer(user)
        return Response(serializer.data)

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
