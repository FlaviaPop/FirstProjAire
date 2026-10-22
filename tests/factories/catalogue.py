import factory

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel


class GradeFactory(factory.django.DjangoModelFactory):
    """Defaults to the seeded grade 2; `get_or_create` on code reuses seeded rows."""

    class Meta:
        model = GradeModel
        django_get_or_create = ("code",)

    code = "2"
    # Used only when creating a new code; seeded grades use 0-9 (review v1 ISS-001).
    sort_order = factory.Sequence(lambda n: 100 + n)
    name_ro = "Clasa a II-a"
    name_en = "Grade 2"


class SubjectFactory(factory.django.DjangoModelFactory):
    """Defaults to the seeded, active grade-2 MEM subject."""

    class Meta:
        model = SubjectModel
        django_get_or_create = ("grade", "code")

    grade = factory.SubFactory(GradeFactory)
    code = "MEM"
    # Used only when creating a new code; seeded subjects use 1-17 per grade (ISS-001).
    sort_order = factory.Sequence(lambda n: 100 + n)
    name_ro = "Matematică și explorarea mediului"
    name_en = "Mathematics and Environmental Exploration"
    # New subjects start inactive like real ones; the seeded MEM row keeps is_active=True.
    is_active = False
