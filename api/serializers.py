from django.forms import widgets
from rest_framework import serializers
from models import Tag, Tweet
from django.contrib.auth.models import User
import logging
log = logging.getLogger(__name__)

class TagSerializer(serializers.ModelSerializer):
    tweets = serializers.RelatedField(many=True)

    class Meta:
        model = Tag
        fields = ('name', 'tweets')

class TweetSerializer(serializers.ModelSerializer):
    retweet_count = serializers.Field(source="retweet_count")
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.RelatedField(many=True)
    user = serializers.Field(source="user.profile.twitter_name")

    class Meta:
        model = Tweet
        fields = ('text', 'source', 'created_at', 'retweet_of', 'reply_to', 'tags', 'user', 'reply_count', 'retweet_count')

class UserSerializer(serializers.Serializer):
    twitter_name = serializers.Field(source="profile.twitter_name")
    username = serializers.Field()
    tweets = serializers.RelatedField()
    pk = serializers.Field()
