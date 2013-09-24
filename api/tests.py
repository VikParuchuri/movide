from django.test import TestCase
from django.test import TestCase
from django.test import Client
from factories import UserFactory, ClassGroupFactory
import logging
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import json

log = logging.getLogger(__name__)

class UserLoginTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = UserFactory()
        response = self.c.login(**{'username': self.user.username, 'password': 'password'})

class ClassGroupViewTest(UserLoginTestCase):
    def setUp(self):
        super(ClassGroupViewTest, self).setUp()
        self.cg = ClassGroupFactory(owner=self.user)

    def test_get_classgroup_list(self):
        cg_list_url = reverse('class_list')
        response = self.c.get(cg_list_url)
        courses = json.loads(response.content)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]['pk'], self.cg.id)
