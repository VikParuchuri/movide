from __future__ import division
from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from datetime import date
from dateutil.rrule import rrule, DAILY
from collections import Counter
from django.core.validators import RegexValidator
from avatar.templatetags.avatar_tags import avatar_url
from django.conf import settings
import re
import calendar
import logging

EMAIL_FREQUENCY_CHOICES = (
    ('N', "Don't receive email."),
    ('D', "Receive a daily digest email."),
    ('A', "Receive emails as notifications happen."),
)

MESSAGE_TYPE_CHOICES = (
    ('D', "Class discussion."),
    ('A', "Course announcement.")
)

TITLE_CHOICES = (
    ("Mr.", "Mr."),
    ("Ms.", "Ms."),
    ("Mrs.", "Mrs.")
)

GRADING_CHOICES = (
    ("COM", "Completion."),
    ("COR", "Correctness.")
)

DEFAULT_WELCOME_MESSAGE = "Welcome to your course.  Check the discussions view to get started!  The instructor can edit this message in the settings view."
DEFAULT_CLASS_DESCRIPTION = "One of the finest courses ever made. (the instructor can change this in the settings view)"

log = logging.getLogger(__name__)
alphanumeric = re.compile(r'[^a-zA-Z0-9]+')


MAX_CHARFIELD_LENGTH = 255
MAX_NAME_LENGTH = 50

class Classgroup(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    owner = models.ForeignKey(User, related_name="created_classgroups", blank=True, null=True, on_delete=models.SET_NULL)
    users = models.ManyToManyField(User, related_name="classgroups", blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_class_settings(self):
        try:
            settings = self.class_settings
        except ClassSettings.DoesNotExist:
            settings = None
        return settings

    def autocomplete_list(self):
        names = self.users.values('username')
        names = ["@" + n['username'] for n in names]
        tags = self.tags.values('name')
        tags = ["#" + t['name'] for t in tags]
        resources = self.resources.values('name', 'resource_type')
        resources = ["*" + r['name'] for r in resources if r['name'] is not None and r['resource_type'] == "vertical"]
        return names + tags + resources

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
        return self.queryset(tag).filter(created__gt=now() - timedelta(days=1)).values('user').distinct().count()

    def message_count_today(self, tag=None):
        return self.queryset(tag).filter(created__gt=now() - timedelta(days=1)).count()

    def message_count_by_day(self, tag=None):
        message_data = list(self.queryset(tag).extra({'created_date': "date(created)"}).values('created_date').annotate(created_count=Count('id')))
        day_counts = self.count_by_day(message_data)
        return day_counts

    def first_message_time(self, tag=None):
        first_message = self.queryset(tag).values('created').order_by("-created")[0]
        return min(self.modified.date(), first_message['created'].date()) - timedelta(days=2)

    def calculate_days(self, data, start, end):
        for dt in rrule(DAILY, dtstart=start, until=end):
            date_found = False
            dt_str = str(dt).split(" ")[0]
            for rec in data:
                if str(rec['created_date']) == dt_str:
                    date_found = True
                    break
            if date_found:
                continue
            data.append({'created_count': 0, 'created_date': dt_str})
        return data

    def count_by_day(self, objects):
        if len(objects) == 0:
            return []
        end = now().date()
        return self.calculate_days(objects, self.first_message_time(), end)

    def network_info(self, tag=None):
        users = self.users.all()
        user_relations = {}
        nodes = []
        for u in users:
            nodes.append({'name': u.username, 'image': u.profile.image, 'size': self.queryset(tag).filter(user=u).count()})
        for u in users:
            replied_to_names = [i['reply_to__user__username'] for i in self.queryset(tag).filter(user=u, reply_to__isnull=False).values('reply_to__user__username')]
            user_relations[u.username] = Counter(replied_to_names)
        edges = []
        for u in user_relations:
            for k in user_relations[u]:
                if u!=k:
                    edges.append({'start': u, 'end': k, 'strength': user_relations[u][k]})
        return {'nodes': nodes, 'edges': edges}

    class Meta:
        permissions = (
            ('view_classgroup', 'View class'),
        )

class Skill(models.Model):
    classgroup = models.ForeignKey(Classgroup, related_name="skills", blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=MAX_NAME_LENGTH, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    grading_policy = models.CharField(max_length=3, choices=GRADING_CHOICES, default="COM")

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("classgroup", "name"),)

class Resource(models.Model):
    user = models.ForeignKey(User, related_name="resources")
    classgroup = models.ForeignKey(Classgroup, related_name="resources")
    name = models.CharField(max_length=MAX_NAME_LENGTH, validators=[RegexValidator(regex=alphanumeric)], blank=True, null=True)
    display_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    resource_type = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    data = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)
    parent = models.ForeignKey('self', related_name="children", blank=True, null=True, on_delete=models.SET_NULL)
    skills = models.ManyToManyField(Skill, related_name="resources", blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def author_view(self):
        from resources import ResourceRenderer
        renderer = ResourceRenderer(self)
        return renderer.author_view()

    def created_timestamp(self):
        return calendar.timegm(self.created.utctimetuple())

    class Meta:
        order_with_respect_to = 'parent'
        permissions = (
            ('view_resource', 'View resource'),
        )

class UserResourceState(models.Model):
    resource = models.ForeignKey(Resource, related_name="user_resource_states")
    user = models.ForeignKey(User, related_name="user_resource_states")
    data = models.TextField()

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("resource", "user"),)

class Message(models.Model):
    text = models.TextField()
    source = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    reply_to = models.ForeignKey('self', related_name="replies", blank=True, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, related_name="messages")
    classgroup = models.ForeignKey(Classgroup, related_name="messages", blank=True, null=True)
    approved = models.BooleanField(default=False)
    resources = models.ManyToManyField(Resource, related_name="messages", blank=True, null=True)
    mentions = models.ManyToManyField(User, related_name="mentioned_in", blank=True, null=True)
    message_type = models.CharField(choices=MESSAGE_TYPE_CHOICES, default="D", max_length=3)
    processed = models.BooleanField(default=False)

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

    def avatar_url(self):
        return avatar_url(self.user)

    def total_rating(self):
        return sum([r['rating'] for r in self.ratings.values('rating')])

class Rating(models.Model):
    rating = models.IntegerField(default=0)
    message = models.ForeignKey(Message, related_name="ratings")
    user = models.ForeignKey(User, related_name="ratings", blank=True, null=True, on_delete=models.SET_NULL)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("message", "user"),)

class ClassSettings(models.Model):
    classgroup = models.OneToOneField(Classgroup, related_name="class_settings", blank=True, null=True)
    is_public = models.BooleanField(default=False)
    moderate_posts = models.BooleanField(default=True)
    access_key = models.CharField(max_length=MAX_CHARFIELD_LENGTH, unique=True)
    allow_signups = models.BooleanField(default=True)
    enable_posting = models.BooleanField(default=True)
    welcome_message = models.TextField(default=DEFAULT_WELCOME_MESSAGE)
    description = models.TextField(default=DEFAULT_CLASS_DESCRIPTION)

    modified = models.DateTimeField(auto_now=True)

    def link(self):
        return "/classes/" + self.classgroup.name + "/class_settings/"

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
    title = models.CharField(choices=TITLE_CHOICES, max_length=3, blank=True, null=True)
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

def make_random_key():
    existing_keys = [t['access_key'] for t in ClassSettings.objects.all().values('access_key')]
    access_key = User.objects.make_random_password(settings.ACCESS_CODE_LENGTH)
    while access_key in existing_keys:
        access_key = User.objects.make_random_password(settings.ACCESS_CODE_LENGTH)
    return access_key

User.profile = property(lambda u: u.get_profile())


