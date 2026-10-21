import datetime

import factory

from infrastructure.persistence.accounts.models import UserModel


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
