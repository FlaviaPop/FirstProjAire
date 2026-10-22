"""Story 1.9 AC 15: every new admin string exists in RO and EN (catalogues read as text)."""

import re
from pathlib import Path

import pytest
from django.conf import settings

from tests.factories.accounts import ParentChildLinkFactory, ParentFactory, StudentFactory
from tests.integration.web.admin.admin_helpers import change_data

pytestmark = pytest.mark.django_db
LOCALE = Path(settings.BASE_DIR) / "src/infrastructure/i18n/locale"

# Owner decision 2026-10-22: 7 messages (AC 15 said 6) - the Parent guard has its own text.
MESSAGES = {
    "There must be at least one active administrator.": (
        "Trebuie să existe cel puțin un administrator activ."
    ),
    "Remove this student's parent links before changing the role.": (
        "Eliminați legăturile elevului cu părinții înainte de a schimba rolul."
    ),
    "Remove this parent's child links before changing the role.": (
        "Eliminați legăturile părintelui cu copiii înainte de a schimba rolul."
    ),
    "This parent is already linked to this student.": (
        "Acest părinte este deja legat de acest elev."
    ),
    "The selected parent account isn't a Parent/Guardian.": (
        "Contul de părinte selectat nu este de tip Părinte/Tutore."
    ),
    "The selected child account isn't a Student.": "Contul de copil selectat nu este de tip Elev.",
    "A person can't be linked to themselves.": "O persoană nu poate fi legată de ea însăși.",
}
TITLES_AND_LABELS = {
    "Learning Platform administration": "Administrarea platformei de învățare",
    "Accounts and links": "Conturi și legături",
    "Accounts": "Conturi",
    "account": "cont",
    "accounts": "conturi",
    "full name": "nume complet",
    "date of birth": "data nașterii",
    "role": "rol",
    "preferred language": "limba preferată",
    "Teacher": "Profesor",
    "Parent/Guardian": "Părinte/Tutore",
    "Admin": "Administrator",
    "parent-child link": "legătură părinte-copil",
    "parent-child links": "legături părinte-copil",
    "created by": "creat de",
    "created at": "creat la",
    "Audit log": "Jurnal de audit",
    "audit log entry": "intrare în jurnalul de audit",
    "audit log entries": "intrări în jurnalul de audit",
    "Sign-in lockouts": "Blocări la autentificare",
}


def _catalogue(language):
    text = (LOCALE / language / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, flags=re.MULTILINE))


def test_the_story_has_seven_guard_and_link_messages():
    assert len(MESSAGES) == 7


@pytest.mark.parametrize(("msgid", "romanian"), {**MESSAGES, **TITLES_AND_LABELS}.items())
def test_romanian_translation_exists(msgid, romanian):
    assert _catalogue("ro")[msgid] == romanian


@pytest.mark.parametrize("msgid", [*MESSAGES, *TITLES_AND_LABELS])
def test_english_entry_exists(msgid):
    assert _catalogue("en")[msgid] == msgid


def test_romanian_admin_shows_translated_model_names(admin_client, compiled_catalogues):
    content = admin_client.get("/ro/admin/").content.decode()

    for text in [
        "Conturi",
        "Legături părinte-copil",
        "Jurnal de audit",
        "Blocări la autentificare",
    ]:
        assert text in content


def test_guard_message_is_shown_in_romanian(
    admin_client, linked_parent, student, compiled_catalogues
):
    response = admin_client.post(
        f"/ro/admin/accounts/usermodel/{student.pk}/change/",
        change_data(student, role="TEACHER"),
    )

    assert "Eliminați legăturile elevului cu părinții" in response.content.decode()


def test_duplicate_link_message_is_shown_in_romanian(admin_client, compiled_catalogues):
    link = ParentChildLinkFactory(parent=ParentFactory(), student=StudentFactory())

    response = admin_client.post(
        "/ro/admin/accounts/parentchildlinkmodel/add/",
        {"parent": link.parent_id, "student": link.student_id},
    )

    assert "Acest părinte este deja legat de acest elev." in response.content.decode()
