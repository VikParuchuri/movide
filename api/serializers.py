from django.forms import widgets
from rest_framework import serializers
from models import Tag, Tweet, UserProfile
from django.contrib.auth.models import User
from django.db import IntegrityError
from tasks import create_user_profile
import logging
log = logging.getLogger(__name__)

class UserField(serializers.SlugRelatedField):
    def from_native(self, data):
        serializer = UserSerializer(data=data)
        serializer.save()
        return super(UserField, self).from_native(data)

class TagSerializer(serializers.Serializer):
    tweets = serializers.RelatedField(many=True, read_only=True)
    users = UserField(many=True, slug_field='profile.twitter_screen_name', queryset=User.objects.all())
    owner = serializers.SlugRelatedField(slug_file="profile.twitter_screen_name", queryset=User.objects.all())
    name = serializers.CharField()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        if instance is not None:
            if instance.owner != user:
                raise serializers.ValidationError("Tag already taken.")

        if instance is None:
            tag = Tag(owner=user, name=attrs.get('name'))
            tag.save()

class TweetSerializer(serializers.ModelSerializer):
    retweet_count = serializers.Field(source="retweet_count")
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)
    user = serializers.SlugRelatedField(many=True, slug_field="profile.twitter_screen_name", read_only=True)
    user_name = serializers.SlugRelatedField(many=True, slug_field="profile.twitter_name", read_only=True)
    retweet_of = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tweet
        fields = ('text', 'source', 'created_at', 'retweet_of', 'reply_to', 'tags', 'user', 'reply_count', 'retweet_count', 'user_name', )

class UserSerializer(serializers.Serializer):
    twitter_screen_name = serializers.Field(source="profile.twitter_screen_name")
    twitter_name = serializers.Field(source="profile.twitter_name")
    username = serializers.CharField()
    tweets = serializers.RelatedField()
    pk = serializers.Field()

    def restore_object(self, attrs, instance=None):
        username = attrs.get('username')
        if username.startswith("@"):
            username = username[1:]
        try:
            instance = User.objects.get(profile__twitter_screen_name=username)
        except User.DoesNotExist:
            pass

        if not instance:
            try:
                password = User.objects.make_random_password(10)
                instance = User.objects.create_user(username=username, password=password)
            except IntegrityError:
                instance = User.objects.get(username=username)
            if instance.profile is not None:
                return instance
        try:
            create_user_profile(username, instance)
        except Exception:
            instance.delete()
            raise serializers.ValidationError("Could not create a user profile.")

        return instance
