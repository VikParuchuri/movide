from django.forms import widgets
from rest_framework import serializers
from models import Tag, Message, UserProfile, EmailSubscription, Classgroup, Rating, ClassSettings, Resource
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging
from django.conf import settings
log = logging.getLogger(__name__)

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
        user = self.context['request'].user
        classgroup = attrs.get('classgroup')
        name = attrs.get('name')
        description = attrs.get('description')

        if instance is None:
            try:
                instance = Tag(name=name)
                instance.save()
            except IntegrityError:
                instance = Tag.objects.get(name=name.lower(), display_name=name)

            try:
                instance.classgroup = Classgroup.objects.get(name=classgroup)
            except Classgroup.DoesNotExist:
                raise serializers.ValidationError("Invalid classgroup specified: {0}".format(classgroup))
        else:
            cg = Classgroup.objects.get(name=classgroup)

            if instance.classgroup != cg:
                raise serializers.ValidationError("Classgroup given does not match classgroup on tag: {0}".format(classgroup))
        instance.description = description
        return instance

class RatingSerializer(serializers.ModelSerializer):
    message = serializers.PrimaryKeyRelatedField(many=False)
    owner = serializers.SlugRelatedField(slug_field="username")
    class Meta:
        model = Rating
        fields = ("rating", "message", "owner", "modified", )

class ClassSettingsSerializer(serializers.ModelSerializer):
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name")
    class Meta:
        model = ClassSettings
        fields = ("is_public", "moderate_posts", "classgroup", )

def make_random_key():
    existing_keys = [t['access_key'] for t in ClassSettings.objects.all().values('access_key')]
    access_key = User.objects.make_random_password(6)
    while access_key in existing_keys:
        access_key = User.objects.make_random_password(6)
    return access_key

class ClassgroupSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    class_settings = serializers.RelatedField(many=False, blank=True, null=True)
    owner = serializers.SlugRelatedField(many=False, slug_field="username", blank=True, null=True)
    users = serializers.SlugRelatedField(many=True, slug_field="username", blank=True, null=True, queryset=User.objects.all())
    pk = serializers.Field()

    def restore_object(self, attrs, instance=None):
        user = self.context['request'].user
        name = attrs.get('name')
        description = attrs.get('description')
        class_settings_values = attrs.get('class_settings')

        settings_attributes = ['moderate_posts', 'is_public', 'allow_signups']

        if instance is None:
            try:
                instance = Classgroup(owner=user, name=name.lower(), display_name=name)
                instance.save()
                user.classgroups.add(instance)
                user.save()
                class_settings = ClassSettings(classgroup=instance, access_key=make_random_key())
                class_settings.save()
            except IntegrityError:
                raise serializers.ValidationError("Class name is already taken.")
        else:
            if instance.owner != user:
                raise serializers.ValidationError("Class name is already taken.")
            class_settings = instance.class_settings

        instance.description = description
        for attrib in settings_attributes:
            val = class_settings_values.get(attrib)
            if val is not None:
                setattr(class_settings, attrib, val)
        class_settings.save()
        return instance

class MessageSerializer(serializers.ModelSerializer):
    pk = serializers.Field()
    reply_count = serializers.Field(source="reply_count")
    tags = serializers.SlugRelatedField(many=True, slug_field="name", blank=True, null=True)
    user = serializers.SlugRelatedField(many=True, slug_field="username", blank=True, null=True)
    user_image = serializers.Field(source="profile_image")
    reply_to = serializers.PrimaryKeyRelatedField(read_only=True)
    ratings = serializers.SlugRelatedField(many=True, slug_field="rating", read_only=True, blank=True, null=True, queryset=Rating.objects.all())
    classgroup = serializers.SlugRelatedField(slug_field="name", blank=True, null=True)
    resources = serializers.PrimaryKeyRelatedField(many=True, blank=True, null=True, queryset=Resource.objects.all())

    class Meta:
        model = Message
        fields = (
                'text', 'source', 'created', 'reply_to',
                'tags', 'reply_count', 'resources', 'user_name',
                'user_image', 'pk', 'classgroup', 'ratings', 'approved'
        )

class ResourceSerializer(serializers.Serializer):
    pk = serializers.Field()
    owner = serializers.SlugRelatedField(many=False, slug_field="username", read_only=True)
    classgroup = serializers.SlugRelatedField(many=False, slug_field="name", read_only=True)
    data = serializers.CharField()
    approved = serializers.BooleanField()


class UserSerializer(serializers.Serializer):
    image = serializers.Field(source="profile.image")
    username = serializers.CharField()
    messages = serializers.SlugRelatedField(many=True, slug_field="text", read_only=True, blank=True, null=True)
    resources = serializers.SlugRelatedField(many=True, slug_field="resources", read_only=True, blank=True, null=True)
    classgroups = serializers.SlugRelatedField(many=True, slug_field="name", blank=True, null=True)
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
                user_data.create_profile(instance)
            except Exception:
                error_msg = "Could not create a user profile."
                log.exception(error_msg)
                instance.delete()
                raise serializers.ValidationError(error_msg)

        create_classgroups(classgroups, instance)

        if instance.classgroups.count()==0:
            raise serializers.ValidationError("Invalid classgroups specified: {0}".format(classgroups))

        return instance
