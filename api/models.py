from __future__ import division
from django.db import models
from django.contrib.auth.models import User

class Tweet(models.Model):
    text = models.CharField(max_length=160)
    source = models.CharField(max_length=255)
    id_str = models.CharField(max_length=35, unique=True, db_index=True)
    created_at = models.DateTimeField()
    retweet_of = models.ForeignKey('self', related_name="retweets", blank=True, null=True)
    reply_to = models.ForeignKey('self', related_name="replies", blank=True, null=True)
    user = models.ForeignKey(User, related_name="tweets")

    modified = models.DateTimeField(auto_now=True)

class Tag(models.Model):
    name = models.CharField(max_length=160, unique=True, db_index=True)
    tweets = models.ManyToManyField(Tweet, related_name="tags", blank=True, null=True)

class UserProfile():
    user = models.OneToOneField(User, related_name="profile", unique=True, blank=True, null=True)
    twitter_name = models.CharField(max_length=100)
    twitter_id_str = models.CharField(max_length=30, unique=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)

User.profile = property(lambda u: u.get_profile())


