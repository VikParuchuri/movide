import factory
from models import Classgroup
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

    name = "testcourse"
    display_name = "Test Course"
