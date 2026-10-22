"""Atom primitives (Story 1.5): every inclusion tag in templatetags/ui.py, valid and invalid."""

import re
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError
from django.utils import translation

WEB_DIR = settings.BASE_DIR / "src/infrastructure/web"


def render(source: str, **context: object) -> str:
    with translation.override("en"):
        return Template("{% load ui %}" + source).render(Context(context))


# --- ui_button ---------------------------------------------------------------------------------


def test_primary_button_has_spinner_and_label():
    html = render('{% ui_button "Save" %}')

    assert 'class="button button--primary"' in html
    assert 'class="button__spinner" aria-hidden="true"' in html
    assert ">Save<" in html
    assert 'type="submit"' in html


@pytest.mark.parametrize("variant", ["primary", "secondary", "danger", "link"])
def test_button_renders_each_variant_as_a_real_button(variant):
    html = render("{% ui_button 'Go' v 'button' %}", v=variant)

    assert html.strip().startswith("<button")
    assert f'class="button button--{variant}"' in html
    assert 'type="button"' in html


def test_button_rejects_unknown_variant():
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" "ghost" %}')


def test_button_rejects_unknown_type():
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" "primary" "image" %}')


def test_button_passes_through_only_hx_attributes_escaped():
    html = render('{% ui_button "Send" hx_post=url hx_disabled_elt="this" %}', url='/x?a="b"')

    assert 'hx-post="/x?a=&quot;b&quot;"' in html
    assert 'hx-disabled-elt="this"' in html


def test_button_rejects_non_hx_attributes():
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" onclick="alert(1)" %}')


def test_button_rejects_hx_on_inline_script_handlers():
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" hx_on__click="alert(1)" %}')


# Review v1 ISS-003: HTMX's other script paths (`js:` values, hx-vars) are refused as well.
@pytest.mark.parametrize(
    "kwarg", ['hx_vals="js:{a: 1}"', 'hx_headers=" javascript:{}"', 'hx_vars="a:1"']
)
def test_button_rejects_hx_attributes_that_evaluate_script(kwarg):
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" ' + kwarg + " %}")


def test_button_keeps_plain_json_hx_vals():
    html = render('{% ui_button "Save" hx_vals=vals %}', vals='{"step": 2}')

    assert 'hx-vals="{&quot;step&quot;: 2}"' in html


def test_button_label_name_and_value_are_autoescaped():
    html = render("{% ui_button label name=n value=v %}", label="<b>", n='a"b', v="<v>")

    assert ">&lt;b&gt;<" in html
    assert 'name="a&quot;b"' in html
    assert 'value="&lt;v&gt;"' in html


def test_button_without_name_or_value_omits_the_attributes():
    html = render('{% ui_button "Save" %}')

    assert "name=" not in html
    assert "value=" not in html


# Review v1 ISS-002: only "not given" omits the attribute; 0 or "" is a real value.
@pytest.mark.parametrize(("value", "expected"), [(0, 'value="0"'), ("", 'value=""')])
def test_button_keeps_a_falsy_value(value, expected):
    assert expected in render('{% ui_button "A" name="answer" value=v %}', v=value)


def test_button_with_icon_renders_a_decorative_20px_icon():
    html = render('{% ui_button "Save" icon="check-circle" %}')

    assert 'class="icon icon--20"' in html
    assert "#check-circle" in html
    assert 'focusable="false" aria-hidden="true"' in html


def test_button_with_unknown_icon_fails_loudly():
    with pytest.raises(ValueError, match="Unknown icon"):
        render('{% ui_button "Save" icon="nope" %}')


def test_disabled_button_is_natively_disabled_without_busy_state():
    html = render('{% ui_button "Save" disabled=True %}')

    assert " disabled" in html
    assert "aria-busy" not in html
    assert "htmx-request" not in html


def test_loading_button_shows_spinner_state_busy_and_disabled():
    html = render('{% ui_button "Save" loading=True %}')

    assert 'class="button button--primary htmx-request"' in html
    assert 'aria-busy="true"' in html
    assert " disabled" in html


# --- ui_icon -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "expected"), [("", 'aria-hidden="true"'), ("Home", 'aria-label="Home"')]
)
def test_icon_accessibility(label, expected):
    assert expected in render('{% ui_icon "house" 24 "regular" label %}', label=label)


def test_labelled_icon_has_img_role_and_is_not_hidden():
    html = render('{% ui_icon "house" 24 "regular" "Home" %}')

    assert 'role="img"' in html
    assert "aria-hidden" not in html


def test_icon_points_at_the_local_sprite():
    html = render('{% ui_icon "house" %}')

    assert '<use href="/static/icons/sprite.svg#house">' in html
    assert 'width="24" height="24"' in html


def test_duotone_icon_uses_duotone_symbol():
    assert "#book-open-duotone" in render('{% ui_icon "book-open" 32 "duotone" %}')


@pytest.mark.parametrize("size", [20, 24, 32])
def test_icon_accepts_each_catalogue_size(size):
    assert f'class="icon icon--{size}"' in render("{% ui_icon 'bell' s %}", s=size)


@pytest.mark.parametrize("args", ['"nope"', '"house" 18', '"house" 24 "filled"'])
def test_icon_rejects_unknown_inputs(args):
    with pytest.raises(ValueError, match="Unknown icon"):
        render("{% ui_icon " + args + " %}")


# --- ui_badge ----------------------------------------------------------------------------------


def test_badge_shows_number_and_full_meaning_for_screen_readers():
    html = render('{% ui_badge 3 "unread notifications" %}')

    assert 'class="badge"' in html
    assert 'aria-label="3 unread notifications"' in html
    assert ">3<" in html


def test_zero_badge_renders_nothing():
    assert render('{% ui_badge 0 "unread" %}').strip() == ""


def test_negative_badge_is_rejected():
    with pytest.raises(ValueError, match="Badge value"):
        render('{% ui_badge -1 "unread" %}')


# Review v1 ISS-001: numbers are never truncated (2.7 is a caller bug, not "2").
@pytest.mark.parametrize("value", [2.7, None, True, "abc"])
def test_badge_rejects_values_that_are_not_whole_numbers(value):
    with pytest.raises(ValueError, match="whole number"):
        render('{% ui_badge v "unread" %}', v=value)


# --- ui_status_pill ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "word"),
    [
        ("ACTIVE", "Active"),
        ("FLAGGED", "Flagged"),
        ("BLOCKED", "Blocked"),
        ("RESUBMITTED", "Resubmitted"),
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
    ],
)
def test_status_pill_always_shows_a_word(status, word):
    html = render("{% ui_status_pill s %}", s=status)

    assert f"pill--{status.lower()}" in html
    assert f">{word}<" in html


def test_status_pill_rejects_unknown_status():
    with pytest.raises(ValueError, match="Unknown status: ARCHIVED"):
        render('{% ui_status_pill "ARCHIVED" %}')


# --- ui_avatar ---------------------------------------------------------------------------------


def test_avatar_is_a_generic_icon_named_after_the_user():
    user = SimpleNamespace(get_full_name=lambda: "Ana <Pop>")

    html = render("{% ui_avatar user %}", user=user)

    assert 'role="img" aria-label="Ana &lt;Pop&gt;"' in html
    assert "#user-circle" in html
    assert "<img" not in html


@pytest.mark.parametrize("user", [None, SimpleNamespace(get_full_name=lambda: "  "), object()])
def test_avatar_without_a_name_falls_back_to_user(user):
    assert 'aria-label="User"' in render("{% ui_avatar user %}", user=user)


# --- ui_score ----------------------------------------------------------------------------------


@pytest.mark.parametrize("value", [1, 50, 100])
def test_score_announces_out_of_100(value):
    html = render("{% ui_score v %}", v=value)

    assert f'aria-label="Score: {value} out of 100"' in html
    assert f'class="score__value" aria-hidden="true">{value}<' in html
    assert "/ 100" in html


@pytest.mark.parametrize("value", [0, 101, -5])
def test_score_outside_range_is_rejected(value):
    with pytest.raises(ValueError, match="Score must be 1-100"):
        render("{% ui_score v %}", v=value)


# Review v1 ISS-001: 87.6 must fail loudly, never be shown as 87 to a child or parent.
@pytest.mark.parametrize("value", [87.6, 99.9, 100.4, Decimal("87.6"), True, None, "abc", ""])
def test_score_rejects_values_that_are_not_whole_numbers(value):
    with pytest.raises(ValueError, match="whole number"):
        render("{% ui_score v %}", v=value)


@pytest.mark.parametrize("value", [87, "87", 87.0, Decimal("87")])
def test_score_accepts_whole_numbers_in_any_form(value):
    assert 'aria-label="Score: 87 out of 100"' in render("{% ui_score v %}", v=value)


# --- ui_progress -------------------------------------------------------------------------------


def test_progress_shows_done_over_total_with_a_labelled_bar():
    html = render('{% ui_progress 3 8 "Exercises" %}')

    assert 'value="3" max="8"' in html
    assert 'aria-valuetext="3 of 8"' in html
    assert '<span class="progress__text">3/8</span>' in html
    assert re.search(r"<label[^>]*>\s*<span[^>]*>Exercises</span>\s*<progress", html)


def test_progress_with_zero_total_shows_zero_of_zero():
    html = render('{% ui_progress 0 0 "Exercises" %}')

    assert 'value="0" max="1"' in html
    assert "0/0" in html


@pytest.mark.parametrize(("done", "total"), [(9, 8), (-1, 8), (0, -1)])
def test_progress_rejects_impossible_counts(done, total):
    with pytest.raises(ValueError, match="Invalid progress"):
        render("{% ui_progress d t 'Exercises' %}", d=done, t=total)


# Review v1 ISS-001: 2.9 of 3 must not be shown as "2/3".
@pytest.mark.parametrize(("done", "total"), [(2.9, 3), (2, 3.5), (None, 3)])
def test_progress_rejects_counts_that_are_not_whole_numbers(done, total):
    with pytest.raises(ValueError, match="whole number"):
        render("{% ui_progress d t 'Exercises' %}", d=done, t=total)


# --- cross-cutting -----------------------------------------------------------------------------


def test_rendering_is_deterministic():
    source = '{% ui_button "Save" icon="house" %}{% ui_progress 3 8 "Exercises" %}{% ui_score 7 %}'

    assert render(source) == render(source)


def test_no_component_or_css_references_external_urls():
    roots = [
        WEB_DIR / "templates/components",
        WEB_DIR / "templates/styleguide",
        WEB_DIR / "static/css",
    ]
    offenders = [
        str(p)
        for root in roots
        for p in root.rglob("*.*")
        if "http://" in p.read_text(encoding="utf-8") or "https://" in p.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_sprite_only_mentions_the_svg_namespace_url():
    sprite = (WEB_DIR / "static/icons/sprite.svg").read_text(encoding="utf-8")

    urls = set(re.findall(r"https?://[^\s\"'<>]+", sprite))

    assert urls == {"http://www.w3.org/2000/svg"}


def primitive_templates() -> list:
    return [
        *(WEB_DIR / "templates/components").glob("*.html"),
        *(WEB_DIR / "templates/styleguide").glob("*.html"),
    ]


@pytest.mark.parametrize("pattern", [r"\bstyle=", r"<style", r"\|\s*safe", "mark_safe"])
def test_component_and_styleguide_templates_have_no_inline_style_or_safe(pattern):
    templates = primitive_templates()
    offenders = [str(p) for p in templates if re.search(pattern, p.read_text(encoding="utf-8"))]

    assert templates
    assert offenders == []


# The `<script` rule moved to test_inline_script.py (Story 1.6): it now forbids INLINE scripts
# only, because AC 12 loads ui.js in the styleguide as an external same-origin module.
