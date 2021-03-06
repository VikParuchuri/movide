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

# Used by StudentClassSettings to define email frequency.
EMAIL_FREQUENCY_CHOICES = (
    ('N', "Don't receive email."),
    ('D', "Receive a daily digest email."),
    ('A', "Receive emails as notifications happen."),
)

# Used by Message to define message type choices.
MESSAGE_TYPE_CHOICES = (
    ('D', "Class discussion."),
    ('A', "Course announcement.")
)

# Used by UserProfile.
TITLE_CHOICES = (
    ("Mr.", "Mr."),
    ("Ms.", "Ms."),
    ("Mrs.", "Mrs.")
)

# Used by Skill to define the type of grading.
GRADING_CHOICES = (
    ("COM", "Completion."),
    ("COR", "Correctness.")
)

# Used by ClassSettings as default values.
DEFAULT_WELCOME_MESSAGE = "Welcome to your course.  Check the discussions view to get started!  The instructor can edit this message in the settings view."
DEFAULT_CLASS_DESCRIPTION = "One of the finest courses ever made. (the instructor can change this in the settings view)"

log = logging.getLogger(__name__)
alphanumeric = re.compile(r'[^a-zA-Z0-9]+')

MAX_CHARFIELD_LENGTH = 255
MAX_NAME_LENGTH = 50

class Classgroup(models.Model):
    """
    Classes are the highest model in movide, and encapsulate other resources.
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    owner = models.ForeignKey(User, related_name="created_classgroups", blank=True, null=True, on_delete=models.SET_NULL)
    users = models.ManyToManyField(User, related_name="classgroups", blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_class_settings(self):
        """
        Return a class settings object if one is associated with this classgroup, else None.
        """
        try:
            settings = self.class_settings
        except ClassSettings.DoesNotExist:
            settings = None
        return settings

    def autocomplete_list(self):
        """
        Return a list of usernames, tags, and resources that can be used to generate a list of entities to autocomplete.
        """
        names = self.users.values('username')
        names = ["@" + n['username'] for n in names]
        tags = self.tags.values('name')
        tags = ["#" + t['name'] for t in tags]
        resources = self.resources.values('display_name', 'resource_type')
        resources = ["*" + r['display_name'] for r in resources if r['display_name'] is not None and r['resource_type'] == "vertical"]
        return names + tags + resources

    def link(self):
        """
        Returns the frontend link to this classgroup.
        """
        return "/classes/" + self.name + "/"

    def api_link(self):
        """
        Returns the API link to this classgroup.
        """
        return "/api/classes/" + self.name + "/"

    def queryset(self, tag=None):
        """
        Return a queryset of messages for this classgroup.
        """
        queryset = self.messages.all()
        if tag is not None and self.tags.filter(id=tag.id) > 0:
            queryset = queryset.filter(tags=tag)
        return queryset

    def message_count(self, tag=None):
        """
        Return the number of messages, optionally filtered.
        """
        return self.queryset(tag).count()

    def user_count(self):
        """
        Return the count of users in this classgroup.
        """
        return self.users.all().count()

    def user_count_today(self, tag=None):
        """
        Return the count of users who have been active in the discussions today.
        """
        return self.queryset(tag).filter(created__gt=now() - timedelta(days=1)).values('user').distinct().count()

    def message_count_today(self, tag=None):
        """
        Number of messages sent today.
        """
        return self.queryset(tag).filter(created__gt=now() - timedelta(days=1)).count()

    def message_count_by_day(self, tag=None):
        """
        Message count broken down by day.
        """
        message_data = list(self.queryset(tag).extra({'created_date': "date(created)"}).values('created_date').annotate(created_count=Count('id')))
        day_counts = self.count_by_day(message_data)
        return day_counts

    def first_message_time(self, tag=None):
        """
        The time when the first message in the course was sent.
        """
        first_message = self.queryset(tag).values('created').order_by("-created")[0]
        return min(self.modified.date(), first_message['created'].date()) - timedelta(days=2)

    def calculate_days(self, data, start, end):
        """
        Calculate the number of messages by day.
        """
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
        """
        Count messages sent by day.
        """
        if len(objects) == 0:
            return []
        end = now().date()
        return self.calculate_days(objects, self.first_message_time(), end)

    def network_info(self, tag=None):
        """
        Generate a network graph of students for display.
        """
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
    """
    Skills are used to track student progress.  Resources are associated with skills.
    """
    classgroup = models.ForeignKey(Classgroup, related_name="skills", blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=MAX_NAME_LENGTH, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    grading_policy = models.CharField(max_length=3, choices=GRADING_CHOICES, default="COM")

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def created_timestamp(self):
        return calendar.timegm(self.created.utctimetuple())

    def resource_text(self):
        """
        String of all resources associated with this skill.
        """
        resource_names = SkillResource.objects.filter(skill=self).order_by("priority").values("resource__display_name")
        resource_names = [r['resource__display_name'] for r in resource_names]
        return ",,".join(resource_names)

    def resource_ids(self):
        """
        ids of all resources associated with this skill.
        """
        resource_ids = SkillResource.objects.filter(skill=self).order_by("priority").values("resource__id")
        resource_ids = [str(r['resource__id']) for r in resource_ids]
        return ",,".join(resource_ids)

    class Meta:
        unique_together = (("classgroup", "name"), )

class Section(models.Model):
    """
    A section allows the course to be organized better, by grouping resources.
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH, validators=[RegexValidator(regex=alphanumeric)], blank=True, null=True)
    display_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    classgroup = models.ForeignKey(Classgroup, related_name="sections")

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Override save to ensure that names and classgroups are unique, but make sure that the null case is okay.
        """
        if self.name is not None and self.name != '':
            conflicting_instance = Section.objects.filter(
                name=self.name,
                classgroup=self.classgroup
            )
            if self.id:
                conflicting_instance = conflicting_instance.exclude(pk=self.id)

            if conflicting_instance.exists():
                raise Exception('Section with this name and classgroup already exists.')

        super(Section, self).save(*args, **kwargs)

    class Meta:
        order_with_respect_to = 'classgroup'

class Resource(models.Model):
    """
    Resources are the building blocks for content and problems.  Each resource can contain other resources.
    """
    user = models.ForeignKey(User, related_name="resources")
    classgroup = models.ForeignKey(Classgroup, related_name="resources")
    name = models.CharField(max_length=MAX_NAME_LENGTH, validators=[RegexValidator(regex=alphanumeric)], blank=True, null=True)
    display_name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    resource_type = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    data = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)
    parent = models.ForeignKey('self', related_name="children", blank=True, null=True, on_delete=models.SET_NULL)
    skills = models.ManyToManyField(Skill, blank=True, null=True, through="SkillResource", related_name="resources")
    section = models.ForeignKey(Section, related_name="resources", blank=True, null=True, on_delete=models.SET_NULL)
    priority = models.IntegerField(default=0)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def created_timestamp(self):
        return calendar.timegm(self.created.utctimetuple())

    def save(self, *args, **kwargs):
        """
        Override save to ensure that names and classgroups are unique, but make sure that the null case is okay.
        """
        if self.name is not None and self.name != '' and self.resource_type == "vertical":
            conflicting_instance = Resource.objects.filter(
                name=self.name,
                classgroup=self.classgroup,
                resource_type="vertical"
            )
            if self.id:
                conflicting_instance = conflicting_instance.exclude(pk=self.id)

            if conflicting_instance.exists():
                raise Exception('Resource with this name and classgroup already exists.')

        super(Resource, self).save(*args, **kwargs)

    class Meta:
        order_with_respect_to = 'parent'
        permissions = (
            ('view_resource', 'View resource'),
        )

class SkillResource(models.Model):
    """
    Associate a skill with a resource.  Extra field for ordering.
    """
    skill = models.ForeignKey(Skill)
    resource = models.ForeignKey(Resource)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=0)

    class Meta:
        unique_together = ('skill', 'resource')

class UserResourceState(models.Model):
    """
    Tracks a user's state in a resource (ie, a student response to a question).
    """
    resource = models.ForeignKey(Resource, related_name="user_resource_states")
    user = models.ForeignKey(User, related_name="user_resource_states")
    data = models.TextField()

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("resource", "user"),)

class Message(models.Model):
    """
    Messages are sent by students and teachers.
    """
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
        """
        Number of replies to this message.
        """
        return self.replies.count()

    def profile_image(self):
        """
        The profile image of the user who sent the message.
        """
        try:
            return self.user.profile.image
        except UserProfile.DoesNotExist:
            return None

    def depth(self):
        """
        The depth of the message (a reply to a message has depth 1, a reply to a reply has depth 2)
        """
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
        """
        Total rating of the message.
        """
        return sum([r['rating'] for r in self.ratings.values('rating')])

class Rating(models.Model):
    """
    Users can rate messages.
    """
    rating = models.IntegerField(default=0)
    message = models.ForeignKey(Message, related_name="ratings")
    user = models.ForeignKey(User, related_name="ratings", blank=True, null=True, on_delete=models.SET_NULL)

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("message", "user"),)

class ClassSettings(models.Model):
    """
    Defines the course settings for a classgroup.
    """
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
    """
    Students can also have their own classgroup settings.
    """
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
    """
    Tags can categorize discussions.  Currently not used.
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True, db_index=True, validators=[RegexValidator(regex=alphanumeric)])
    display_name = models.CharField(max_length=MAX_NAME_LENGTH)
    messages = models.ManyToManyField(Message, related_name="tags", blank=True, null=True)
    classgroup = models.ForeignKey(Classgroup, related_name="tags")
    description = models.TextField()

    modified = models.DateTimeField(auto_now=True)

class UserProfile(models.Model):
    """
    Stores some additional user information.
    """
    user = models.OneToOneField(User, related_name="profile", unique=True, blank=True, null=True)
    image = models.CharField(max_length=MAX_CHARFIELD_LENGTH, blank=True, null=True, unique=True)
    title = models.CharField(choices=TITLE_CHOICES, max_length=3, blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

class EmailSubscription(models.Model):
    """
    Allow for email subscriptions to be stored.  Not used currently.
    """
    email_address = models.EmailField(max_length=MAX_CHARFIELD_LENGTH, unique=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    """
    Abstract class to allow for notifications to be stored.
    """
    cleared = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=MAX_CHARFIELD_LENGTH)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class MessageNotification(Notification):
    """
    Notifications for messages are sent when an action a user needs to know about occurs, for example, a message is replied to.
    """
    receiving_message = models.ForeignKey(Message, related_name="received_message_notifications")
    receiving_user = models.ForeignKey(User, related_name="message_notifications")
    origin_message = models.ForeignKey(Message)

    class Meta:
        unique_together = (("receiving_message", "origin_message"),)

class RatingNotification(Notification):
    """
    Rating notifications are sent when a student rates the message of another.
    """
    receiving_message = models.ForeignKey(Message, related_name="received_rating_notifications")
    receiving_user = models.ForeignKey(User, related_name="rating_notifications")
    origin_rating = models.ForeignKey(Rating)

    class Meta:
        unique_together = (("receiving_message", "origin_rating"),)

def make_random_key():
    """
    Make a random access key for a classgroup.
    """
    existing_keys = [t['access_key'] for t in ClassSettings.objects.all().values('access_key')]
    access_key = User.objects.make_random_password(settings.ACCESS_CODE_LENGTH)
    while access_key in existing_keys:
        access_key = User.objects.make_random_password(settings.ACCESS_CODE_LENGTH)
    return access_key

User.profile = property(lambda u: u.get_profile())


