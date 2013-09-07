from __future__ import division
from django.db import models
from django.contrib.auth.models import User

class Tweet(models.Model):
    text = models.CharField(max_length=160)
    source = models.CharField(max_length=255)
    id_str = models.CharField(max_length=35, unique=True, db_index=True)
    created_at = models.DateTimeField()
    retweet_of = models.ForeignKey('self', related_name="retweets", blank=True, null=True, on_delete=models.SET_NULL)
    reply_to = models.ForeignKey('self', related_name="replies", blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, related_name="tweets")

    modified = models.DateTimeField(auto_now=True)

    def retweet_count(self):
        return self.retweets.count()

    def reply_count(self):
        return self.replies.count()

    def profile_image(self):
        try:
            return self.user.profile.twitter_profile_image
        except UserProfile.DoesNotExist:
            return None

    def twitter_name(self):
        try:
            return self.user.profile.twitter_name
        except UserProfile.DoesNotExist:
            return None

class Tag(models.Model):
    name = models.CharField(max_length=160, unique=True, db_index=True)
    tweets = models.ManyToManyField(Tweet, related_name="tags", blank=True, null=True)
    users = models.ManyToManyField(User, related_name="tags", blank=True, null=True)
    owner = models.ForeignKey(User, related_name="created_tags", blank=True, null=True, on_delete=models.SET_NULL)

    modified = models.DateTimeField(auto_now=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", unique=True, blank=True, null=True)
    twitter_name = models.CharField(max_length=100, blank=True, null=True)
    twitter_id_str = models.CharField(max_length=30, unique=True, db_index=True)
    twitter_screen_name = models.CharField(max_length=100, unique=True)
    twitter_profile_image = models.CharField(max_length=255, blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    oauth_token = models.CharField(max_length=200, blank=True, null=True)
    oauth_secret = models.CharField(max_length=200, blank=True, null=True)

User.profile = property(lambda u: u.get_profile())


