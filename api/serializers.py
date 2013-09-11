from django.forms import widgets
from rest_framework import serializers
from models import Tag, Tweet, UserProfile, EmailSubscription
from django.contrib.auth.models import User
from django.db import IntegrityError
from tasks import UserTwitterData, UserTweet
import logging
from django.conf import settings
log = logging.getLogger(__name__)

class EmailSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSubscription
        fields = ("email_address", )

class UserField(serializers.SlugRelatedField):
    def from_native(self, data):
        serializer = UserSerializer(data=data)
        serializer.save()
        return super(UserField, self).from_native(data)

class TagSerializer(serializers.Serializer):
    pk = serializers.Field()
    users = UserField(many=True, slug_field='username', queryset=User.objects.all(), blank=True, null=True)
    owner = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all(), blank=True, null=True)
    tweet_count = serializers.Field(source="tweet_count")
    tweet_count_today = serializers.Field(source="tweet_count_today")
    user_count = serializers.Field(source="user_count")
    user_count_today = serializers.Field(source="user_count_today")
    tweet_count_by_day = serializers.Field(source="tweet_count_by_day")
    display_name = serializers.Field()
    name = serializers.CharField()
    modified = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        if instance is not None:
            if instance.owner != user:
                raise serializers.ValidationError("Tag is already taken.")

        name = attrs.get('name').encode('ascii', 'ignore')
        if name.startswith("#"):
            name = name[1:]

        if instance is None:
            try:
                instance = Tag(owner=user, name=name.lower(), display_name=name)
                instance.save()
                user.tags.add(instance)
                user.save()
            except IntegrityError:
                raise serializers.ValidationError("Tag is already taken.")
        return instance

class TagInformationSerializer(serializers.Serializer):
    pk = serializers.Field()
    network_info = serializers.Field(source="network_info")
    display_name = serializers.Field()
    name = serializers.CharField()
    modified = serializers.Field()

class TweetSerializer(serializers.ModelSerializer):
    pk = serializers.Field()
    retweet_count = serializers.Field(source="retweet_count")
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)
    user = serializers.SlugRelatedField(many=True, slug_field="username", read_only=True, blank=True, null=True)
    user_name = serializers.Field(source="twitter_name")
    user_screen_name = serializers.Field(source="twitter_screen_name")
    user_twitter_profile_image = serializers.Field(source="profile_image")
    retweet_of = serializers.PrimaryKeyRelatedField(read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tweet
        fields = (
                'text', 'source', 'created_at', 'retweet_of', 'reply_to',
                'tags', 'reply_count', 'retweet_count', 'user_name',
                'user_twitter_profile_image', 'pk', 'user_screen_name',
        )

class TweetReplySerializer(serializers.Serializer):
    tweet_text = serializers.CharField()
    in_reply_to_id = serializers.CharField()
    tag = serializers.CharField()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        in_reply_to_id = attrs.get('in_reply_to_id')
        tweet_text = attrs.get('tweet_text')
        tag = attrs.get('tag')
        if tag.startswith("#"):
            tag = tag[1:]

        user_tweet = UserTweet(user)

        try:
            tag = Tag.objects.get(name=tag)
        except Tag.DoesNotExist:
            raise serializers.ValidationError("Could not find the tag that this was posted from!")

        if len(tweet_text) < 1:
            raise serializers.ValidationError("Need to enter an actual reply.")

        if settings.TWITTER_HASHTAG not in tweet_text.lower():
            tweet_text = tweet_text + " " + settings.TWITTER_HASHTAG
        if tag.name not in tweet_text.lower():
            tweet_text = tweet_text + " #" + tag.name

        if in_reply_to_id is not None:
            try:
                tweet = Tweet.objects.get(id=int(in_reply_to_id))
                tweet_screen_name = tweet.user.profile.twitter_screen_name
            except Tweet.DoesNotExist:
                raise serializers.ValidationError("The given tweet for this reply id does not exist.")
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("Cannot find a twitter screen name for the tweet you are replying to.")
            if not tweet_screen_name.startswith("@"):
                tweet_screen_name = "@" + tweet_screen_name
            if tweet_screen_name.lower() not in tweet_text.lower():
                tweet_text = tweet_screen_name + " " + tweet_text
            user_tweet.post_reply(tweet_text, tweet.id_str)
        else:
            user_tweet.post_tweet(tweet_text)

        return instance

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
        if tag is not None and tag.startswith("#"):
            tag = tag[1:]

        user_data = UserTwitterData(username)
        try:
            instance = User.objects.get(profile__twitter_id_str=user_data.id_str)
        except User.DoesNotExist:
            pass

        if not instance:
            try:
                password = User.objects.make_random_password(10)
                instance = User.objects.create_user(username=username, password=password)
            except IntegrityError:
                instance = User.objects.get(username=username)

            try:
                user_data.create_profile(instance)
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
