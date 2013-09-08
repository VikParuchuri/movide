from __future__ import division
from django.contrib.auth.models import User
from models import Tag, Tweet, UserProfile
from rest_framework.views import APIView
from serializers import TagSerializer, TweetSerializer, UserSerializer
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

    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tag = self.get_object(pk)
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serialized = UserSerializer(data=request.DATA, context={'request' : request})
        if serialized.is_valid():
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserRegistration(APIView):
    def post(self, request, format=None):
        serialized = UserSerializer(data=request.DATA)
        if serialized.is_valid():
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)