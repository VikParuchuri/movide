from __future__ import division
from models import Tweet, Tag, UserProfile
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

class TwitterParser():
    fields = ["created_at", "text", "source", "id_str", "user_id", "retweet_id", "reply_id", "tags", "user_name", "screen_name"]
    def __init__(self, data):
        self.data = data
        self.values = {}
        for f in self.fields:
            self.values[f] = getattr(self, f)()

    def created_at(self):
        datetime_string = "%a %b %d %H:%M:%S %z %Y"
        return datetime.strptime(self.data['created_at'], datetime_string)

    def text(self):
        return self.data['text']

    def source(self):
        return self.data['source']

    def id_str(self):
        return self.data['id_str']

    def user_id(self):
        return self.data['user']['id_str']

    def user_name(self):
        return self.data['user']['name']

    def screen_name(self):
        return self.data['user']['screen_name']

    def retweet_id(self):
        if ['retweeted_status'] in self.data:
            return self.data['retweeted_status']['id_str']
        else:
            return None

    def reply_id(self):
        return self.data['in_reply_to_status_id_str']

    def tags(self):
        return self.data['entities']['hashtags']

@task()
def save_tweet(data):
    data = json.loads(data)
    parser = TwitterParser(data)
    user_id = parser.values['user_id']
    screen_name = parser.values['screen_name']
    twitter_name = parser.values['user_name']
    try:
        user = User.objects.get(profile__twitter_id_str=user_id)
        user.profile.twitter_name = twitter_name
        user.profile.twitter_screen_name = screen_name
        user.profile.save()
    except User.DoesNotExist:
        log.exception("Cannot find user with id {0}".format(user_id))
        return

    tweet = Tweet(
        text=parser.values['text'],
        source=parser.values['source'],
        id_str=parser.values['id_str'],
        created_at=parser.values['created_at'],
        user=user,

        )

    tag_found = False
    for t in parser.values['tags']:
        try:
            tag = Tag.objects.get(name=t)
        except Tag.DoesNotExist:
            continue

        if tag in user.tags:
            tag_found = True
            tweet.tags.add(tag)

    if not tag_found:
        return

    reply_id = parser.values['reply_id']
    if reply_id is not None:
        try:
            reply = Tweet.objects.get(id_str=reply_id)
            tweet.reply_to = reply
        except Tweet.DoesNotExist:
            pass

    retweet_id = parser.values['retweet_id']
    if retweet_id is not None:
        try:
            retweet = Tweet.objects.get(id_str=retweet_id)
            tweet.retweet_of = retweet
        except Tweet.DoesNotExist:
            pass

    tweet.save()

class MovideStreamer(TwythonStreamer):
    def on_success(self, data):
        save_tweet.delay(data)

    def on_error(self, status_code, data):
        log.error("Disconnected with status {0}".format(status_code))
        self.disconnect()

@periodic_task(run_every=timedelta(seconds=settings.TWITTER_STREAM_EVERY))
@single_instance_task(settings.CACHE_TIMEOUT)
def post_updates():
    if settings.TWITTER_STREAM:
        stream = MovideStreamer(settings.TWITTER_APP_KEY, settings.TWITTER_SECRET_APP_KEY, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_SECRET_ACCESS_TOKEN)
        stream.statuses.filter(track=settings.TWITTER_HASHTAG)

@task()
@single_instance_task(settings.CACHE_TIMEOUT)
def create_user_profile(twitter_screen_name, user):
    if user.profile is not None:
        return
    twitter = Twython(settings.TWITTER_APP_KEY, settings.TWITTER_SECRET_APP_KEY, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_SECRET_ACCESS_TOKEN)
    user_data = twitter.show_user(screen_name=twitter_screen_name)
    user_data = json.loads(user_data)
    profile = UserProfile(
        user=user,
        twitter_screen_name=twitter_screen_name,
        twitter_name=user_data['name'],
        twitter_id_str=user_data['id_str'],
        twitter_profile_image=user_data['profile_image_url']
        )
    profile.save()