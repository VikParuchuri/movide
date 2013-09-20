from django.forms import widgets
from rest_framework import serializers
from models import Tag, Message, UserProfile, EmailSubscription, Classgroup, Rating, ClassSettings, Resource
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging
from django.conf import settings
import re
from rest_framework.pagination import PaginationSerializer


log = logging.getLogger(__name__)

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
    messages = serializers.SlugRelatedField(many=True, slug_field='text', queryset=Message.objects.all(), blank=True, null=True)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", blank=True, null=True, queryset=Classgroup.objects.all())
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

class RatingSerializer(serializers.ModelSerializer):
    message = serializers.PrimaryKeyRelatedField(many=False)
    owner = serializers.SlugRelatedField(slug_field="username")
    class Meta:
        model = Rating
        fields = ("rating", "message", "owner", "modified", "created", )

class ClassSettingsSerializer(serializers.ModelSerializer):
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name")
    class Meta:
        model = ClassSettings
        fields = ("is_public", "moderate_posts", "classgroup", "modified", )

def make_random_key():
    existing_keys = [t['access_key'] for t in ClassSettings.objects.all().values('access_key')]
    access_key = User.objects.make_random_password(6)
    while access_key in existing_keys:
        access_key = User.objects.make_random_password(6)
    return access_key

def set_attributes(attributes, values, instance):
    for attrib in attributes:
        val = values.get(attrib)
        if val is not None:
            setattr(instance, attrib, val)
    return instance

class ClassgroupSerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.Field()
    description = serializers.CharField(required=False)
    class_settings = serializers.RelatedField(many=False, blank=True, null=True)
    owner = serializers.SlugRelatedField(many=False, slug_field="username", blank=True, null=True, queryset=User.objects.all())
    users = serializers.SlugRelatedField(many=True, slug_field="username", blank=True, null=True, queryset=User.objects.all())
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
                class_settings = ClassSettings(classgroup=instance, access_key=make_random_key())
                class_settings.save()
            except IntegrityError:
                error_msg = "Class name is already taken."
                log.exception(error_msg)
                raise serializers.ValidationError(error_msg)
        else:
            if instance.owner != user:
                raise serializers.ValidationError("Class name is already taken.")
            class_settings = instance.class_settings

        instance = set_attributes(attributes, attrs, instance)
        if class_settings_values is not None:
            class_settings = set_attributes(settings_attributes, class_settings_values, class_settings)
        class_settings.save()
        return instance

class MessageSerializer(serializers.Serializer):
    pk = serializers.Field()
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", blank=True, null=True, queryset=Tag.objects.all())
    user = serializers.SlugRelatedField(many=False, slug_field="username", blank=True, null=True, queryset=User.objects.all())
    user_image = serializers.Field(source="profile_image")
    reply_to = serializers.PrimaryKeyRelatedField(required=False, blank=True, null=True, queryset=Message.objects.all())
    ratings = serializers.SlugRelatedField(many=True, slug_field="rating", read_only=True, blank=True, null=True, queryset=Rating.objects.all())
    classgroup = serializers.SlugRelatedField(slug_field="name", blank=True, null=True, queryset=Classgroup.objects.all())
    resources = serializers.PrimaryKeyRelatedField(many=True, blank=True, null=True, queryset=Resource.objects.all())
    created_timestamp = serializers.Field(source="created_timestamp")
    text = serializers.CharField()
    source = serializers.CharField()
    created = serializers.Field()
    reply_count = serializers.Field()
    approved = serializers.BooleanField()
    modified = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        classgroup = attrs.get('classgroup')

        attributes = ["text", "source", "reply_to"]

        if instance is None:
            instance = Message(user=user, classgroup=classgroup)
        else:
            if instance.user != user:
                raise serializers.ValidationError("Attempting to edit a message that is not yours.")

        instance = set_attributes(attributes, attrs, instance)
        instance.save()
        return instance

class PaginatedMessageSerializer(PaginationSerializer):
    class Meta:
        object_serializer_class = MessageSerializer

class ResourceSerializer(serializers.Serializer):
    pk = serializers.Field()
    owner = serializers.SlugRelatedField(many=False, slug_field="username", read_only=True)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", read_only=True)
    data = serializers.CharField()
    approved = serializers.BooleanField()
    name = serializers.CharField()
    display_name = serializers.CharField()

    modified = serializers.Field()
    created = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')

        attributes = ['data', 'approved']

        if instance is None:
            instance = Resource(owner=user, classgroup=classgroup, name=alphanumeric_name(name), display_name=name)
            instance.save()
        else:
            if instance.owner != user:
                raise serializers.ValidationError("Class name is already taken.")

        instance = set_attributes(attributes, attrs, instance)
        return instance

def create_user_profile(user):
    profile = UserProfile(user=user)
    profile.save()

class UserSerializer(serializers.Serializer):
    image = serializers.Field(source="profile.image")
    username = serializers.CharField()
    messages = serializers.SlugRelatedField(many=True, slug_field="text", read_only=True, blank=True, null=True)
    resources = serializers.SlugRelatedField(many=True, slug_field="resources", read_only=True, blank=True, null=True)
    classgroups = serializers.SlugRelatedField(many=True, slug_field="name", blank=True, null=True, queryset=Classgroup.objects.all())
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
