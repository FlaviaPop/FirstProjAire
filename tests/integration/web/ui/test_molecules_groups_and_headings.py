"""Story 1.6 review v1: choice groups in ui_field (ISS-001), card heading level (ISS-003),
and alert-dismiss focus handling in ui.js (ISS-002)."""

import re

import pytest
from django import forms
from django.conf import settings
from django.template import Context, Template
from django.utils import translation

from infrastructure.web.templatetags.ui import Cell

UI_JS = settings.BASE_DIR / "src/infrastructure/web/static/js/ui.js"


def render(source: str, **context: object) -> str:
    with translation.override("en"):
        return Template("{% load ui %}" + source).render(Context(context))


class ChoiceForm(forms.Form):
    answer = forms.ChoiceField(
        label="Answer", choices=[("a", "A"), ("b", "B")], widget=forms.RadioSelect
    )
    topics = forms.MultipleChoiceField(
        label="Topics", choices=[("x", "X"), ("y", "Y")], widget=forms.CheckboxSelectMultiple
    )
    name = forms.CharField(label="Name")


def invalid_choice_form() -> ChoiceForm:
    form = ChoiceForm(data={})
    form.is_valid()
    return form


# --- ISS-001: choice groups and forms without ids ----------------------------------------------


@pytest.mark.parametrize("name", ["answer", "topics"])
def test_choice_group_uses_fieldset_and_legend_not_an_orphan_label(name):
    html = render("{% ui_field f." + name + " %}", f=ChoiceForm())

    assert '<fieldset class="field field--group"' in html
    assert re.search(r'<legend class="field__label">\s*\w+', html)
    assert 'for=""' not in html
    assert '<label class="field__label"' not in html


@pytest.mark.parametrize("name", ["answer", "topics"])
def test_choice_group_help_and_error_ids_are_unique_to_the_field(name):
    html = render("{% ui_field f." + name + ' help="Pick" %}', f=invalid_choice_form())

    assert f'id="id_{name}_help"' in html
    assert f'id="id_{name}_error"' in html
    assert f'aria-describedby="id_{name}_help id_{name}_error"' in html
    assert 'id="_help"' not in html
    assert 'id="_error"' not in html


def test_choice_group_marks_the_group_invalid_once():
    html = render("{% ui_field f.answer %}", f=invalid_choice_form())

    assert re.search(r'<fieldset[^>]*aria-invalid="true"', html)
    assert html.count('aria-describedby="id_answer_error"') == 1


def test_single_input_markup_is_unchanged_next_to_a_group():
    html = render("{% ui_field f.name %}", f=ChoiceForm())

    assert '<label class="field__label" for="id_name">' in html
    assert "<fieldset" not in html


def test_field_without_auto_id_fails_loudly():
    with pytest.raises(ValueError, match="auto_id"):
        render("{% ui_field f.name %}", f=ChoiceForm(auto_id=False))


def test_field_pair_without_auto_id_fails_loudly():
    with pytest.raises(ValueError, match="auto_id"):
        render("{% ui_field_pair f.name f.name %}", f=ChoiceForm(auto_id=False))


# --- ISS-003: card heading level ---------------------------------------------------------------


def test_card_heading_defaults_to_h2():
    html = render('{% ui_card "Matematică" %}')

    assert '<h2 class="card__title">' in html
    assert "</h2>" in html


@pytest.mark.parametrize("level", [3, 4, "3"])
def test_card_heading_level_is_chosen_by_the_caller(level):
    html = render('{% ui_card "Matematică" href="/ro/x/" level=lvl %}', lvl=level)

    assert f'<h{int(level)} class="card__title"><a href="/ro/x/">' in html
    assert f"</h{int(level)}>" in html


@pytest.mark.parametrize("level", [1, 5, 0, "h3", None, 2.5])
def test_card_rejects_heading_levels_outside_2_to_4(level):
    with pytest.raises(ValueError, match="heading level"):
        render('{% ui_card "Matematică" level=lvl %}', lvl=level)


def test_cell_is_still_importable_from_the_ui_module():
    assert Cell("x").text == "x"


# --- ISS-002: dismissing an alert keeps keyboard focus on the page -----------------------------


def test_ui_js_moves_focus_to_main_before_removing_a_focused_alert():
    source = UI_JS.read_text(encoding="utf-8")
    dismiss = source[source.index("[data-dismiss]") :]

    assert "contains(document.activeElement)" in dismiss
    assert dismiss.index(".focus()") < dismiss.index(".remove()")
    assert "getElementById('content')" in dismiss
