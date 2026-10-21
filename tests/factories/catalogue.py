import factory

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel


class GradeFactory(factory.django.DjangoModelFactory):
    """Defaults to the seeded grade 2; `get_or_create` on code reuses seeded rows."""

    class Meta:
        model = GradeModel
        django_get_or_create = ("code",)

    code = "2"
    sort_order = 3
    name_ro = "Clasa a II-a"
    name_en = "Grade 2"


class SubjectFactory(factory.django.DjangoModelFactory):
    """Defaults to the seeded, active grade-2 MEM subject."""

    class Meta:
        model = SubjectModel
        django_get_or_create = ("grade", "code")

    grade = factory.SubFactory(GradeFactory)
    code = "MEM"
    sort_order = 2
    name_ro = "Matematică și explorarea mediului"
    name_en = "Mathematics and Environmental Exploration"
    is_active = True
