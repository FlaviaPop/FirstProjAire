"""Seed the kindergarten-to-grade-8 catalogue (Story 2.1, patterns §6.4).

The data is inlined on purpose: a migration must keep producing the same rows even if the
application code changes later, so it never imports from `models.py` or any app module and
works only through historical models (`apps.get_model`).

Forward is idempotent in effect (`get_or_create` keyed on codes), so a partially failed run
can be re-applied. Reverse deletes exactly the seeded (grade, subject) pairs, then the seeded
grades. Rows added later by other means are left alone. If such a row still depends on a
seeded row (a later subject in a seeded grade, or CYCLE-2 content pointing at a seeded subject
through a PROTECT foreign key), Django raises ProtectedError and the migration aborts instead
of orphaning data.

Content confirmed by the project owner on 2026-10-21 (story AC 10): 10 levels in display order
K = Grădiniță (the 5 experiential domains), P = Clasa pregătitoare, then grades 1-8 with the
proposed subject lists. Only grade 2 CLR, MEM and EN are active. Changes after merge go in a
follow-up data migration (0003_...), never in this file.
"""

from typing import ClassVar

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

GRADES = [  # (code, sort_order, name_ro, name_en)
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

SUBJECT_NAMES = {  # code: (name_ro, name_en)
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

KINDERGARTEN_DOMAINS = ["DLC", "DS", "DOS", "DEC", "DPM"]
PRIMARY_EARLY = ["CLR", "MEM", "EN", "DP", "MM", "AVAP", "EF", "REL"]
SUBJECTS_BY_GRADE = {  # grade code: subject codes in display order (sort_order = position from 1)
    "K": KINDERGARTEN_DOMAINS,
    "P": PRIMARY_EARLY,
    "1": PRIMARY_EARLY,
    "2": PRIMARY_EARLY,
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

# Requirements ("Grade and subject catalogue"): only these are active in the MVP.
ACTIVE = {("2", "CLR"), ("2", "MEM"), ("2", "EN")}


def seed(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    grade_model = apps.get_model("catalogue", "GradeModel")
    subject_model = apps.get_model("catalogue", "SubjectModel")
    for code, order, name_ro, name_en in GRADES:
        grade, _ = grade_model.objects.get_or_create(
            code=code, defaults={"sort_order": order, "name_ro": name_ro, "name_en": name_en}
        )
        for position, subject_code in enumerate(SUBJECTS_BY_GRADE[code], start=1):
            subject_name_ro, subject_name_en = SUBJECT_NAMES[subject_code]
            subject_model.objects.get_or_create(
                grade=grade,
                code=subject_code,
                defaults={
                    "sort_order": position,
                    "name_ro": subject_name_ro,
                    "name_en": subject_name_en,
                    "is_active": (code, subject_code) in ACTIVE,
                },
            )


def unseed(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    grade_model = apps.get_model("catalogue", "GradeModel")
    subject_model = apps.get_model("catalogue", "SubjectModel")
    for code, *_ in GRADES:
        # PROTECT foreign keys from later content raise ProtectedError here.
        subject_model.objects.filter(grade__code=code, code__in=SUBJECTS_BY_GRADE[code]).delete()
    # A subject added later to a seeded grade still PROTECTs it: fail rather than orphan it.
    grade_model.objects.filter(code__in=[code for code, *_ in GRADES]).delete()


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [("catalogue", "0001_initial")]

    operations: ClassVar[list[migrations.operations.base.Operation]] = [
        migrations.RunPython(seed, unseed)
    ]
