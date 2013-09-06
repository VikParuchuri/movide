from __future__ import division
from models import Tweet, Tag, UserProfile
from datetime import datetime
from datetime import timedelta
from django.conf import settings
import logging
import functools
from django.core.cache import cache
from django.utils.timezone import now
from celery.task import periodic_task
from twython import TwythonStreamer
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
    fields = ["created_at", "text", "source", "id_str", "user_id", "retweet_id", "reply_id", "tags"]
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

    def retweet_id(self):
        if ['retweeted_status'] in self.data:
            return self.data['retweeted_status']['id_str']
        else:
            return None

    def reply_id(self):
        return self.data['in_reply_to_status_id_str']

    def tags(self):
        return self.data['entities']['hashtags']

class MovideStreamer(TwythonStreamer):
    def on_success(self, data):
        data = json.loads(data)
        parser = TwitterParser(data)
        user_id = parser.values['user_id']
        try:
            user = User.objects.get(profile__twitter_id_str=user_id)
        except User.DoesNotExist:
            log.exception("Cannot find user with id {0}".format(user_id))
            return
        tweet = Tweet(
            text=parser.values['text'],
            source=parser.values['source'],
            id_str=parser.values['id_str'],
            created_at=parser.values['created_at']
        )
        tweet.user = user

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

        for t in parser.values['tags']:
            tag, created = Tag.objects.get_or_create(name=t)
            if created:
                tag.save()
            tweet.tags.add(tag)
        tweet.save()

    def on_error(self, status_code, data):
        log.error("Disconnected with status {0}".format(status_code))
        self.disconnect()

@periodic_task(run_every=timedelta(seconds=settings.TWITTER_STREAM_EVERY))
@single_instance_task(settings.CACHE_TIMEOUT)
def post_updates():
    if settings.TWITTER_STREAM:
        stream = MovideStreamer(settings.TWITTER_APP_KEY, settings.TWITTER_SECRET_APP_KEY, settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_SECRET_ACCESS_TOKEN)
        stream.statuses.filter(track=settings.TWITTER_HASHTAG)