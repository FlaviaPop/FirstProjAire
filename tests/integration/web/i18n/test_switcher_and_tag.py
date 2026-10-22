import re
from types import SimpleNamespace

import pytest
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils import translation

pytestmark = pytest.mark.django_db


def _render_switcher(rf, path, lang, **context):
    request = rf.get(path)
    with translation.override(lang):
        return render_to_string("components/language_switcher.html", context, request=request)


@pytest.mark.parametrize("lang", ["ro", "en"])
def test_switcher_marks_exactly_the_current_language(rf, lang):
    html = _render_switcher(rf, f"/{lang}/accounts/login/", lang)

    other = "en" if lang == "ro" else "ro"
    assert re.search(rf'value="{lang}"[^>]*aria-pressed="true"', html)
    assert re.search(rf'value="{other}"[^>]*aria-pressed="false"', html)
    assert html.count('aria-pressed="true"') == 1


def test_switcher_is_a_csrf_protected_post_form_back_to_the_same_page(rf):
    html = _render_switcher(rf, "/ro/accounts/login/?next=/ro/x/", "ro")

    assert 'method="post"' in html
    assert 'action="/i18n/setlang/"' in html
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'name="next" value="/ro/accounts/login/?next=/ro/x/"' in html


def test_switcher_accessibility_attributes(rf):
    html = _render_switcher(rf, "/en/accounts/login/", "en")

    assert 'aria-label="Language"' in html
    assert 'lang="ro" title="Română"' in html
    assert 'lang="en" title="English"' in html
    assert html.count('type="submit" name="language"') == 2


def test_switcher_label_is_translated_to_romanian(rf, compiled_catalogues):
    assert 'aria-label="Limba"' in _render_switcher(rf, "/ro/", "ro")


# Review v1 ISS-003: regular icon for staff by default; the student layout passes duotone.
@pytest.mark.parametrize(
    ("context", "symbol"),
    [({}, '#translate"'), ({"icon_variant": "duotone"}, '#translate-duotone"')],
)
def test_switcher_icon_variant(rf, context, symbol):
    assert symbol in _render_switcher(rf, "/ro/", "ro", **context)


def test_switcher_has_no_script_or_inline_style(rf):
    html = _render_switcher(rf, "/ro/", "ro")

    assert "<script" not in html
    assert "style=" not in html


@pytest.mark.parametrize(("lang", "expected"), [("ro", "Matematică"), ("en", "Mathematics")])
def test_localized_tag_renders_the_active_language(lang, expected):
    subject = SimpleNamespace(name_ro="Matematică", name_en="Mathematics")
    template = Template('{% load i18n_content %}{% localized subject "name" %}')

    with translation.override(lang):
        assert template.render(Context({"subject": subject})) == expected


def test_localized_tag_autoescapes():
    subject = SimpleNamespace(name_ro="<b>x</b>", name_en="y")
    template = Template('{% load i18n_content %}{% localized subject "name" %}')

    with translation.override("ro"):
        assert template.render(Context({"subject": subject})) == "&lt;b&gt;x&lt;/b&gt;"
