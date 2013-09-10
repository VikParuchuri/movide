from __future__ import division
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from datetime import date
from dateutil.rrule import rrule, DAILY

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

    def twitter_screen_name(self):
        try:
            return self.user.profile.twitter_screen_name
        except UserProfile.DoesNotExist:
            return None

class Tag(models.Model):
    name = models.CharField(max_length=160, unique=True, db_index=True)
    tweets = models.ManyToManyField(Tweet, related_name="tags", blank=True, null=True)
    users = models.ManyToManyField(User, related_name="tags", blank=True, null=True)
    owner = models.ForeignKey(User, related_name="created_tags", blank=True, null=True, on_delete=models.SET_NULL)
    display_name = models.CharField(max_length=160)

    modified = models.DateTimeField(auto_now=True)

    def tweet_count(self):
        return self.tweets.all().count()

    def user_count(self):
        return self.users.all().count()

    def user_count_today(self):
        return self.tweets.filter(created_at__gt=now() - timedelta(days=1)).values('user').distinct().count()

    def tweet_count_today(self):
        return self.tweets.filter(created_at__gt=now() - timedelta(days=1)).count()

    def tweet_count_by_day(self):
        tweet_data = list(self.tweets.extra({'created' : "date(created_at)"}).values('created').annotate(created_count=Count('id')))
        day_counts = self.count_by_day(tweet_data)
        return day_counts

    def first_tweet_time(self):
        first_tweet = self.tweets.values('created_at').order_by("-created_at")[0]
        return min(self.modified.date(), first_tweet['created_at'].date()) - timedelta(days=2)

    def calculate_days(self, data, start, end):
        for dt in rrule(DAILY, dtstart=start, until=end):
            date_found = False
            dt_str = str(dt).split(" ")[0]
            for rec in data:
                if str(rec['created']) == dt_str:
                    date_found = True
                    break
            if date_found:
                continue
            data.append({'created_count' : 0, 'created' : dt_str})
        return data

    def count_by_day(self, objects):
        if len(objects) == 0:
            return []
        end = now().date()
        return self.calculate_days(objects, self.first_tweet_time(), end)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", unique=True, blank=True, null=True)
    twitter_name = models.CharField(max_length=100, blank=True, null=True)
    twitter_id_str = models.CharField(max_length=30, unique=True, db_index=True)
    twitter_screen_name = models.CharField(max_length=100, unique=True)
    twitter_profile_image = models.CharField(max_length=255, blank=True, null=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    oauth_token = models.CharField(max_length=200, blank=True, null=True)
    oauth_secret = models.CharField(max_length=200, blank=True, null=True)

class EmailSubscription(models.Model):
    email_address = models.EmailField(max_length=255, unique=True)
    modified = models.DateTimeField(auto_now=True)

User.profile = property(lambda u: u.get_profile())


