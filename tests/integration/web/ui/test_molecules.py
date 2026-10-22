"""Molecule primitives (Story 1.6), part 1: Story Tests block, field, pair, alert, card, tile.

Part 2 (empty state, page header, dialog, table) is test_molecules_layout.py.
"""

import re

import pytest
from django import forms
from django.template import Context, Template
from django.utils import translation

from infrastructure.web.templatetags.ui import Cell


def render(source: str, **context: object) -> str:
    with translation.override("en"):
        return Template("{% load ui %}" + source).render(Context(context))


class SampleForm(forms.Form):
    title_ro = forms.CharField(label="Title")
    title_en = forms.CharField(label="Title")


class SuffixedForm(forms.Form):
    title_ro = forms.CharField(label="Title (RO)")
    title_en = forms.CharField(label="Title (EN)", required=False)
    note = forms.CharField(label="Note", required=False)


def invalid_form() -> SampleForm:
    form = SampleForm(data={})
    form.is_valid()
    return form


# --- Story Tests block (verbatim) --------------------------------------------------------------


def test_field_without_errors_has_label_and_no_invalid_flag():
    html = render("{% ui_field f.title_ro %}", f=SampleForm())

    assert '<label class="field__label" for="id_title_ro">' in html
    assert "aria-invalid" not in html
    assert "(required)" in html


def test_field_with_errors_is_associated_and_flagged():
    form = SampleForm(data={})
    form.is_valid()

    html = render('{% ui_field f.title_ro help="Shown to students" %}', f=form)

    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="id_title_ro_help id_title_ro_error"' in html
    assert 'id="id_title_ro_error"' in html


def test_field_pair_labels_languages():
    html = render("{% ui_field_pair f.title_ro f.title_en %}", f=SampleForm())

    assert "<fieldset" in html
    assert "<legend" in html
    assert 'lang="ro"' in html
    assert 'lang="en"' in html
    assert "Română" in html
    assert "English" in html


@pytest.mark.parametrize(
    ("level", "role"),
    [("error", "alert"), ("warning", "alert"), ("info", "status"), ("success", "status")],
)
def test_alert_roles(level, role):
    assert f'role="{role}"' in render("{% ui_alert lvl 'Saved' %}", lvl=level)


def test_alert_rejects_unknown_level():
    with pytest.raises(ValueError, match="Unknown alert level"):
        render('{% ui_alert "fatal" "x" %}')


def test_disabled_tile_is_not_interactive():
    html = render('{% ui_disabled_tile "Grade 5" %}')

    assert 'aria-disabled="true"' in html
    assert "<a " not in html
    assert "<button" not in html
    assert "tabindex" not in html
    assert "Unavailable" in html


def test_confirm_dialog_contains_its_own_csrf_form():
    html = render(
        '{% ui_confirm_dialog "d1" "Submit test?" "You have one attempt." "Submit" "/x/" %}',
        csrf_token="tok",
    )

    assert '<dialog id="d1"' in html
    assert 'action="/x/"' in html
    assert 'name="csrfmiddlewaretoken"' in html
    assert "data-dialog-close" in html


def test_dialog_trigger_has_noscript_fallback_text():
    html = render('{% ui_dialog_trigger "d1" "Submit" %}')

    assert 'data-dialog-open="d1"' in html
    assert 'type="button"' in html
    assert "<noscript>" in html


def test_table_renders_cells_and_header_scope():
    rows = [["Ana", Cell("Active", pill="ACTIVE"), Cell("Open", href="/ro/x/")]]

    html = render(
        '{% ui_table cols rows "Scores" "No scores yet." %}',
        cols=["Name", "Status", "Link"],
        rows=rows,
    )

    assert html.count('scope="col"') == 3
    assert "pill--active" in html
    assert 'href="/ro/x/"' in html
    assert "<caption" in html


def test_empty_table_renders_empty_state_instead():
    html = render('{% ui_table cols rows "Scores" "No scores yet." %}', cols=["Name"], rows=[])

    assert "<table" not in html
    assert "No scores yet." in html


def test_table_rejects_unsupported_cells():
    with pytest.raises(ValueError, match="Unsupported cell"):
        render('{% ui_table cols rows "c" "e" %}', cols=["x"], rows=[[{"html": "<b>"}]])


def test_breadcrumb_marks_current_page():
    html = render(
        '{% ui_page_header "Chapter 1" crumbs %}',
        crumbs=[("Catalogue", "/ro/catalogue/"), ("Chapter 1", "")],
    )

    assert 'aria-label="Breadcrumb"' in html
    assert 'aria-current="page"' in html


# --- ui_field ----------------------------------------------------------------------------------


def test_field_renders_django_widget_with_matching_id_when_unbound():
    html = render("{% ui_field f.title_ro %}", f=SampleForm())

    assert '<div class="field">' in html
    assert re.search(r'<input type="text" name="title_ro"[^>]*id="id_title_ro"', html)
    assert "aria-describedby" not in html
    assert "field__error" not in html


def test_field_error_ids_only_error_when_no_help():
    html = render("{% ui_field f.title_ro %}", f=invalid_form())

    assert 'aria-describedby="id_title_ro_error"' in html
    assert 'class="field field--invalid"' in html
    assert 'class="field__error field-error" id="id_title_ro_error"' in html
    assert "This field is required." in html
    assert "#warning-circle" in html


def test_field_help_is_described_when_valid():
    html = render("{% ui_field f.title_ro help=h %}", f=SampleForm(), h="Shown <b>")

    assert '<p class="field__help" id="id_title_ro_help">Shown &lt;b&gt;</p>' in html
    assert 'aria-describedby="id_title_ro_help"' in html
    assert "aria-invalid" not in html


def test_field_optional_has_no_required_suffix():
    html = render("{% ui_field f.note %}", f=SuffixedForm())

    assert "(required)" not in html
    assert "field__required" not in html


def test_field_required_suffix_is_translated_markup():
    html = render("{% ui_field f.title_ro %}", f=SampleForm())

    assert '<span class="field__required">(required)</span>' in html


def test_field_rejects_non_bound_field():
    with pytest.raises(ValueError, match="Expected a form field"):
        render("{% ui_field 'title' %}")


# --- ui_field_pair -----------------------------------------------------------------------------


def test_field_pair_columns_and_language_labels():
    html = render("{% ui_field_pair f.title_ro f.title_en %}", f=SampleForm())

    assert '<fieldset class="field-pair">' in html
    assert '<legend class="field-pair__legend">Title</legend>' in html
    assert '<div class="field-pair__columns">' in html
    assert html.count('<div class="field-pair__column">') == 2
    assert '<span class="field-pair__lang">Română</span>' in html
    assert '<span class="field-pair__lang">English</span>' in html
    assert re.search(
        r'<input[^>]*name="title_ro"[^>]*lang="ro"|lang="ro"[^>]*name="title_ro"', html
    )
    assert re.search(
        r'<input[^>]*name="title_en"[^>]*lang="en"|lang="en"[^>]*name="title_en"', html
    )


def test_field_pair_legend_strips_language_suffix():
    html = render("{% ui_field_pair f.title_ro f.title_en %}", f=SuffixedForm())

    assert '<legend class="field-pair__legend">Title</legend>' in html
    assert "(RO)" not in html
    assert "(EN)" not in html


def test_field_pair_legend_keeps_words_ending_in_ro():
    class IntroForm(forms.Form):
        intro_ro = forms.CharField(label="Intro")
        intro_en = forms.CharField(label="Intro")

    html = render("{% ui_field_pair f.intro_ro f.intro_en %}", f=IntroForm())

    assert '<legend class="field-pair__legend">Intro</legend>' in html


def test_field_pair_shows_errors_per_column():
    form = SuffixedForm(data={"title_en": "x"})
    form.is_valid()

    html = render("{% ui_field_pair f.title_ro f.title_en %}", f=form)

    assert 'id="id_title_ro_error"' in html
    assert 'id="id_title_en_error"' not in html
    assert html.count('aria-invalid="true"') == 1


def test_field_pair_rejects_non_fields():
    with pytest.raises(ValueError, match="Expected a form field"):
        render("{% ui_field_pair 'a' 'b' %}")


# --- ui_alert ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("level", "icon"),
    [
        ("info", "bell"),
        ("success", "check-circle"),
        ("warning", "warning-circle"),
        ("error", "warning-circle"),
    ],
)
def test_alert_shows_level_icon_and_message(level, icon):
    html = render("{% ui_alert lvl msg %}", lvl=level, msg="<i>Saved</i>")

    assert f'class="alert alert--{level}"' in html
    assert f"#{icon}" in html
    assert '<p class="alert__message">&lt;i&gt;Saved&lt;/i&gt;</p>' in html


def test_dismissible_alert_has_translated_close_button():
    html = render("{% ui_alert 'info' 'Saved' %}")

    assert 'class="alert__close"' in html
    assert "data-dismiss" in html
    assert 'type="button"' in html
    assert 'aria-label="Close"' in html


def test_non_dismissible_alert_has_no_close_button():
    html = render("{% ui_alert 'error' 'Failed' dismissible=False %}")

    assert "data-dismiss" not in html
    assert "<button" not in html


# --- ui_card -----------------------------------------------------------------------------------


def test_plain_card_has_title_body_and_meta():
    html = render("{% ui_card 'Grade 5' body='Six chapters' meta='Updated' %}")

    assert '<article class="card">' in html
    assert '<h2 class="card__title">Grade 5</h2>' in html
    assert '<p class="card__body">Six chapters</p>' in html
    assert '<p class="card__meta">Updated</p>' in html
    assert "<a " not in html


def test_linked_card_has_single_link_in_title():
    html = render("{% ui_card 'Grade 5' href='/ro/g5/' icon='book-open' %}")

    assert '<article class="card card--link">' in html
    assert html.count("<a ") == 1
    assert '<h2 class="card__title"><a href="/ro/g5/">Grade 5</a></h2>' in html
    assert "#book-open" in html
    assert "card__body" not in html
    assert "card__meta" not in html


def test_card_rejects_unknown_icon():
    with pytest.raises(ValueError, match="Unknown icon"):
        render("{% ui_card 'x' icon='rocket' %}")


@pytest.mark.parametrize("href", ["javascript:alert(1)", " JavaScript:x", "data:text/html,x"])
def test_card_rejects_script_urls(href):
    with pytest.raises(ValueError, match="script URL"):
        render("{% ui_card 'x' href=h %}", h=href)


def test_card_escapes_context_values():
    html = render("{% ui_card t body=b %}", t="<b>T</b>", b="<script>")

    assert "&lt;b&gt;T&lt;/b&gt;" in html
    assert "&lt;script&gt;" in html


# --- ui_disabled_tile --------------------------------------------------------------------------


def test_disabled_tile_markup_and_reason():
    html = render("{% ui_disabled_tile 'Grade 5' reason='Not published' %}")

    assert '<div class="tile tile--disabled" aria-disabled="true">' in html
    assert "#lock-simple" in html
    assert "icon--20" in html
    assert '<span class="tile__title">Grade 5</span>' in html
    assert '<span class="tile__status">Unavailable</span>' in html
    assert '<span class="tile__reason">Not published</span>' in html
    assert html.count("href=") == 1  # only the sprite <use href>, no link


def test_disabled_tile_without_reason():
    assert "tile__reason" not in render("{% ui_disabled_tile 'Grade 5' %}")
