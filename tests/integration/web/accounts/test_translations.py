"""AC 15: RO and EN catalogue entries exist for every msgid Story 1.2 introduces.

GNU gettext isn't installed on the dev machine, so the catalogues are checked as text,
not compiled (Story 1.4 compiles them and adds the project-wide completeness test).
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

LOCALE = Path(settings.BASE_DIR) / "src/infrastructure/i18n/locale"
STORY_MSGIDS = {
    "Sign in": "Autentificare",
    "Username": "Nume de utilizator",
    "Password": "Parolă",
    "Incorrect username or password.": "Nume de utilizator sau parolă incorecte.",
    "Too many attempts": "Prea multe încercări",
    "Too many failed attempts. Try again in 15 minutes or ask the administrator.": (
        "Prea multe încercări eșuate. Încearcă din nou peste 15 minute "
        "sau cere ajutorul administratorului."
    ),
}


def _catalogue(language):
    text = (LOCALE / language / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, flags=re.MULTILINE))


@pytest.mark.parametrize(("msgid", "romanian"), STORY_MSGIDS.items())
def test_romanian_translation_exists(msgid, romanian):
    assert _catalogue("ro")[msgid] == romanian


@pytest.mark.parametrize("msgid", STORY_MSGIDS)
def test_english_entry_exists(msgid):
    assert _catalogue("en")[msgid] in {"", msgid}
