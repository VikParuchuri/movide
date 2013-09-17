from __future__ import division
from models import Message, Tag, UserProfile
from datetime import datetime
from datetime import timedelta
from django.conf import settings
import logging
import functools
from django.core.cache import cache
from django.utils.timezone import now
from celery.task import periodic_task, task
from twython import TwythonStreamer, Twython
import json
from django.contrib.auth.models import User
from dateutil import parser

log=logging.getLogger(__name__)

def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()
        return wrapper
    return task_exc

@task()
def create_user_profile_task(twitter_screen_name, user_id):
    user = User.objects.get(id=user_id)
    user_data = UserTwitterData(twitter_screen_name)
    user_data.create_profile(user)

class UserTwitterData(object):
    def __init__(self, screen_name):
        if screen_name.startswith("@"):
            screen_name = screen_name[1:]
        screen_name = screen_name.lower()
        self.screen_name = screen_name
        self.twitter = Twython(settings.TWITTER_APP_KEY, settings.TWITTER_SECRET_APP_KEY, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_SECRET_ACCESS_TOKEN)
        self.get_data()

    def get_data(self):
        self.user_data = self.twitter.show_user(screen_name=self.screen_name)

    @property
    def id_str(self):
        return self.user_data['id_str']

    def create_profile(self, user):
        try:
            profile = UserProfile.objects.get(user=user)
            return
        except UserProfile.DoesNotExist:
            pass

        profile = UserProfile(
            user=user,
            twitter_screen_name=self.screen_name,
            twitter_name=self.user_data['name'],
            twitter_id_str=self.user_data['id_str'],
            twitter_profile_image=self.user_data['profile_image_url']
        )
        profile.save()
        return profile

class UserTweet(object):
    def __init__(self, user):
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            error_msg = "Cannot find a profile for user {0}".format(user)
            log.error(error_msg)
            raise UserProfile.DoesNotExist(error_msg)

        if profile.oauth_token is None or profile.oauth_secret is None:
            error_msg = "Cannot find oauth tokens or secrets for user {0}".format(user)
            log.error(error_msg)
            raise ValueError(error_msg)

        self.twitter = Twython(settings.TWITTER_AUTH_APP_KEY, settings.TWITTER_AUTH_SECRET_APP_KEY, profile.oauth_token, profile.oauth_secret)

    def post_reply(self, tweet_text, reply_to_id):
        self.twitter.update_status(status=tweet_text, in_reply_to_status_id=reply_to_id)

    def post_tweet(self, tweet_text):
        self.twitter.update_status(status=tweet_text)