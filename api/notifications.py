from __future__ import unicode_literals
from models import RatingNotification, MessageNotification, Message
from permissions import ClassGroupPermissions, IsNotTeacher
from resources import get_grading_view
from django.core.cache import cache

NOTIFICATION_TYPES = {
    'reply_to_discussion': "{origin_user} replied to your discussion!",
    'reply_to_watched_thread': "{origin_user} replied to a discussion that you are watching.",
    'rating_for_discussion': "{origin_user} liked your discussion.",
    'instructor_discussion_started': "Your course instructor started a new discussion.",
    'instructor_announcement_made': "Your course instructor made a new announcement.",
    'mention_in_message': "{origin_user} mentioned you in their discussion.",
    "mention_in_reply": "{origin_user} mentioned you in their reply to a discussion."
}

def get_to_be_graded_count(user, classgroup):
    """
    Get the length of the grading queue for a given classgroup and user.
    Right now only teachers can grade.
    """
    to_be_graded = 0
    if ClassGroupPermissions.is_teacher(classgroup, user):
        grading_queue = GradingQueue(classgroup, user)
        queue = grading_queue.retrieve()
        if queue is not None:
            to_be_graded = len(queue)
    return to_be_graded

class InvalidNotificationType(Exception):
    pass

class NotificationText(object):
    """
    Generate notification text for a message to a user.
    """
    def __init__(self, notifications):
        self.notifications = notifications

    def generate_text(self):
        self.notification_text = []
        for n in self.notifications:
            if isinstance(n, RatingNotification):
                self.notification_text.append(self.generate_text_rating(n))
            elif isinstance(n, MessageNotification):
                self.notification_text.append(self.generate_text_message(n))
            else:
                error_message = "Invalid notification type passed to NotificationText."
                raise InvalidNotificationType(error_message)

    def generate_text_message(self, notification):
        return NOTIFICATION_TYPES[notification.notification_type].format(origin_user=notification.origin_message.user)

    def generate_text_rating(self, notification):
        return NOTIFICATION_TYPES[notification.notification_type].format(origin_user=notification.origin_rating.user)

    def get_messages(self):
        messages = []
        for i,n in enumerate(self.notifications):
            messages.append({'message' : n.receiving_message, 'notification_text' : self.notification_text[i], 'notification' : n})
        return messages

class GradingQueue(object):
    """
    Generate the grading queue for a classgroup.
    """
    def __init__(self, classgroup, user):
        self.cg = classgroup
        self.user = user
        if not ClassGroupPermissions.is_teacher(self.cg, self.user):
            raise IsNotTeacher("User must be teacher in order to have a queue.")

        self.key_name = self.cg.name + "_grading_queue"

    def get_grading_views(self):
        """
        Crawl through the resources in the class to get the grading views.
        """
        resources = self.cg.resources.all()
        users = self.cg.users.all()
        grading_views = {}
        for r in resources:
            for u in users:
                grading_view = get_grading_view(r, u)
                if grading_view is not None and grading_view['needs_grading']:
                    user = u.username
                    grading_view['user'] = user
                    resource = r.display_name
                    grading_view['resource'] = resource
                    grading_views['{0}_{1}'.format(user, resource)] = grading_view
        return grading_views

    def update(self):
        cache.set(self.key_name, self.get_grading_views())

    def retrieve(self):
        return cache.get(self.key_name)

    def remove(self, user, resource):
        key = "{0}_{1}".format(user.username, resource.display_name)
        views = cache.get(self.key_name)

        views.pop(key, None)
        if len(views) == 0:
            views = None
        cache.set(self.key_name, views)

