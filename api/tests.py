from rest_framework.test import APITestCase, APIClient
from factories import UserFactory, ClassGroupFactory, ResourceFactory
import logging
from django.core.urlresolvers import reverse
from rest_framework.serializers import ValidationError
import json
from permissions import ClassGroupPermissions
from tasks import process_saved_message
from frontend.views import uncleared_notification_count
from models import Resource
import calendar

log = logging.getLogger(__name__)

class UserLoginTestCase(APITestCase):
    """
    A test case that automatically creates users up to user_count.
    """
    user_count = 1
    post_class_name = "Test"
    class_name = post_class_name.lower()

    def setUp(self):
        # Create as many users as user_count.
        for i in xrange(self.user_count):
            client = APIClient()
            user = UserFactory()
            client.login(**{'username': user.username, 'password': 'password'})

            # Each user is at self.userN and client at self.cN.
            setattr(self, "c{0}".format(i), client)
            setattr(self, "user{0}".format(i), user)

        # Setup some common urls.
        self.resource_url = reverse('resources')
        self.resource_author_url = reverse('resource_author')

    def create_course(self):
        """
        Shortcut function to create a course.
        """
        self.c0.post(reverse('class_list'), {'name': self.post_class_name}, format='json')

    def get_class_detail(self, class_name):
        """
        Shortcut function to get class detail.
        """
        detail_url = reverse('class_detail', kwargs={
            'classgroup': class_name
        })

        return self.c0.get(detail_url).data

    def create_vertical(self):
        """
        Shortcut to create a vertical resource.
        """
        self.c0.post(self.resource_url, {'resource_type': 'vertical', 'classgroup': self.cg.name})
        resource_id = Resource.objects.all()[0].id
        self.c0.post(self.resource_author_url,
                     {
                         'resource_id': resource_id,
                         'classgroup': self.cg.name,
                         'resource_type': 'vertical',
                         'name': self.name
                     }
        )
        return resource_id

class ClassGroupViewTest(UserLoginTestCase):
    """
    Test creating, viewing, and modifying a classgroup.
    """
    user_count = 2

    def setUp(self):
        super(ClassGroupViewTest, self).setUp()
        self.cg = ClassGroupFactory(owner=self.user0)

    def test_get_classgroup_list(self):
        """
        See if we can get the list of classgroups.
        """
        cg_list_url = reverse('class_list')
        response = self.c0.get(cg_list_url)
        courses = response.data
        # We should have the one class we made in setup.
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]['pk'], self.cg.id)

        # The user should have all permissions in the course, as they are the course owner.
        self.assertTrue(ClassGroupPermissions.is_teacher(self.cg, self.user0))
        self.assertTrue(ClassGroupPermissions.is_administrator(self.cg, self.user0))
        self.assertEqual(ClassGroupPermissions.access_level(self.cg, self.user0), ClassGroupPermissions.administrator)

    def test_get_classgroup_list_fail(self):
        """
        Test to see if an empty class list is shown to someone with no permissions.
        """
        cg_list_url = reverse('class_list')
        response = self.c1.get(cg_list_url)
        courses = json.loads(response.content)
        self.assertEqual(len(courses), 0)

        # User 1 should not be able to access the course.
        self.assertEqual(ClassGroupPermissions.access_level(self.cg, self.user1), ClassGroupPermissions.none)

    def test_get_enrollment_page(self):
        """
        See if the access code link is properly shown.
        """
        response = self.c1.get(self.cg.link())
        self.assertIn('Enter access code', response.content)

    def test_enroll_in_course(self):
        """
        Try enrolling in a course with an access code.
        """
        access_key = self.cg.class_settings.access_key
        self.c1.post(reverse('verify_code'), {'class_name': self.cg.name, 'code': access_key})

        # Check that the user has the right permissions.
        self.assertIn(self.user1, self.cg.users.all())
        self.assertTrue(ClassGroupPermissions.is_student(self.cg, self.user1))
        self.assertEqual(ClassGroupPermissions.access_level(self.cg, self.user1), ClassGroupPermissions.student)

class ClassGroupAPITest(UserLoginTestCase):
    """
    Test working with the classgroup API.
    """
    user_count = 2
    class_description = "Test description."
    welcome_message = "Test welcome."

    def setUp(self):
        super(ClassGroupAPITest, self).setUp()

    def test_create(self):
        """
        Create a course.
        """
        self.create_course()
        # We should have a course in our list after making one.
        class_list = self.c0.get(reverse('class_list')).data
        self.assertEqual(len(class_list), 1)
        cg = class_list[0]
        self.assertEqual(cg['name'], self.class_name)

        # Check that there is a class settings model is automatically created.
        detail = self.get_class_detail(cg['name'])
        self.assertEqual(detail['class_settings']['classgroup'], self.class_name)

    def test_change_course_settings(self):
        """
        Try changing the course settings.
        """
        self.create_course()

        settings_post_url = reverse('class_settings_post', kwargs={
            'classgroup': self.class_name
        })

        # Should be successful.  Our user 0 is the owner of the course.
        response = self.c0.post(settings_post_url, {'description': self.class_description, 'welcome_message': self.welcome_message})

        # Should fail, as user 1 is not a teacher in the course.
        denied_response = self.c1.post(settings_post_url, {'description': self.class_description, 'welcome_message': self.welcome_message})
        self.assertEqual(denied_response.status_code, 404)

        # Ensure that the settings were changed properly.
        detail = self.get_class_detail(self.class_name)
        self.assertEqual(detail['class_settings']['description'], self.class_description)
        self.assertEqual(detail['class_settings']['welcome_message'], self.welcome_message)

        # Try the class settings API endpoint and make sure it the values are set there.
        settings_url = reverse('class_settings', kwargs={
            'classgroup': self.class_name
        })
        setting = self.c0.get(settings_url).data
        self.assertEqual(setting['description'], self.class_description)

    def test_change_student_settings(self):
        """
        Try changing course settings for the student.
        """
        self.create_course()

        # Settings are posted to one URL, but are retrieved through the API for now.
        settings_post_url = reverse('student_class_settings_post', kwargs={
            'classgroup': self.class_name
        })
        settings_url = reverse('student_class_settings', kwargs={
            'classgroup': self.class_name
        })

        # Try changing a setting and ensure that it saves properly.
        student_settings = self.c0.get(settings_url).data
        self.assertEqual(student_settings['email_frequency'], "A")
        self.c0.post(settings_post_url, {'email_frequency': 'N'})
        student_settings = self.c0.get(settings_url).data
        self.assertEqual(student_settings['email_frequency'], "N")

    def test_get_stats(self):
        """
        Try to get course statistics.
        """
        self.create_course()

        stats_url = reverse('class_stats', kwargs={
            'classgroup': self.class_name
        })
        stats = self.c0.get(stats_url).data

        # Two welcome messages are created when a course is made.
        self.assertEqual(stats['message_count_today'], 2)
        # User 0 is registered in the course.
        self.assertEqual(stats['user_count'], 1)
        self.assertEqual(stats['name'], self.class_name)

class MessagesAPITest(UserLoginTestCase):
    """
    Test the API endpoint for messages.
    """
    user_count = 2
    text = "Test text."
    source = "Web."

    def setUp(self):
        super(MessagesAPITest, self).setUp()
        self.cg = ClassGroupFactory()
        self.cg.users.add(self.user0)
        self.message_url = reverse('messages')

    def get_messages(self):
        """
        Shortcut to get messages.
        """
        messages = self.c0.get(self.message_url, {'user': self.user0.username, 'classgroup': self.cg.name}).data
        return messages

    def get_message_detail_url(self, pk):
        """
        Shortcut to get the url for message detail.
        """
        return reverse('message_detail', kwargs={'pk': pk})

    def create_message(self):
        """
        Shortcut to create a message.
        """
        response = self.c0.post(self.message_url, {
            'classgroup': self.cg.name,
            'text': self.text,
            'source': self.source,
            })
        return response

    def test_create_and_delete_message(self):
        """
        Try to create and delete a message.
        """
        # We created our course directly through a factory, so no initial messages.
        messages = self.get_messages()
        self.assertEqual(len(messages), 0)

        # Create a message and ensure that it is saved properly.
        response = self.create_message()
        self.assertEqual(response.status_code, 201)
        messages = self.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['text'], self.text)

        # Make sure the detail view works.
        message_detail_url = self.get_message_detail_url(messages[0]['pk'])
        message_detail = self.c0.get(message_detail_url)
        self.assertEqual(message_detail.status_code, 200)
        self.assertEqual(message_detail.data['text'], self.text)

        # Ensure that a user not in the course cannot see the message.
        message_detail = self.c1.get(message_detail_url)
        self.assertEqual(message_detail.status_code, 400)

        # Try to delete the message, but can't unless you are a teacher.
        self.c0.delete(message_detail_url)
        self.assertEqual(message_detail.status_code, 400)
        self.cg.owner = self.user0
        self.cg.save()

        # Succeed in deleting the message.
        self.c0.delete(message_detail_url)
        messages = self.get_messages()
        self.assertEqual(len(messages), 0)

    def test_create_message_rating(self):
        """
        Try to rate a message.
        """
        # Ensure that the message is created and has no rating.
        self.create_message()
        messages = self.get_messages()
        message = messages[0]
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(message['ratings']), 0)
        self.assertEqual(message['total_rating'], 0)

        # Ensure that we properly create a rating.
        rating_url = reverse('ratings')
        self.c0.post(rating_url, {'message': message['pk'], 'rating': 1})
        messages = self.get_messages()
        message = messages[0]
        self.assertEqual(len(message['ratings']), 1)
        self.assertEqual(message['total_rating'], 1)

        # We cannot rate a message if we are not in the course.
        with self.assertRaises(ValidationError):
            self.c1.post(rating_url, {'message': message['pk'], 'rating': 1})

    def test_message_notification(self):
        """
        Ensure that message notifications work properly.
        """
        self.create_message()
        self.create_message()

        # Get message notifications and check the count.  The count (1) is one less than the true count (2) in order
        # to prevent unnecessary notifications.
        message_notification_url = reverse('message_notifications')
        notifications = self.c0.get(
            message_notification_url,
            {
                'classgroup': self.cg.name,
                'start_time': calendar.timegm(self.cg.created.utctimetuple())
            }
        ).data
        self.assertEqual(notifications['message_count'], 1)

    def test_notification(self):
        """
        Test the notifications view when we mention someone in a message.
        """
        # Add user 1 to the classgroup.
        self.cg.users.add(self.user1)
        # Create a message from user0 that mentions user1.
        response = self.c0.post(self.message_url, {
            'classgroup': self.cg.name,
            'text': "@{0} mention test.".format(self.user1.username),
            'source': self.source,
            })
        messages = self.get_messages()
        # Run the task to process mentions.
        process_saved_message(messages[0]['pk'])
        # Check that user 1 has new notifications.
        self.assertEqual(uncleared_notification_count(self.user1, self.cg), 1)

        # Get all the notifications from the API.  Ensure that this resets the notification counter.
        notification_url = reverse('notifications')
        notifications = self.c1.get(notification_url, {'user': self.user1.username, 'classgroup': self.cg.name}).data
        self.assertEqual(uncleared_notification_count(self.user1, self.cg), 0)
        self.assertEqual(len(notifications['results']), 1)
        notification_text = notifications['results'][0]['notification_text']
        self.assertIn('mention', notification_text)

        self.cg.users.remove(self.user1)

class ResourceAPITest(UserLoginTestCase):
    """
    Test the Resource api endpoints.
    """
    user_count = 2
    name = "test4334"
    html = "HTML"

    def setUp(self):
        super(ResourceAPITest, self).setUp()
        self.cg = ClassGroupFactory()
        self.cg.users.add(self.user0)

    def get_resources(self):
        """
        Shortcut to get the resources.
        """
        resources = self.c0.get(self.resource_url, {'classgroup': self.cg.name}).data
        return resources

    def get_resource_detail(self, pk, view_type="user"):
        """
        Shortcut to get detail for a given resource.
        """
        resource_detail = reverse('resource_detail', kwargs={
            'pk': pk,
        })

        return self.c0.get(resource_detail, {'view_type': view_type}).data

    def test_create_resource(self):
        """
        Try to create a resource.
        """
        # We shouldn't have any resources to start with.
        resources = self.get_resources()
        self.assertEqual(len(resources), 0)

        # User 0 is in the course, and can create a resource.
        response = self.c0.post(self.resource_url, {'resource_type': 'vertical', 'classgroup': self.cg.name})
        self.assertEqual(response.status_code, 200)

        # User 1 is not in the course, and cannot make a resource.
        response = self.c1.post(self.resource_url, {'resource_type': 'vertical', 'classgroup': self.cg.name})
        self.assertEqual(response.status_code, 403)

        # Only vertical modules with names show up in the resource list.  We should have 0 resources.
        resources = self.get_resources()
        self.assertEqual(len(resources), 0)

        # Create a resource properly, with a valid name.
        response = self.c0.post(self.resource_author_url,
            {
                'resource_id': Resource.objects.all()[0].id,
                'classgroup': self.cg.name,
                'resource_type': 'vertical',
                'name': self.name
            }
        )
        self.assertEqual(response.status_code, 201)

        # Ensure that the resource is saved properly.
        resources = self.get_resources()
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource['name'], self.name)

    def test_create_component(self):
        """
        Try creating a component in a vertical.
        """
        resource_id = self.create_vertical()

        # Create an HTML module and make sure it was created properly.
        component_html = self.c0.get(self.resource_author_url, {
            'vertical_id': resource_id,
            'classgroup': self.cg.name,
            'resource_type': 'html'
        }).content
        self.assertIn('redactor', component_html)
        vertical = Resource.objects.get(id=resource_id)
        self.assertEqual(len(vertical.children.all()), 1)

        # Get the author HTML for the component we created.
        component_id = Resource.objects.all()[1].id
        response = self.c0.post(self.resource_author_url,
            {
                'resource_id': component_id,
                'classgroup': self.cg.name,
                'name': self.name,
                'html': self.html,
                'resource_type': 'html',
            }
        )
        self.assertEqual(response.status_code, 201)

        # Ensure that the component saved properly.
        resource_detail = self.get_resource_detail(component_id)
        self.assertIn(self.html, resource_detail['html'])

        # Ensure that the author view shows all the values.
        resource_author_detail = self.get_resource_detail(resource_id, view_type="author")
        self.assertIn(self.html, resource_author_detail['html'])
        self.assertIn(self.name, resource_author_detail['html'])

        # Try to update the name of the component.
        component_detail = reverse('resource_detail', kwargs={
            'pk': component_id,
            })
        new_name = "newname2332"
        response = self.c0.post(component_detail, {
            'action': 'save_form_values',
            'name': new_name,
        })
        self.assertEqual(response.status_code, 200)

        # User 1 should not have permission to update the component.
        self.cg.users.add(self.user1)
        response = self.c1.post(component_detail, {
            'action': 'save_form_values',
            'name': new_name,
            })
        self.assertEqual(response.status_code, 403)
        self.cg.users.remove(self.user1)

        # The resource HTML should have the new values we saved.
        resource_detail = self.get_resource_detail(component_id)
        self.assertIn(new_name, resource_detail['html'])
        self.assertNotIn(self.name, resource_detail['html'])

        # User 1 cannot delete the component, as they do not have permission.
        response = self.c1.delete(component_detail)
        self.assertEqual(response.status_code, 403)

        # User 0 can delete it.
        response = self.c0.delete(component_detail)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(vertical.children.all()), 0)

class SkillAPITest(UserLoginTestCase):
    """
    Test the skill api endpoints.
    """
    user_count = 2
    name = "test4545"

    def setUp(self):
        super(SkillAPITest, self).setUp()
        self.cg = ClassGroupFactory()
        self.cg.users.add(self.user0)
        self.skill_url = reverse("skills")

    def get_skills(self):
        """
        Shortcut to get list of skills.
        """
        return self.c0.get(self.skill_url, {'classgroup': self.cg.name}).data

    def get_skill_detail_url(self, pk):
        return reverse('skill_detail', kwargs={
            'pk': pk
        })

    def test_skill_creation(self):
        """
        Try to create and edit a skill.
        """
        skills = self.get_skills()
        self.assertEqual(len(skills), 0)

        # This should fail, as the user does not have the right permissions.
        response = self.c0.post(self.skill_url, {
            'grading_policy': "COR",
            'name': self.name,
            'classgroup': self.cg.name,

        })
        self.assertEqual(response.status_code, 403)
        self.cg.owner = self.user0
        self.cg.save()

        # After making our user the course owner, this should work.
        response = self.c0.post(self.skill_url, {
            'grading_policy': "COR",
            'name': self.name,
            'classgroup': self.cg.name,

            })
        self.assertEqual(response.status_code, 201)
        skills = self.get_skills()
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]['name'], self.name)

        skill_detail_url = self.get_skill_detail_url(skills[0]['pk'])

        # Create a resource that we can associate the skill with.
        resource = ResourceFactory()
        resource.classgroup = self.cg
        resource.save()

        # Try to update the skill with new information.
        newname = "newname24"
        response = self.c0.put(skill_detail_url, {
            'grading_policy': "COR",
            'name': newname,
            'classgroup': self.cg.name,
            'resources': [resource.display_name,]
            })
        self.assertEqual(response.status_code, 201)
        skills = self.get_skills()
        self.assertEqual(skills[0]['name'], newname)

        # User 1 cannot delete the skill.
        response = self.c1.delete(skill_detail_url)
        self.assertEqual(response.status_code, 403)

        # User 0 can delete the skill.
        response = self.c0.delete(skill_detail_url)
        self.assertEqual(response.status_code, 204)
        skills = self.get_skills()
        self.assertEqual(len(skills), 0)

class SectionAPITest(UserLoginTestCase):
    """
    Test the section api endpoints.
    """
    user_count = 2
    name = "test4545"

    def setUp(self):
        super(SectionAPITest, self).setUp()
        self.cg = ClassGroupFactory()
        self.cg.users.add(self.user0)
        self.section_url = reverse("sections")

    def get_sections(self):
        """
        Shortcut to get list of sections.
        """
        return self.c0.get(self.section_url, {'classgroup': self.cg.name}).data

    def get_section_detail_url(self, pk):
        """
        Shortcut to get the url for section detail.
        """
        return reverse('section_detail', kwargs={
            'pk': pk
        })






