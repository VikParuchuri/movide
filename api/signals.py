from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth.models import User
from models import UserProfile, MessageNotification, Message, RatingNotification, Rating, Classgroup, make_random_key, ClassSettings, Resource
from tasks import process_saved_message
import logging
from django.db import IntegrityError
from permissions import ClassGroupPermissions
from south.signals import post_migrate

log = logging.getLogger(__name__)

def update_permissions_after_migration(app, **kwargs):
    """
    Update app permission just after every migration.
    """
    from django.conf import settings
    from django.db.models import get_app, get_models
    from django.contrib.auth.management import create_permissions

    create_permissions(get_app(app), get_models(), 2 if settings.DEBUG else 0)

post_migrate.connect(update_permissions_after_migration)

@receiver(post_save, sender=User, dispatch_uid="create_profile")
def create_profile(sender, instance, **kwargs):
    try:
        profile = instance.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=instance)
        profile.save()

@receiver(post_save, sender=Classgroup, dispatch_uid="create_class_settings")
def create_class_settings(sender, instance, **kwargs):
    try:
        class_settings = instance.class_settings
    except ClassSettings.DoesNotExist:
        settings = ClassSettings(classgroup=instance, access_key=make_random_key())
        settings.save()

@receiver(post_save, sender=Message, dispatch_uid="create_message_notification")
def create_message_notification(sender, instance, **kwargs):
    if instance.reply_to is not None:
        if instance.user != instance.reply_to.user:
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
    elif instance.reply_to is None and instance.classgroup is not None and ClassGroupPermissions.is_teacher(instance.classgroup, instance.user) and instance.message_type == "A":
        for user in instance.classgroup.users.all():
            if user != instance.user:
                try:
                    MessageNotification.objects.get_or_create(
                        receiving_message=instance,
                        receiving_user=user,
                        origin_message=instance,
                        notification_type="instructor_announcement_made",
                        )
                except IntegrityError:
                    log.warn("MessageNotification already exists for instructor post with receiver message {0} and origin message {1}".format(instance.id, instance.id))

    process_saved_message.delay(instance.id)

@receiver(post_save, sender=Rating, dispatch_uid="create_rating_notification")
def create_rating_notification(sender, instance, **kwargs):
    if instance.message.user != instance.user:
        try:
            RatingNotification.objects.get_or_create(
                receiving_message=instance.message,
                receiving_user=instance.message.user,
                origin_rating=instance,
                notification_type="rating_for_discussion",
                )
        except IntegrityError:
            log.warn("RatingNotification already exists with receiver message {0} and origin rating {1}".format(instance.message.id, instance.id))