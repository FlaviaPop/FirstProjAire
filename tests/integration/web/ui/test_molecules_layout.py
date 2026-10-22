"""Molecule primitives (Story 1.6), part 2: empty state, page header, confirm dialog, table.

Split from test_molecules.py to keep both files under the 400-line limit (patterns §17).
"""

import re

import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.utils import translation

from infrastructure.web.templatetags.ui import Cell


def render(source: str, **context: object) -> str:
    with translation.override("en"):
        return Template("{% load ui %}" + source).render(Context(context))


# --- ui_empty_state ----------------------------------------------------------------------------


def test_empty_state_with_action_renders_button_link():
    html = render("{% ui_empty_state 'Nothing yet.' 'Create' '/ro/new/' %}")

    assert '<div class="empty-state">' in html
    assert '<p class="empty-state__message">Nothing yet.</p>' in html
    assert (
        '<a class="button button--primary empty-state__action" href="/ro/new/">Create</a>' in html
    )
    assert "#list-checks" in html
    assert "icon--32" in html


@pytest.mark.parametrize(("label", "url"), [("Create", ""), ("", "/ro/new/"), ("", "")])
def test_empty_state_without_both_action_args_has_no_link(label, url):
    html = render("{% ui_empty_state 'Nothing yet.' l u %}", l=label, u=url)

    assert "<a " not in html


def test_empty_state_uses_theme_icon_variant():
    html = render("{% ui_empty_state 'x' icon='users' %}", icon_variant="duotone")

    assert "#users-duotone" in html


def test_empty_state_defaults_to_regular_icon():
    assert "#list-checks-duotone" not in render("{% ui_empty_state 'x' %}")


def test_empty_state_rejects_script_action_url():
    with pytest.raises(ValueError, match="script URL"):
        render("{% ui_empty_state 'x' 'Go' 'javascript:x' %}")


# --- ui_page_header ----------------------------------------------------------------------------


def test_page_header_structure_with_crumbs_and_actions():
    html = render(
        "{% ui_page_header 'Chapter 1' crumbs acts %}",
        crumbs=[("Catalogue", "/ro/catalogue/"), ("Grade 5", "/ro/g5/"), ("Chapter 1", "")],
        acts=[("Edit", "/ro/edit/", "secondary"), ("Publish", "/ro/pub/", "primary")],
    )

    assert '<header class="page-header">' in html
    assert '<nav class="breadcrumb" aria-label="Breadcrumb">' in html
    assert '<ol class="breadcrumb__list">' in html
    assert html.count('class="breadcrumb__item"') == 3
    assert html.count("#caret-right") == 2
    assert '<a href="/ro/catalogue/">Catalogue</a>' in html
    assert html.count('aria-current="page"') == 1
    assert re.search(r'aria-current="page"[^>]*>\s*(<svg.*?</svg>\s*)?Chapter 1', html, re.S)
    assert '<h1 class="page-header__title">Chapter 1</h1>' in html
    assert '<a class="button button--secondary" href="/ro/edit/">Edit</a>' in html
    assert '<a class="button button--primary" href="/ro/pub/">Publish</a>' in html


def test_page_header_without_crumbs_or_actions():
    html = render("{% ui_page_header 'Home' %}")

    assert "<nav" not in html
    assert "page-header__actions" not in html
    assert '<h1 class="page-header__title">Home</h1>' in html


def test_page_header_rejects_unknown_action_variant():
    with pytest.raises(TemplateSyntaxError):
        render("{% ui_page_header 'x' actions=a %}", a=[("Go", "/x/", "ghost")])


@pytest.mark.parametrize("crumbs", [[("only-label",)], [("a", "b", "c")]])
def test_page_header_rejects_malformed_crumbs(crumbs):
    with pytest.raises(ValueError, match="must have 2 values"):
        render("{% ui_page_header 'x' c %}", c=crumbs)


def test_page_header_rejects_script_crumb_url():
    with pytest.raises(ValueError, match="script URL"):
        render("{% ui_page_header 'x' c %}", c=[("a", "javascript:x"), ("b", "")])


# --- ui_confirm_dialog / ui_dialog_trigger -----------------------------------------------------


def test_confirm_dialog_structure_and_hidden_inputs():
    html = render(
        "{% ui_confirm_dialog 'd1' 'Delete?' 'Gone forever.' 'Delete' '/x/' 'danger' hidden %}",
        csrf_token="tok",
        hidden={"id": '7"', "next": "/ro/"},
    )

    assert '<dialog id="d1" class="dialog" aria-labelledby="d1-title"' in html
    assert 'aria-describedby="d1-body"' in html
    assert '<form method="post" action="/x/" class="dialog__form">' in html
    assert '<input type="hidden" name="id" value="7&quot;">' in html
    assert '<input type="hidden" name="next" value="/ro/">' in html
    assert '<h2 class="dialog__title" id="d1-title">Delete?</h2>' in html
    assert '<p class="dialog__body" id="d1-body">Gone forever.</p>' in html
    assert 'class="button button--secondary" data-dialog-close>Cancel</button>' in html
    assert 'type="submit" class="button button--danger"' in html


def test_confirm_dialog_accepts_hidden_pairs():
    html = render(
        "{% ui_confirm_dialog 'd1' 't' 'b' 'Go' '/x/' hidden=h %}", h=[("a", 0), ("b", "")]
    )

    assert '<input type="hidden" name="a" value="0">' in html
    assert '<input type="hidden" name="b" value="">' in html


def test_confirm_dialog_includes_extra_template():
    html = render(
        "{% ui_confirm_dialog 'd1' 't' 'b' 'Go' '/x/' extra_template=tpl %}",
        tpl="components/status_pill.html",
    )

    assert '<span class="pill pill--' in html


def test_confirm_dialog_rejects_unknown_variant():
    with pytest.raises(TemplateSyntaxError):
        render("{% ui_confirm_dialog 'd1' 't' 'b' 'Go' '/x/' 'ghost' %}")


@pytest.mark.parametrize("dialog_id", ["", "1abc", "a b", 'x"y'])
def test_confirm_dialog_rejects_bad_ids(dialog_id):
    with pytest.raises(ValueError, match="Invalid dialog id"):
        render("{% ui_confirm_dialog i 't' 'b' 'Go' '/x/' %}", i=dialog_id)


def test_confirm_dialog_rejects_script_action():
    with pytest.raises(ValueError, match="script URL"):
        render("{% ui_confirm_dialog 'd1' 't' 'b' 'Go' 'javascript:x' %}")


def test_dialog_trigger_markup_and_noscript_text():
    html = render("{% ui_dialog_trigger 'd1' 'Delete sample' 'danger' %}")

    assert (
        '<button type="button" class="button button--danger" data-dialog-open="d1">'
        "Delete sample</button>" in html
    )
    assert (
        '<noscript><p class="dialog-noscript">'
        "JavaScript is required to confirm this action.</p></noscript>" in html
    )


def test_dialog_trigger_rejects_unknown_variant():
    with pytest.raises(TemplateSyntaxError):
        render("{% ui_dialog_trigger 'd1' 'x' 'ghost' %}")


def test_dialog_trigger_rejects_bad_id():
    with pytest.raises(ValueError, match="Invalid dialog id"):
        render("{% ui_dialog_trigger 'a b' 'x' %}")


# --- ui_table ----------------------------------------------------------------------------------


def test_table_structure_and_escaping():
    html = render(
        "{% ui_table cols rows 'Scores' 'none' %}",
        cols=["Name", "Score"],
        rows=[["<b>Ana</b>", 0], [Cell("0"), 87]],
    )

    assert '<div class="table-wrap"><table class="table">' in html
    assert '<caption class="table__caption">Scores</caption>' in html
    assert '<th scope="col">Name</th>' in html
    assert "<td>&lt;b&gt;Ana&lt;/b&gt;</td>" in html
    assert html.count("<td>0</td>") == 2
    assert "<td>87</td>" in html


def test_table_link_cell_escapes_href_and_text():
    html = render(
        "{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[[Cell("<i>", href='/x?a="b"')]]
    )

    assert '<td><a href="/x?a=&quot;b&quot;">&lt;i&gt;</a></td>' in html


@pytest.mark.parametrize("cell", [True, None, 1.5, {"html": "<b>"}, ["x"]])
def test_table_rejects_non_str_int_cell_types(cell):
    with pytest.raises(ValueError, match=r"^Unsupported cell"):
        render("{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[[cell]])


def test_table_rejects_unknown_pill_status():
    with pytest.raises(ValueError, match="Unknown status"):
        render("{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[[Cell("x", pill="NOPE")]])


def test_table_rejects_cell_with_both_href_and_pill():
    cell = Cell("x", href="/x/", pill="ACTIVE")

    with pytest.raises(ValueError, match="either a link or a pill"):
        render("{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[[cell]])


def test_table_rejects_script_href():
    with pytest.raises(ValueError, match="script URL"):
        render(
            "{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[[Cell("x", href="javascript:1")]]
        )


def test_table_rejects_row_width_mismatch():
    with pytest.raises(ValueError, match="must have 2 cells"):
        render("{% ui_table cols rows 'c' 'e' %}", cols=["x", "y"], rows=[["only one"]])


def test_empty_table_uses_empty_state_and_theme_variant():
    html = render(
        "{% ui_table cols rows 'c' 'Nothing.' %}", cols=["x"], rows=(), icon_variant="duotone"
    )

    assert '<div class="empty-state">' in html
    assert "#list-checks-duotone" in html
    assert "<table" not in html
    assert "<caption" not in html


def test_table_rejects_unknown_theme_icon_variant():
    with pytest.raises(ValueError, match="Unknown icon variant"):
        render("{% ui_table cols rows 'c' 'e' %}", cols=["x"], rows=[], icon_variant="bold")


# --- Cell --------------------------------------------------------------------------------------


def test_cell_is_immutable():
    cell = Cell("x")

    with pytest.raises(AttributeError):
        cell.text = "y"  # type: ignore[misc]
