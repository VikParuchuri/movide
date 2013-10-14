from __future__ import unicode_literals
from django.forms import widgets
from rest_framework import serializers
from models import (Tag, Message, UserProfile, EmailSubscription, Classgroup,
                    Rating, ClassSettings, Resource, StudentClassSettings,
                    MESSAGE_TYPE_CHOICES, make_random_key, GRADING_CHOICES, Skill, SkillResource,
                    Section)
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging
from django.conf import settings
import re
from rest_framework.pagination import PaginationSerializer
from django.contrib.sites.models import get_current_site
from permissions import ClassGroupPermissions


log = logging.getLogger(__name__)

WELCOME_MESSAGE2_TEMPLATE = """
To get started, you might want to create some resources.  Resources are stacks of content and problems.  Teachers and students can both create resources.  Once you make resources, you can tie them to skills.  Skills are collections of resources that allow self-paced learning and track student progress.  Skills and resources can be discussed using the message function.
"""

WELCOME_MESSAGE_TEMPLATE = """
Welcome to your class {class_name}!  You can remove this announcement by hitting the delete button at the bottom right of this.  To invite your students, simply tell them to visit the url {class_link} and use the access code {access_key}.  You can view these again in the settings view, as well as enable or disable student signup.  If you have any questions, please feel free to email info@movide.com.  Hope you enjoy using Movide!
"""

def alphanumeric_name(string):
    return re.sub(r'\W+', '', string.lower().encode("ascii", "ignore"))

def create_classgroups(classgroups, instance):
    for c in classgroups:
        try:
            cg = Classgroup.objects.get(name=c)
        except Classgroup.DoesNotExist:
            continue
        instance.classgroups.add(cg)
        instance.save()

class EmailSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSubscription
        fields = ("email_address", )

class ClassSettingsField(serializers.SlugRelatedField):
    def from_native(self, data):
        serializer = ClassSettingsSerializer(data=data)
        serializer.save()
        return super(ClassSettingsField, self).from_native(data)

class TagSerializer(serializers.Serializer):
    pk = serializers.Field()
    messages = serializers.SlugRelatedField(many=True, slug_field='text', queryset=Message.objects.all(), required=False)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", required=False, queryset=Classgroup.objects.all())
    description = serializers.CharField()
    name = serializers.CharField()
    modified = serializers.Field()
    display_name = serializers.CharField()

    def restore_object(self, attrs, instance=None):
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')

        attributes = ["description"]

        if instance is None:
            try:
                instance = Tag(name=name)
                instance.save()
            except IntegrityError:
                instance = Tag.objects.get(name=alphanumeric_name(name), display_name=name)

            try:
                instance.classgroup = Classgroup.objects.get(name=classgroup)
            except Classgroup.DoesNotExist:
                raise serializers.ValidationError("Invalid classgroup specified: {0}".format(classgroup))
        else:
            cg = Classgroup.objects.get(name=classgroup)

            if instance.classgroup != cg:
                raise serializers.ValidationError("Classgroup given does not match classgroup on tag: {0}".format(classgroup))
        instance = set_attributes(attributes, attrs, instance)
        return instance

class RatingSerializer(serializers.Serializer):
    message = serializers.PrimaryKeyRelatedField(many=False, queryset=Message.objects.all())
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    rating = serializers.IntegerField()
    modified = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        message = attrs.get('message')

        attributes = ["rating"]

        if message.classgroup not in user.classgroups.all():
            raise serializers.ValidationError("Attempting rate a post that is not in your class.")

        if instance is None:
            instance, created = Rating.objects.get_or_create(user=user, message=message)
        else:
            if instance.user != user:
                raise serializers.ValidationError("Attempting to edit a rating that is not yours.")

        instance = set_attributes(attributes, attrs, instance)
        instance.save()
        return instance

class ClassSettingsSerializer(serializers.ModelSerializer):
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", read_only=True)
    class Meta:
        model = ClassSettings
        fields = ("is_public", "moderate_posts", "classgroup",
                  "modified", "welcome_message", "enable_posting", "description", )

class StudentClassSettingsSerializer(serializers.ModelSerializer):
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", read_only=True)
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    email_frequency_choices = serializers.Field()

    class Meta:
        model = StudentClassSettings
        fields = ("classgroup", "user", "email_frequency", "email_frequency_choices", )

def set_attributes(attributes, values, instance):
    for attrib in attributes:
        val = values.get(attrib)
        if val is not None:
            setattr(instance, attrib, val)
    return instance

class ClassgroupSerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.Field()
    class_settings = serializers.RelatedField(many=False, required=False)
    owner = serializers.SlugRelatedField(many=False, slug_field="username", required=False, queryset=User.objects.all())
    users = serializers.SlugRelatedField(many=True, slug_field="username", required=False, queryset=User.objects.all())
    pk = serializers.Field()
    modified = serializers.Field()
    created = serializers.Field()
    link = serializers.Field(source="link")

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        name = attrs.get('name')
        class_settings_values = attrs.get('class_settings')

        attributes = ["description"]
        settings_attributes = ['moderate_posts', 'is_public', 'allow_signups']

        if instance is None:
            try:
                instance = Classgroup(owner=user, name=alphanumeric_name(name), display_name=name)
                instance.save()
                user.classgroups.add(instance)
                user.save()

                cg_perm = ClassGroupPermissions(instance)
                cg_perm.setup()
                cg_perm.assign_access_level(user, cg_perm.administrator)

                try:
                    class_settings = ClassSettings(classgroup=instance, access_key=make_random_key())
                    class_settings.save()
                except IntegrityError:
                    class_settings = ClassSettings.objects.get(classgroup=instance)

                try:
                    message = Message(
                        user=user,
                        classgroup=instance,
                        source="welcome",
                        text=WELCOME_MESSAGE2_TEMPLATE,
                        message_type="A",
                        )
                    message.save()
                    message = Message(
                        user=user,
                        classgroup=instance,
                        source="welcome",
                        text=WELCOME_MESSAGE_TEMPLATE.format(
                            class_name=instance.display_name,
                            class_link=get_current_site(self.context['request']).domain + instance.link(),
                            access_key=class_settings.access_key
                        ),
                        message_type="A",
                    )
                    message.save()
                except IntegrityError:
                    pass

            except IntegrityError:
                error_msg = "Class name is already taken."
                log.exception(error_msg)
                raise serializers.ValidationError(error_msg)
        else:
            if not ClassGroupPermissions.is_teacher(instance, user):
                raise serializers.ValidationError("Class name is already taken.")
            class_settings = instance.class_settings

        instance = set_attributes(attributes, attrs, instance)
        if class_settings_values is not None:
            class_settings = set_attributes(settings_attributes, class_settings_values, class_settings)
        class_settings.save()
        return instance

class RatingField(serializers.RelatedField):
    def to_native(self, value):
        return {
            'rating': value.rating,
            'user': value.user.username,
        }

class MessageSerializer(serializers.Serializer):
    pk = serializers.Field()
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", required=False, queryset=Tag.objects.all())
    user = serializers.SlugRelatedField(many=False, slug_field="username", required=False, queryset=User.objects.all())
    user_image = serializers.Field(source="profile_image")
    reply_to = serializers.PrimaryKeyRelatedField(required=False, queryset=Message.objects.all())
    ratings = RatingField(many=True, read_only=True, required=False)
    classgroup = serializers.SlugRelatedField(slug_field="name", required=False, queryset=Classgroup.objects.all())
    resources = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Resource.objects.all())
    created_timestamp = serializers.Field(source="created_timestamp")
    text = serializers.CharField()
    source = serializers.CharField()
    created = serializers.Field()
    reply_count = serializers.Field()
    approved = serializers.BooleanField()
    modified = serializers.Field()
    depth = serializers.Field(source="depth")
    avatar_url = serializers.Field(source="avatar_url")
    message_type = serializers.ChoiceField(choices=MESSAGE_TYPE_CHOICES, default="D")
    total_rating = serializers.Field(source="total_rating")

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        classgroup = attrs.get('classgroup')

        attributes = ["text", "source", "reply_to"]

        if (classgroup.class_settings is not None and
            classgroup.class_settings.enable_posting is False and
            not ClassGroupPermissions.is_teacher(classgroup, user)):
            raise serializers.ValidationError("You are not allowed to make a post right now.")


        if instance is None:
            instance = Message(user=user, classgroup=classgroup)
        else:
            if instance.user != user:
                raise serializers.ValidationError("Attempting to edit a message that is not yours.")

        message_type = attrs.get('message_type')
        if message_type == "A" and not ClassGroupPermissions.is_teacher(classgroup, user):
            raise serializers.ValidationError("You cannot make an announcement unless you own a course.")

        instance.message_type = message_type

        instance = set_attributes(attributes, attrs, instance)
        instance.save()
        return instance

class PaginatedMessageSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = MessageSerializer

class NotificationSerializer(MessageSerializer):
    notification_text = serializers.Field()
    notification_created = serializers.Field()
    notification_created_timestamp = serializers.Field()

class PaginatedNotificationSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = NotificationSerializer

class ResourceSerializer(serializers.Serializer):
    pk = serializers.Field()
    user = serializers.SlugRelatedField(many=False, slug_field="username", read_only=True)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", read_only=True)
    approved = serializers.BooleanField()
    name = serializers.CharField()
    display_name = serializers.Field()
    section = serializers.SlugRelatedField(many=False, slug_field="name", required=False, read_only=True)
    created_timestamp = serializers.Field(source="created_timestamp")
    priority = serializers.Field()

    modified = serializers.Field()
    created = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')

        attributes = ['data', 'approved']

        if instance is None:
            instance = Resource(user=user, classgroup=classgroup, name=alphanumeric_name(name), display_name=name)
            instance.save()
        else:
            if instance.user != user:
                raise serializers.ValidationError("Class name is already taken.")

        instance = set_attributes(attributes, attrs, instance)
        return instance

class PaginatedResourceSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = ResourceSerializer

def create_user_profile(user):
    profile = UserProfile(user=user)
    profile.save()

class UserSerializer(serializers.Serializer):
    image = serializers.Field(source="profile.image")
    username = serializers.CharField()
    messages = serializers.SlugRelatedField(many=True, slug_field="text", read_only=True, required=False)
    resources = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True, required=False)
    classgroups = serializers.SlugRelatedField(many=True, slug_field="name", required=False, queryset=Classgroup.objects.all())
    pk = serializers.Field()

    def restore_object(self, attrs, instance=None):
        username = attrs.get('username')
        classgroups = attrs.get('classgroups')

        try:
            instance = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                password = User.objects.make_random_password(10)
                instance = User.objects.create_user(username=username, password=password)
            except IntegrityError:
                instance = User.objects.get(username=username)

            try:
                create_user_profile(instance)
            except Exception:
                error_msg = "Could not create a user profile."
                log.exception(error_msg)
                instance.delete()
                raise serializers.ValidationError(error_msg)

        create_classgroups(classgroups, instance)

        if instance.classgroups.count()==0:
            raise serializers.ValidationError("Invalid classgroups specified: {0}".format(classgroups))

        return instance

class ClassgroupStatsSerializer(serializers.Serializer):
    pk = serializers.Field()
    network_info = serializers.Field(source="network_info")
    message_count_by_day = serializers.Field(source="message_count_by_day")
    message_count_today = serializers.Field(source="message_count_today")
    message_count = serializers.Field(source="message_count")
    user_count = serializers.Field(source="user_count")
    user_count_today = serializers.Field(source="user_count_today")
    display_name = serializers.Field()
    name = serializers.CharField()
    modified = serializers.Field()

class SectionSerializer(serializers.Serializer):
    pk = serializers.Field()
    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", required=False, queryset=Classgroup.objects.all())

    modified = serializers.Field()
    created = serializers.Field()

    def restore_object(self, attrs, instance=None):
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')

        user = self.context['request'].user

        if instance is None:
            instance = Section(classgroup=classgroup, name=alphanumeric_name(name), display_name=name)
            instance.save()
        else:
            if not ClassGroupPermissions.is_teacher(classgroup, user):
                raise serializers.ValidationError("You do not have permission to modify this section.")
            instance.name = alphanumeric_name(name)
            instance.display_name = name
        return instance

class SkillSerializer(serializers.Serializer):
    pk = serializers.Field()
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", required=False, queryset=Classgroup.objects.all())
    resource_text = serializers.Field(source="resource_text")
    resource_ids = serializers.Field(source="resource_ids")
    grading_policy = serializers.ChoiceField(choices=GRADING_CHOICES, default="COM")
    name = serializers.CharField()
    display_name = serializers.Field()
    created_timestamp = serializers.Field(source="created_timestamp")

    modified = serializers.Field()
    created = serializers.Field()

    def restore_object(self, attrs, instance=None):
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')

        attributes = ['grading_policy']
        user = self.context['request'].user

        if instance is None:
            instance = Skill(classgroup=classgroup, name=alphanumeric_name(name), display_name=name)
            instance.save()
        else:
            if not ClassGroupPermissions.is_teacher(classgroup, user):
                raise serializers.ValidationError("You do not have permission to modify this skill.")
            instance.name = alphanumeric_name(name)
            instance.display_name = name

        resources = self.context['request'].DATA.get('resources')
        if isinstance(resources, basestring):
            resources = [resources]
        if resources is not None:
            resources = [str(r).strip() for r in resources]
        else:
            resources = []

        skill_resources = []
        for (i, r) in enumerate(resources):
            if len(r) < 1:
                continue
            resource = Resource.objects.get(display_name=r, classgroup=classgroup)
            skill_resource, created = SkillResource.objects.get_or_create(
                resource=resource,
                skill=instance
            )
            skill_resource.priority = i
            skill_resource.save()
            skill_resources.append(skill_resource)

        for s in SkillResource.objects.filter(skill=instance):
            if s not in skill_resources:
                s.delete()

        instance = set_attributes(attributes, attrs, instance)
        return instance

class PaginatedSkillSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = SkillSerializer


