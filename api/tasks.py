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

class TwitterParser(object):
    fields = ["created_at", "text", "source", "id_str", "user_id", "retweet_id", "reply_id", "tags", "user_name", "screen_name", "profile_image_url"]
    def __init__(self, data):
        self.data = data
        self.values = {}
        for f in self.fields:
            self.values[f] = getattr(self, f)()

    def created_at(self):
        return parser.parse(self.data['created_at'])

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
        if 'retweeted_status' in self.data:
            return self.data['retweeted_status']['id_str']
        else:
            return None

    def reply_id(self):
        return self.data['in_reply_to_status_id_str']

    def tags(self):
        hashtags = self.data['entities']['hashtags']
        return [t['text'] for t in hashtags]

    def profile_image_url(self):
        return self.data['user']['profile_image_url']

@task()
def save_tweet(data):
    parser = TwitterParser(data)
    user_id = parser.values['user_id']
    screen_name = parser.values['screen_name']
    twitter_name = parser.values['user_name']
    profile_image = parser.values['profile_image_url']
    try:
        user = User.objects.get(profile__twitter_id_str=user_id)
        user.profile.twitter_name = twitter_name
        user.profile.twitter_screen_name = screen_name
        user.profile.twitter_profile_image = profile_image
        user.profile.save()
        user.username = screen_name
        user.save()
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

    log.info("Got tweet {0} from user {1} and tags {2}".format(parser.values['text'], parser.values['screen_name'], parser.values['tags']))

    tag_found = False
    for t in parser.values['tags']:
        if t.startswith("#"):
            t = t[1:]
        try:
            tag = Tag.objects.get(name=t)
        except Tag.DoesNotExist:
            continue

        if tag in user.tags.all():
            tag_found = True
            tweet.save()
            tweet.tags.add(tag)

    if not tag_found:
        log.exception("Tags {0} could not be found in the list of tags.".format(parser.values['tags']))
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
        cache.delete("celery-single-instance-stream_tweets")

@periodic_task(run_every=timedelta(seconds=settings.TWITTER_STREAM_EVERY))
@single_instance_task(settings.TWITTER_STREAM_CACHE_TIMEOUT)
def stream_tweets():
    if settings.TWITTER_STREAM:
        stream = MovideStreamer(settings.TWITTER_APP_KEY, settings.TWITTER_SECRET_APP_KEY, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_SECRET_ACCESS_TOKEN)
        stream.statuses.filter(track=settings.TWITTER_HASHTAG)

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