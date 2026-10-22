import datetime

import factory

from infrastructure.persistence.accounts.models import ParentChildLinkModel, UserModel


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserModel
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    full_name = factory.Faker("name")
    date_of_birth = datetime.date(2018, 5, 1)
    role = "STUDENT"
    preferred_language = "ro"
    password = factory.django.Password("pilot-pass-123")


# --- Story 1.2: one factory per role (patterns §12.3) ---
class StudentFactory(UserFactory):
    role = "STUDENT"
    date_of_birth = datetime.date(2018, 5, 1)


class TeacherFactory(UserFactory):
    role = "TEACHER"
    date_of_birth = datetime.date(1985, 9, 15)


class ParentFactory(UserFactory):
    role = "PARENT"
    date_of_birth = datetime.date(1987, 2, 20)


class AdminFactory(UserFactory):
    role = "ADMIN"  # is_staff/is_superuser are derived from the role (Story 1.9)
    date_of_birth = datetime.date(1980, 1, 10)


# --- Story 1.9: parent-child links ---
class ParentChildLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParentChildLinkModel

    parent = factory.SubFactory(ParentFactory)
    student = factory.SubFactory(StudentFactory)
    created_at = datetime.datetime(2026, 10, 20, 8, 0, tzinfo=datetime.UTC)
