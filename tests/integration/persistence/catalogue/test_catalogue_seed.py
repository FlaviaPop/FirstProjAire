"""The K, P, 1-8 catalogue seeded by migration 0002 (requirements: "Grade and subject catalogue").

pytest-django builds the test DB by running every migration, so these tests see exactly what
`manage.py migrate` produces on an empty database.
"""

import pytest

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel

pytestmark = pytest.mark.django_db

# Independent copy of the story's proposal tables as confirmed by the project owner on
# 2026-10-21 (AC 10): K = Grădiniță with 5 domains, P = Clasa pregătitoare added before grade 1.
EXPECTED_GRADES = [
    ("K", 0, "Grădiniță", "Kindergarten"),
    ("P", 1, "Clasa pregătitoare", "Preparatory grade"),
    ("1", 2, "Clasa I", "Grade 1"),
    ("2", 3, "Clasa a II-a", "Grade 2"),
    ("3", 4, "Clasa a III-a", "Grade 3"),
    ("4", 5, "Clasa a IV-a", "Grade 4"),
    ("5", 6, "Clasa a V-a", "Grade 5"),
    ("6", 7, "Clasa a VI-a", "Grade 6"),
    ("7", 8, "Clasa a VII-a", "Grade 7"),
    ("8", 9, "Clasa a VIII-a", "Grade 8"),
]
KINDERGARTEN_DOMAINS = ["DLC", "DS", "DOS", "DEC", "DPM"]
EARLY_PRIMARY = ["CLR", "MEM", "EN", "DP", "MM", "AVAP", "EF", "REL"]
EXPECTED_SUBJECTS = {
    "K": KINDERGARTEN_DOMAINS,
    "P": EARLY_PRIMARY,
    "1": EARLY_PRIMARY,
    "2": EARLY_PRIMARY,
    "3": ["LLR", "MAT", "SN", "EN", "EC", "MM", "AVAP", "EF", "REL"],
    "4": ["LLR", "MAT", "SN", "EN", "EC", "IST", "GEO", "MM", "AVAP", "EF", "REL"],
    "5": [
        "LLR",
        "MAT",
        "EN",
        "ML2",
        "BIO",
        "IST",
        "GEO",
        "ES",
        "TIC",
        "ET",
        "EP",
        "EM",
        "EF",
        "REL",
    ],
    "6": [
        "LLR",
        "MAT",
        "EN",
        "ML2",
        "BIO",
        "FIZ",
        "IST",
        "GEO",
        "ES",
        "TIC",
        "ET",
        "EP",
        "EM",
        "EF",
        "REL",
    ],
    "7": [
        "LLR",
        "MAT",
        "EN",
        "ML2",
        "BIO",
        "FIZ",
        "CHI",
        "LAT",
        "IST",
        "GEO",
        "ES",
        "TIC",
        "ET",
        "EP",
        "EM",
        "EF",
        "REL",
    ],
    "8": [
        "LLR",
        "MAT",
        "EN",
        "ML2",
        "BIO",
        "FIZ",
        "CHI",
        "IST",
        "GEO",
        "ES",
        "TIC",
        "ET",
        "EP",
        "EM",
        "EF",
        "REL",
    ],
}
EXPECTED_NAMES = {
    "DLC": ("Domeniul Limbă și comunicare", "Language and communication"),
    "DS": ("Domeniul Științe", "Sciences"),
    "DOS": ("Domeniul Om și societate", "People and society"),
    "DEC": ("Domeniul Estetic și creativ", "Aesthetic and creative"),
    "DPM": ("Domeniul Psihomotric", "Psychomotor"),
    "CLR": ("Comunicare în limba română", "Communication in Romanian"),
    "MEM": ("Matematică și explorarea mediului", "Mathematics and Environmental Exploration"),
    "EN": ("Limba engleză", "English"),
    "DP": ("Dezvoltare personală", "Personal Development"),
    "MM": ("Muzică și mișcare", "Music and Movement"),
    "AVAP": ("Arte vizuale și abilități practice", "Visual Arts and Practical Skills"),
    "EF": ("Educație fizică", "Physical Education"),
    "REL": ("Religie", "Religion"),
    "LLR": ("Limba și literatura română", "Romanian Language and Literature"),
    "MAT": ("Matematică", "Mathematics"),
    "SN": ("Științe ale naturii", "Natural Sciences"),
    "EC": ("Educație civică", "Civic Education"),
    "IST": ("Istorie", "History"),
    "GEO": ("Geografie", "Geography"),
    "ML2": ("Limba modernă 2", "Second Modern Language"),
    "BIO": ("Biologie", "Biology"),
    "FIZ": ("Fizică", "Physics"),
    "CHI": ("Chimie", "Chemistry"),
    "LAT": ("Limba latină", "Latin"),
    "ES": ("Educație socială", "Social Education"),
    "TIC": ("Informatică și TIC", "Computer Science and ICT"),
    "ET": (
        "Educație tehnologică și aplicații practice",
        "Technology Education and Practical Applications",
    ),
    "EP": ("Educație plastică", "Art Education"),
    "EM": ("Educație muzicală", "Music Education"),
}


def test_ten_levels_in_display_order():
    codes = list(GradeModel.objects.values_list("code", flat=True))

    assert codes == ["K", "P", "1", "2", "3", "4", "5", "6", "7", "8"]


def test_kindergarten_lists_the_five_experiential_domains_all_inactive():
    domains = SubjectModel.objects.filter(grade__code="K")

    assert list(domains.values_list("code", flat=True)) == KINDERGARTEN_DOMAINS
    assert not domains.filter(is_active=True).exists()
    assert domains.get(code="DLC").name_ro == "Domeniul Limbă și comunicare"


def test_grades_have_proposed_sort_order_and_bilingual_names():
    grades = list(GradeModel.objects.values_list("code", "sort_order", "name_ro", "name_en"))

    assert grades == EXPECTED_GRADES


@pytest.mark.parametrize("grade_code", list(EXPECTED_SUBJECTS))
def test_each_grade_has_its_proposed_subjects_in_display_order(grade_code):
    rows = SubjectModel.objects.filter(grade__code=grade_code).values_list("code", "sort_order")

    expected = [(code, position) for position, code in enumerate(EXPECTED_SUBJECTS[grade_code], 1)]
    assert list(rows) == expected


def test_subject_total_matches_the_proposal():
    expected_total = sum(len(codes) for codes in EXPECTED_SUBJECTS.values())

    assert SubjectModel.objects.count() == expected_total == 111


def test_every_subject_carries_the_proposed_bilingual_names():
    stored = SubjectModel.objects.values_list("code", "name_ro", "name_en")

    mismatches = [row for row in stored if EXPECTED_NAMES[row[0]] != (row[1], row[2])]

    assert mismatches == []


def test_only_grade_two_clr_mem_en_are_active():
    active = set(SubjectModel.objects.filter(is_active=True).values_list("grade__code", "code"))

    assert active == {("2", "CLR"), ("2", "MEM"), ("2", "EN")}


def test_every_name_is_bilingual():
    assert not GradeModel.objects.filter(name_ro="").exists()
    assert not GradeModel.objects.filter(name_en="").exists()
    assert not SubjectModel.objects.filter(name_ro="").exists()
    assert not SubjectModel.objects.filter(name_en="").exists()


def test_grade_two_subjects_display_order():
    codes = list(SubjectModel.objects.filter(grade__code="2").values_list("code", flat=True))

    assert codes[:3] == ["CLR", "MEM", "EN"]


def test_romanian_diacritics_are_stored_intact():
    subject = SubjectModel.objects.get(grade__code="2", code="MEM")

    assert subject.name_ro == "Matematică și explorarea mediului"


def test_default_ordering_follows_grade_then_subject_order():
    first, last = SubjectModel.objects.first(), SubjectModel.objects.last()

    assert (first.grade.code, first.code) == ("K", "DLC")
    assert (last.grade.code, last.code) == ("8", "REL")


def test_grade_exposes_its_subjects_through_related_name():
    grade = GradeModel.objects.get(code="2")

    assert grade.subjects.count() == len(EARLY_PRIMARY)


def test_string_form_identifies_grade_and_subject_by_code():
    subject = SubjectModel.objects.get(grade__code="2", code="EN")

    assert str(subject.grade) == "2"
    assert str(subject) == f"{subject.grade_id}:EN"
