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
    tweets = serializers.RelatedField(many=True, read_only=True, blank=True, null=True)
    users = UserField(many=True, slug_field='username', queryset=User.objects.all(), blank=True, null=True)
    owner = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all(), blank=True, null=True)
    name = serializers.CharField()
    modified = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        if instance is not None:
            if instance.owner != user:
                raise serializers.ValidationError("Tag is already taken.")

        name = attrs.get('name').encode('ascii', 'ignore')
        if not name.startswith("#"):
            name = "#" + name
        if instance is None:
            try:
                instance = Tag(owner=user, name=name)
                instance.save()
            except IntegrityError:
                raise serializers.ValidationError("Tag is already taken.")
        return instance

class TweetSerializer(serializers.ModelSerializer):
    retweet_count = serializers.Field(source="retweet_count")
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)
    user = serializers.SlugRelatedField(many=True, slug_field="username", read_only=True, blank=True, null=True)
    user_name = serializers.SlugRelatedField(many=True, slug_field="username", read_only=True, blank=True, null=True)
    retweet_of = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tweet
        fields = ('text', 'source', 'created_at', 'retweet_of', 'reply_to', 'tags', 'user', 'reply_count', 'retweet_count', 'user_name', )

class UserSerializer(serializers.Serializer):
    twitter_screen_name = serializers.Field(source="username")
    twitter_name = serializers.Field(source="profile.twitter_name")
    twitter_profile_image = serializers.Field(source="profile.twitter_profile_image")
    username = serializers.CharField()
    tweets = serializers.SlugRelatedField(many=True, slug_field="text", read_only=True, blank=True, null=True)
    pk = serializers.Field()

    def restore_object(self, attrs, instance=None):
        username = attrs.get('username')
        tag = self.context['request'].DATA.get('tag', None)
        if username.startswith("@"):
            username = username[1:]
        if not tag.startswith("#"):
            tag = "#" + tag
        try:
            instance = User.objects.get(username=username)
        except User.DoesNotExist:
            pass

        if not instance:
            try:
                password = User.objects.make_random_password(10)
                instance = User.objects.create_user(username=username, password=password)
            except IntegrityError:
                instance = User.objects.get(username=username)
        try:
            create_user_profile(username, instance)
        except Exception:
            error_msg = "Could not create a user profile."
            log.exception(error_msg)
            instance.delete()
            raise serializers.ValidationError(error_msg)

        try:
            if tag is not None:
                t = Tag.objects.get(name=tag)
                instance.tags.add(t)
                instance.save()
        except Tag.DoesNotExist:
            raise serializers.ValidationError("Invalid tag specified: {0}".format(tag))

        return instance
