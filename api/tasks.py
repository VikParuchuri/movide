from __future__ import division
from datetime import datetime
from datetime import timedelta
from django.conf import settings
import logging
import functools
from django.core.cache import cache
from django.utils.timezone import now
from celery.task import periodic_task, task
from models import Message
from django.db import transaction
from nltk.tokenize import word_tokenize, sent_tokenize, RegexpTokenizer
from itertools import chain
from django.contrib.auth.models import User
from models import Resource, Tag, MessageNotification
from django.db import IntegrityError

log=logging.getLogger(__name__)

class MentionFinder(object):
    def __init__(self):
        pass

    def process_message(self, message):
        if message.processed:
            return

        text = message.text
        tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')
        tokens = tokenizer.tokenize(text)
        for t in tokens:
            t_end = t[1:]
            if t.startswith("@"):
                try:
                    user = User.objects.get(username__iexact=t_end)
                    message.mentions.add(user)

                    if user != message.user:
                        try:
                            if message.reply_to is None:
                                MessageNotification.objects.get_or_create(
                                    receiving_message=message,
                                    receiving_user=user,
                                    origin_message=message,
                                    notification_type="mention_in_message",
                                    )
                            else:
                                MessageNotification.objects.get_or_create(
                                    receiving_message=message.reply_to,
                                    receiving_user=user,
                                    origin_message=message,
                                    notification_type="mention_in_reply",
                                    )
                        except IntegrityError:
                            pass

                except User.DoesNotExist:
                    pass
            elif t.startswith("#"):
                try:
                    tag = Tag.objects.get(name__iexact=t_end)
                    message.tags.add(tag)
                except Tag.DoesNotExist:
                    pass
            elif t.startswith("*"):
                try:
                    resource = Resource.objects.get(name__iexact=t_end)
                    message.resources.add(resource)
                except Resource.DoesNotExist:
                    pass

        message.processed = True

    def process_messages(self, messages):
        for m in messages:
            self.process_message(m)

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
def process_saved_message(message_id):
    transaction.commit_unless_managed()
    message = Message.objects.get(id=message_id)
    mention_finder = MentionFinder()
    mention_finder.process_message(message)