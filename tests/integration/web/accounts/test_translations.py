"""AC 15: RO and EN catalogue entries exist for every msgid Story 1.2 introduces.

The catalogues are checked as text, so this runs without GNU gettext (Story 1.4 adds the
project-wide completeness test and compiles them).
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
}
# Review v1 ISS-002: the lockout sentence is a plural message driven by AXES_COOLOFF_TIME.
LOCKOUT_SINGULAR = (
    "Too many failed attempts. Try again in %(minutes)s minute or ask the administrator."
)


def _catalogue(language):
    text = (LOCALE / language / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, flags=re.MULTILINE))


@pytest.mark.parametrize(("msgid", "romanian"), STORY_MSGIDS.items())
def test_romanian_translation_exists(msgid, romanian):
    assert _catalogue("ro")[msgid] == romanian


@pytest.mark.parametrize("msgid", STORY_MSGIDS)
def test_english_entry_exists(msgid):
    assert _catalogue("en")[msgid] in {"", msgid}


def _plural_forms(language, singular):
    text = (LOCALE / language / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
    match = re.search(
        rf'^msgid "{re.escape(singular)}"\nmsgid_plural "[^"]+"\n((?:msgstr\[\d\] ".*"\n)+)',
        text,
        flags=re.MULTILINE,
    )
    assert match, f"no plural entry for {singular!r} in {language}"
    return re.findall(r'^msgstr\[\d\] "(.*)"$', match.group(1), flags=re.MULTILINE)


def test_lockout_message_has_three_romanian_plural_forms():
    forms = _plural_forms("ro", LOCKOUT_SINGULAR)

    assert len(forms) == 3  # Romanian: 1 minut / 2-19 minute / 20+ de minute
    assert all("%(minutes)s" in form for form in forms)
    assert "%(minutes)s minut sau" in forms[0]
    assert "%(minutes)s minute sau" in forms[1]
    assert "%(minutes)s de minute" in forms[2]


def test_lockout_message_has_two_english_plural_forms():
    forms = _plural_forms("en", LOCKOUT_SINGULAR)

    assert len(forms) == 2
    assert all("%(minutes)s" in form for form in forms)
