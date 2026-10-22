import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.utils import translation

from infrastructure.web.common.i18n import content_language, localized

SUBJECT = SimpleNamespace(name_ro="Matematică", name_en="Mathematics")
RO_CATALOGUE = (
    Path(__file__).resolve().parents[3] / "src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po"
)


@pytest.mark.parametrize(
    ("active", "expected"),
    [("ro", "ro"), ("en", "en"), ("en-us", "en"), ("en-GB", "en"), ("de", "ro"), ("", "ro")],
)
def test_content_language_maps_active_language(active, expected):
    with translation.override(active or None):
        assert content_language() == expected


def test_localized_reads_the_active_language_field():
    with translation.override("en"):
        assert localized(SUBJECT, "name") == "Mathematics"
    with translation.override("ro"):
        assert localized(SUBJECT, "name") == "Matematică"


def test_localized_fails_loudly_for_missing_field():
    with translation.override("ro"), pytest.raises(AttributeError):
        localized(SUBJECT, "title")


def test_localized_never_falls_back_to_the_other_language():
    only_ro = SimpleNamespace(name_ro="Matematică")

    with translation.override("en"), pytest.raises(AttributeError):
        localized(only_ro, "name")


def _po_entries(text: str) -> list[dict[str, str | bool]]:
    """Minimal .po parser (no gettext needed): msgid/msgstr with continuation lines."""
    entries = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        fuzzy = any(line.startswith("#,") and "fuzzy" in line for line in lines)
        fields: dict[str, str] = {}
        current = None
        for line in lines:
            if line.startswith("#"):
                continue
            match = re.match(r'^(msgid|msgstr(?:\[\d+\])?|msgid_plural|msgctxt) "(.*)"$', line)
            if match:
                current = match.group(1)
                fields[current] = match.group(2)
            elif line.startswith('"') and current:
                fields[current] += line.strip()[1:-1]
        if "msgid" in fields:
            msgstrs = [v for k, v in fields.items() if k.startswith("msgstr")]
            entries.append({"msgid": fields["msgid"], "translated": all(msgstrs), "fuzzy": fuzzy})
    return entries


def test_translations_complete():
    # Patterns §12.4: no empty msgstr and no fuzzy entry in the RO catalogue (header excluded).
    entries = [e for e in _po_entries(RO_CATALOGUE.read_text(encoding="utf-8")) if e["msgid"]]

    missing = [e["msgid"] for e in entries if not e["translated"]]
    fuzzy = [e["msgid"] for e in entries if e["fuzzy"]]
    assert entries, "RO catalogue has no entries"
    assert missing == [], f"Missing RO translations: {missing}"
    assert fuzzy == [], f"Fuzzy RO translations: {fuzzy}"


@pytest.mark.parametrize(
    ("po", "problem"),
    [
        ('msgid "Hello"\nmsgstr ""\n', "missing"),
        ('#, fuzzy\nmsgid "Hello"\nmsgstr "Salut"\n', "fuzzy"),
        ('msgid "Hello"\nmsgid_plural "Hellos"\nmsgstr[0] "Salut"\nmsgstr[1] ""\n', "missing"),
    ],
)
def test_completeness_parser_detects_problems(po, problem):
    header = 'msgid ""\nmsgstr ""\n"Language: ro\\n"\n\n'
    entries = [e for e in _po_entries(header + po) if e["msgid"]]

    assert entries
    assert (not entries[0]["translated"]) if problem == "missing" else entries[0]["fuzzy"]


def test_completeness_parser_reads_multiline_strings():
    po = 'msgid ""\n"Long "\n"text"\nmsgstr ""\n"Text "\n"lung"\n'

    assert _po_entries(po) == [{"msgid": "Long text", "translated": True, "fuzzy": False}]
