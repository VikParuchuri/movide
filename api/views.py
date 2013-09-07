from __future__ import division
from django.contrib.auth.models import User
from models import Tag, Tweet
from rest_framework.views import APIView
from serializers import TagSerializer, TweetSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.db.models import Q, Count
from django.http import Http404
import logging
from django.conf import settings

class TagView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        tags= Tag.objects.all().order_by('-modified')
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

        queryset = Tweet.objects.all()
        if tag is not None:
            queryset = self.filter_tag(queryset, tag)
        if user is not None:
            queryset = self.filter_user(queryset, user)
        serializer = TweetSerializer(queryset, many=True)
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

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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