"""Story 2.2 AC 12: RO/EN catalogue entries for every new UI string, and the RO pages use them."""

import re

import pytest
from django.conf import settings

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel

LOCALE = settings.BASE_DIR / "src/infrastructure/i18n/locale"
ROMANIAN = {
    "Catalogue": "Catalog",
    "Pilot": "Pilot",
    "Available to students": "Disponibil pentru elevi",
    "No chapters are published yet.": "Încă nu sunt publicate capitole.",
    "The catalogue is not available yet.": "Catalogul nu este încă disponibil.",
    # Owner wording decision 2026-10-23 (2.2 review v1 ISS-002): "materie" for student/parent UI.
    "Grades and subjects": "Clase și materii",
}


def _catalogue(language: str) -> dict[str, str]:
    text = (LOCALE / language / "LC_MESSAGES/django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, re.M))


def _entry(language: str, msgid: str) -> str:
    text = (LOCALE / language / "LC_MESSAGES/django.po").read_text(encoding="utf-8")
    start = text.rindex("\n\n", 0, text.index(f'\nmsgid "{msgid}"\n'))
    return text[start : text.index("\n\n", start + 2)]


@pytest.mark.parametrize(("msgid", "romanian"), ROMANIAN.items())
def test_romanian_translation_matches_the_story(msgid, romanian):
    assert _catalogue("ro")[msgid] == romanian


@pytest.mark.parametrize("msgid", ROMANIAN)
def test_english_entry_equals_its_msgid(msgid):
    assert _catalogue("en")[msgid] == msgid


@pytest.mark.parametrize("language", ["ro", "en"])
@pytest.mark.parametrize("msgid", ROMANIAN)
def test_entries_are_not_fuzzy_and_reference_the_catalogue_sources(language, msgid):
    entry = _entry(language, msgid)

    assert "fuzzy" not in entry
    assert "src/infrastructure/web/" in entry


@pytest.mark.django_db
def test_romanian_catalogue_page_is_translated(teacher_client, compiled_catalogues):
    html = teacher_client.get("/ro/catalogue/").content.decode()

    assert '<h1 class="page-header__title">Catalog</h1>' in html
    assert '<p class="catalogue__lead">Clase și materii</p>' in html
    assert html.count('<p class="card__meta">Disponibil pentru elevi</p>') == 3
    assert '<span class="catalogue__pilot">Pilot</span>' in html
    assert html.count('<span class="tile__status">Indisponibil</span>') == 108
    assert "Comunicare în limba română" in html
    assert "Limba engleză" in html


@pytest.mark.django_db
def test_romanian_subject_and_empty_pages_are_translated(student_client, compiled_catalogues):
    mem = SubjectModel.objects.get(grade__code="2", code="MEM").pk
    subject_html = student_client.get(f"/ro/subjects/{mem}/").content.decode()
    SubjectModel.objects.all().delete()
    GradeModel.objects.all().delete()

    empty_html = student_client.get("/ro/catalogue/").content.decode()

    assert "Încă nu sunt publicate capitole." in subject_html
    assert "Catalogul nu este încă disponibil." in empty_html
