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
from models import Resource, Tag, MessageNotification, Classgroup
from django.db import IntegrityError
from resources import get_vertical_score, get_resource_score
from django.core.cache import cache
from notifications import GradingQueue
from uploads import upload_data_to_s3
import csv
import StringIO

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

@periodic_task(run_every=timedelta(seconds=settings.UPDATE_GRADING_QUEUE_EVERY))
@single_instance_task(settings.CACHE_TIMEOUT)
def update_grading_queues():
    transaction.commit_unless_managed()
    classgroups = Classgroup.objects.all()
    for cl in classgroups:
        update_grading_queue(cl.id)

@task()
def update_grading_queue(cl_id):
    cl = Classgroup.objects.get(id=cl_id)
    grading_queue = GradingQueue(cl, cl.owner)
    grading_queue.update()

@periodic_task(run_every=timedelta(seconds=settings.UPDATE_GRADES_EVERY))
@single_instance_task(settings.CACHE_TIMEOUT)
def update_grades():
    transaction.commit_unless_managed()
    classgroups = Classgroup.objects.all()
    for cl in classgroups:
        student_grade = StudentGrade(cl)

        # Set per-skill grades.
        cache.set(cl.name + "_grades", student_grade.calculate_skill_grades())

        # Set per-resource grades.
        resource_grades = student_grade.calculate_resource_grades()
        cache.set(cl.name + "_resource_grades", resource_grades)

        # Generate a grades table and send it to S3.
        string_write = StringIO.StringIO()
        resource_grades_table = student_grade.parse_resource_grades(resource_grades)
        writer = csv.writer(string_write)
        for i in xrange(len(resource_grades_table)):
            writer.writerow(resource_grades_table[i])
        if len(resource_grades_table) > 1 and len(resource_grades_table[1]) > 1:
            upload_data_to_s3(string_write, "{0}/{1}".format(cl.name, "resource_grades_table.csv"))
        cache.set(cl.name + "_resource_grades_table", resource_grades_table)

class StudentGrade(object):
    def __init__(self, classgroup):
        self.classgroup = classgroup

    def calculate_skill_grade(self, user):
        class_skills = self.classgroup.skills.all()
        skill_grades = {}
        for skill in class_skills:
            resources = skill.resources.all()
            scores = []
            for r in resources:
                if r.resource_type == "vertical":
                    scores += get_vertical_score(r, user, skill.grading_policy)
            scores = [int(s) for s in scores]
            skill_grades[skill.display_name] = scores
        return skill_grades

    def calculate_skill_grades(self):
        """
        Calculate the grades for skills in a course.
        """
        skill_grades = {}
        for user in self.classgroup.users.all():
            skill_grades[user.username] = self.calculate_skill_grade(user)
        return skill_grades

    def calculate_resource_grade(self, user):
        """
        Calculate the score for a resource.
        """
        resources = self.classgroup.resources.all()
        grades = {}
        for r in resources:
            scores = []
            if r.resource_type != "vertical" and r.parent is not None:
                score = get_resource_score(r, user)
                if score is not None:
                    grades[r.id] = score
        return grades

    def calculate_resource_grades(self):
        resource_grades = {}
        for user in self.classgroup.users.all():
            resource_grades[user.username] = self.calculate_resource_grade(user)
        return resource_grades

    def parse_resource_grades(self, grades):
        all_ids = []
        for user in grades:
            all_ids += grades[user].keys()
            all_ids = list(set(all_ids))

        all_resources = []
        for aid in all_ids:
            r = Resource.objects.get(id=aid)
            if r.parent is not None:
                all_resources.append(r)

        all_resources = sorted(all_resources, key=lambda r: r.created)

        mat_view = [[""] + ["{0}: {1}".format(r.parent.name, r.name) for r in all_resources]]
        for user in grades:
            row_view = [user]
            for r in all_resources:
                row_view.append(grades[user].get(r.id, -1))
            mat_view.append(row_view)

        return mat_view




