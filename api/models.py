from __future__ import division
from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from datetime import date
from dateutil.rrule import rrule, DAILY
from collections import Counter
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
import re
import calendar
import logging
EMAIL_FREQUENCY_CHOICES = (
    ('N', "Don't receive email."),
    ('D', "Receive a daily digest email."),
    ('A', "Receive emails as notifications happen."),
)

log = logging.getLogger(__name__)
alphanumeric = re.compile(r'[^a-zA-Z0-9]+')


MAX_CHARFIELD_LENGTH = 255
MAX_NAME_LENGTH = 50

class Classgroup(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    owner = models.ForeignKey(User, related_name="created_classgroups", blank=True, null=True, on_delete=models.SET_NULL)
    users = models.ManyToManyField(User, related_name="classgroups", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def link(self):
        return "/classes/" + self.name + "/"

    def api_link(self):
        return "/api/classes/" + self.name + "/"

    def queryset(self, tag=None):
        queryset = self.messages.all()
        if tag is not None and self.tags.filter(id=tag.id) > 0:
            queryset = queryset.filter(tags=tag)
        return queryset

    def message_count(self, tag=None):
        return self.queryset(tag).count()

    def user_count(self):
        return self.users.all().count()

    def user_count_today(self, tag=None):
        return self.queryset(tag).filter(created_at__gt=now() - timedelta(days=1)).values('user').distinct().count()

    def message_count_today(self, tag=None):
        return self.queryset(tag).filter(created_at__gt=now() - timedelta(days=1)).count()

    def message_count_by_day(self, tag=None):
        message_data = list(self.queryset(tag).extra({'created' : "date(created_at)"}).values('created').annotate(created_count=Count('id')))
        day_counts = self.count_by_day(message_data)
        return day_counts

    def first_message_time(self, tag=None):
        first_message = self.queryset(tag).values('created_at').order_by("-created_at")[0]
        return min(self.modified.date(), first_message['created_at'].date()) - timedelta(days=2)

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

    def network_info(self, tag=None):
        users = self.users.all()
        user_relations = {}
        nodes = []
        for u in users:
            nodes.append({'name' : u.username, 'image' : u.profile.image, 'size' : self.queryset(tag).filter(user=u).count()})
        for u in users:
            replied_to_names = [i['reply_to__user__username'] for i in self.queryset(tag).filter(user=u, reply_to__isnull=False).values('reply_to__user__username')]
            user_relations[u.username] = Counter(replied_to_names)
        edges = []
        for u in user_relations:
            for k in user_relations[u]:
                if u!=k:
                    edges.append({'start' : u, 'end' : k, 'strength' : user_relations[u][k]})
        return {'nodes' : nodes, 'edges' : edges}

class Resource(models.Model):
    owner = models.ForeignKey(User, related_name="resources")
    classgroup = models.ForeignKey(Classgroup, related_name="resources")
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    resource_type = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    data = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    text = models.TextField()
    source = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    reply_to = models.ForeignKey('self', related_name="replies", blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, related_name="messages")
    classgroup = models.ForeignKey(Classgroup, related_name="messages")
    approved = models.BooleanField(default=False)
    resources = models.ManyToManyField(Resource, related_name="messages", blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def reply_count(self):
        return self.replies.count()

    def profile_image(self):
        try:
            return self.user.profile.image
        except UserProfile.DoesNotExist:
            return None

    def depth(self):
        depth = 0
        reply_to = self.reply_to
        while depth < 3 and reply_to is not None:
            depth+=1
            reply_to = reply_to.reply_to
        return depth

    def created_timestamp(self):
        return calendar.timegm(self.created.utctimetuple())

class Rating(models.Model):
    rating = models.IntegerField(default=0)
    message = models.ForeignKey(Message, related_name="ratings")
    owner = models.ForeignKey(User, related_name="ratings", blank=True, null=True, on_delete=models.SET_NULL)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

class ClassSettings(models.Model):
    classgroup = models.OneToOneField(Classgroup, related_name="class_settings", blank=True, null=True)
    is_public = models.BooleanField(default=False)
    moderate_posts = models.BooleanField(default=True)
    access_key = models.CharField(max_length=MAX_CHARFIELD_LENGTH, unique=True)
    allow_signups = models.BooleanField(default=True)

    modified = models.DateTimeField(auto_now=True)

class StudentClassSettings(models.Model):
    classgroup = models.ForeignKey(Classgroup, related_name="student_class_settings")
    user = models.ForeignKey(User, related_name="student_class_settings")
    email_frequency = models.CharField(max_length=3, choices=EMAIL_FREQUENCY_CHOICES, default="A")

    class Meta:
        unique_together = (("classgroup", "user"),)

    def email_frequency_choices(self):
        return EMAIL_FREQUENCY_CHOICES

    def link(self):
        return "/classes/" + self.classgroup.name + "/student_settings/"

class Tag(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    messages = models.ManyToManyField(Message, related_name="tags", blank=True, null=True)
    classgroup = models.ForeignKey(Classgroup, related_name="tags")
    description = models.TextField()

    modified = models.DateTimeField(auto_now=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", unique=True, blank=True, null=True)
    image = models.CharField(max_length=MAX_CHARFIELD_LENGTH, blank=True, null=True, unique=True)
    modified = models.DateTimeField(auto_now=True)

class EmailSubscription(models.Model):
    email_address = models.EmailField(max_length=MAX_CHARFIELD_LENGTH, unique=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    cleared = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class MessageNotification(Notification):
    receiving_message = models.ForeignKey(Message, related_name="received_message_notifications")
    receiving_user = models.ForeignKey(User, related_name="message_notifications")
    origin_message = models.ForeignKey(Message)

    class Meta:
        unique_together = (("receiving_message", "origin_message"),)

class RatingNotification(Notification):
    receiving_message = models.ForeignKey(Message, related_name="received_rating_notifications")
    receiving_user = models.ForeignKey(User, related_name="rating_notifications")
    origin_rating = models.ForeignKey(Rating)

    class Meta:
        unique_together = (("receiving_message", "origin_rating"),)


@receiver(post_save, sender=User)
def create_profile(sender, instance, **kwargs):
    try:
        profile = instance.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=instance)
        profile.save()

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, **kwargs):
    if instance.reply_to is not None:
        try:
            MessageNotification.objects.get_or_create(
                receiving_message=instance.reply_to,
                receiving_user=instance.reply_to.user,
                origin_message=instance,
                notification_type="reply_to_discussion",
            )
        except IntegrityError:
            log.warn("MessageNotification already exists with receiver message {0} and origin message {1}".format(instance.reply_to.id, instance.id))
        for m in instance.reply_to.replies.all():
            if m.user != instance.reply_to.user and m.user != instance.user:
                try:
                    MessageNotification.objects.get_or_create(
                        receiving_message=instance.reply_to,
                        receiving_user=m.user,
                        origin_message=instance,
                        notification_type="reply_to_watched_thread",
                        )
                except IntegrityError:
                    log.warn("MessageNotification already exists with receiver message {0} and origin message {1}".format(m.id, instance.id))
    elif instance.reply_to is None and instance.user == instance.classgroup.owner:
        for user in instance.classgroup.users.all():
            if user != instance.classgroup.owner:
                try:
                    MessageNotification.objects.get_or_create(
                        receiving_message=instance,
                        receiving_user=user,
                        origin_message=instance,
                        notification_type="instructor_discussion_started",
                            )
                except IntegrityError:
                    log.warn("MessageNotification already exists for instructor post with receiver message {0} and origin message {1}".format(instance.id, instance.id))

@receiver(post_save, sender=Rating)
def create_rating_notification(sender, instance, **kwargs):
    try:
        RatingNotification.objects.get_or_create(
            receiving_message=instance.message,
            receiving_user=instance.message.user,
            origin_rating=instance,
            notification_type="rating_for_discussion",
        )
    except IntegrityError:
        log.warn("RatingNotification already exists with receiver message {0} and origin rating {1}".format(instance.message.id, instance.id))

User.profile = property(lambda u: u.get_profile())


