import factory
from models import Classgroup, Message, Resource
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user{0}'.format(n))
    email = factory.Sequence(lambda n: 'person{0}@test.com'.format(n))
    is_active = True
    is_staff = True
    password = make_password('password')

class ClassGroupFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Classgroup
    owner = factory.SubFactory(UserFactory)

    name = factory.Sequence(lambda n: 'course{0}'.format(n))
    display_name = "Test Course"

class MessageFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Message
    classgroup = factory.SubFactory(ClassGroupFactory)
    user = factory.SubFactory(UserFactory)

    text = "Test text."
    source = "Test"

class ResourceFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Resource
    user = factory.SubFactory(UserFactory)
    classgroup = factory.SubFactory(ClassGroupFactory)

    name = factory.Sequence(lambda n: 'name{0}'.format(n))
    display_name = "Name"
    resource_type = "vertical"
