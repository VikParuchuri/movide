from __future__ import division
from django.contrib.auth.models import User
from models import Tag, Tweet, UserProfile
from rest_framework.views import APIView
from serializers import TagSerializer, TweetSerializer, UserSerializer, EmailSubscriptionSerializer, TweetReplySerializer
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.db.models import Q, Count
from django.http import Http404
import logging
from django.conf import settings
log = logging.getLogger(__name__)

class TagView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        tags= Tag.objects.filter(owner=request.user).order_by('-modified')
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = request.DATA
        serializer = TagSerializer(data=data, context={'request' : request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TagDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, tag):
        try:
            return Tag.objects.get(name=tag)
        except Tag.DoesNotExist:
            raise Http404

    def get(self, request, tag, format=None):
        tag = self.get_object(tag)
        serializer = TagSerializer(tag)
        return Response(serializer.data)

class TweetView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def filter_tag(self, queryset, tag):
        return queryset.filter(tags__name=tag)

    def filter_user(self, queryset, user):
        return queryset.filter(user=user)

    def get(self, request, format=None):
        tag = self.request.QUERY_PARAMS.get('tag', None)
        user = self.request.QUERY_PARAMS.get('user', None)
        if tag is None and user is None:
            error_msg = "Need to specify a username or a tag."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(tag, list):
            tag = tag[0]
        if isinstance(user, list):
            user = user[0]
        if user is not None and user.startswith("@"):
            user = user[1:]
        if tag is not None and tag.startswith("#"):
            tag = tag[1:]

        queryset = Tweet.objects.all()
        if tag is not None:
            queryset = self.filter_tag(queryset, tag)
        if user is not None:
            queryset = self.filter_user(queryset, user)
        serializer = TweetSerializer(queryset.order_by("-modified"), many=True)
        return Response(serializer.data)

class TweetDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Tweet.objects.get(pk=pk)
        except Tweet.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tag = self.get_object(pk)
        serializer = TweetSerializer(tag)
        return Response(serializer.data)

class UserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def filter_tag(self, queryset, tag):
        return queryset.filter(tags__name=tag)

    def get(self, request, format=None):
        tag = self.request.QUERY_PARAMS.get('tag', None)
        if tag is None:
            error_msg = "Need to specify a tag."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(tag, list):
            tag = tag[0]
        if tag.startswith("#"):
            tag = tag[1:]

        queryset = User.objects.all()
        if tag is not None:
            queryset = self.filter_tag(queryset, tag)
        serializer = UserSerializer(queryset.order_by("date_joined"), many=True)
        return Response(serializer.data)

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
        except Tweet.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tag = request.DATA.get('tag', None)
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        tag = request.DATA.get('tag', None)
        if tag is None:
            error_msg = "Need a tag in order to delete a model."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if tag.startswith("#"):
            tag = tag[1:]

        try:
            tag_model = Tag.objects.get(name=tag)
        except tag.DoesNotExist:
            error_msg = "Cannot find the specified tag."
            log.error(error_msg)
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        user.tags.remove(tag_model)

        return Response(status=status.HTTP_204_NO_CONTENT)

class UserRegistration(APIView):
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

class EmailSubscription(APIView):
    def post(self, request, format=None):
        serializer = EmailSubscriptionSerializer(data=request.DATA)
        if serializer.is_valid():

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

class TweetReply(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        if 'in_reply_to_id' not in request.DATA:
            request.DATA['in_reply_to_id'] = None
        serializer = TweetReplySerializer(data=request.DATA, context={'request' : request})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)
