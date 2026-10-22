"""Static checks on the molecule stylesheets and ui.js (Story 1.6, AC 9, 11, 13).

There is no JS test tooling in this project (dialog behaviour is exercised by Playwright in
Story 1.10), so ui.js is verified here by assertions on its source text.
"""

import re

import pytest
from django.conf import settings

STATIC = settings.BASE_DIR / "src/infrastructure/web/static"
COMPONENTS_CSS = STATIC / "css/components"
UI_JS = STATIC / "js/ui.js"
MOLECULES = [
    "form_field",
    "alert",
    "card",
    "disabled_tile",
    "empty_state",
    "page_header",
    "confirm_dialog",
    "table",
]


def css(name: str) -> str:
    return (COMPONENTS_CSS / f"{name}.css").read_text(encoding="utf-8")


def rule_for(sheet: str, selector: str) -> str:
    """Concatenated bodies of every rule whose selector list contains ``selector``."""
    bodies = []
    sheet = re.sub(r"/\*.*?\*/", "", sheet, flags=re.DOTALL)
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", sheet):
        names = [s.strip() for s in selectors.split(",")]
        if selector in names:
            bodies.append(body)
    return "\n".join(bodies)


def js() -> str:
    return UI_JS.read_text(encoding="utf-8")


# --- Stylesheets -------------------------------------------------------------------------------


@pytest.mark.parametrize("molecule", MOLECULES)
def test_each_molecule_has_its_own_token_only_stylesheet(molecule):
    sheet = css(molecule)
    assert "var(--" in sheet
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", sheet)
    assert not re.search(r"rgba?\(", sheet)
    assert "!important" not in sheet
    assert not re.search(r"https?://", sheet)
    assert "outline: none" not in sheet
    assert len(sheet.splitlines()) < 400


@pytest.mark.parametrize("selector", [".card", ".error-card", ".login-card"])
def test_card_hooks_share_surface_radius_elevation_and_padding(selector):
    body = rule_for(css("card"), selector)
    assert "var(--color-surface)" in body
    assert "var(--radius" in body
    assert "var(--elevation-1)" in body
    assert "var(--space-6)" in body


def test_student_cards_get_32px_padding():
    sheet = css("card")
    assert "var(--space-8)" in rule_for(sheet, ".theme-student .card")
    assert "var(--space-8)" in rule_for(sheet, ".theme-student .login-card")


@pytest.mark.parametrize("selector", [".error-card", ".login-card"])
def test_error_and_login_cards_are_centred_with_560px_max_width(selector):
    body = rule_for(css("card"), selector)
    assert "max-width: 560px" in body
    assert "margin: var(--space-12) auto" in body


def test_error_card_violations_and_reference_are_styled():
    sheet = css("card")
    assert rule_for(sheet, ".error-card__violations")
    ref = rule_for(sheet, ".error-card__ref")
    assert "var(--color-muted)" in ref
    assert "var(--font-14)" in ref


def test_linked_card_is_fully_clickable_with_hover_and_focus_ring():
    sheet = css("card")
    assert "position: relative" in rule_for(sheet, ".card--link")
    stretched = rule_for(sheet, ".card--link .card__title a::after")
    assert 'content: ""' in stretched
    assert "inset: 0" in stretched
    assert "var(--elevation-2)" in rule_for(sheet, ".card--link:hover")
    focus = rule_for(sheet, ".card--link:focus-within")
    assert "var(--color-focus)" in focus


@pytest.mark.parametrize(
    ("variant", "border", "tint"),
    [
        ("info", "--color-primary", "--pill-resubmitted-bg"),
        ("success", "--color-success", "--pill-active-bg"),
        ("warning", "--color-warning", "--pill-flagged-bg"),
        ("error", "--color-error", "--pill-blocked-bg"),
    ],
)
def test_alert_variant_has_left_border_and_tint(variant, border, tint):
    body = rule_for(css("alert"), f".alert--{variant}")
    assert f"var({border})" in body
    assert f"var({tint})" in body


@pytest.mark.parametrize("selector", [".error-partial", ".form-banner--error"])
def test_error_hooks_get_the_error_alert_styles(selector):
    sheet = css("alert")
    assert rule_for(sheet, selector)
    assert "var(--color-error)" in rule_for(sheet, selector)
    assert "var(--pill-blocked-bg)" in rule_for(sheet, selector)


def test_alert_base_has_4px_left_border_and_text_colour():
    body = rule_for(css("alert"), ".alert")
    assert "border-left: 4px solid" in body
    assert "var(--color-text)" in body


def test_alert_close_button_is_at_least_32px():
    body = rule_for(css("alert"), ".alert__close")
    assert "var(--touch-min)" in body


def test_field_error_hook_matches_field_error_text():
    sheet = css("form_field")
    body = rule_for(sheet, ".field-error")
    assert "var(--color-error)" in body
    assert "var(--weight-semibold)" in body
    assert body == rule_for(sheet, ".field__error")


def test_field_inputs_and_invalid_state():
    sheet = css("form_field")
    assert "var(--weight-semibold)" in rule_for(sheet, ".field__label")
    widget = rule_for(sheet, ".field input")
    assert "1px solid var(--color-border)" in widget
    assert "var(--touch" in widget
    assert "var(--space-2) var(--space-3)" in widget
    assert "var(--space-3) var(--space-4)" in rule_for(sheet, ".theme-student .field input")
    assert "2px solid var(--color-error)" in rule_for(sheet, '[aria-invalid="true"]')
    assert "2px solid var(--color-error)" in rule_for(sheet, ".field--invalid input")
    assert "var(--color-muted)" in rule_for(sheet, ".field__help")


def test_field_pair_is_two_equal_columns_with_24px_gap():
    body = rule_for(css("form_field"), ".field-pair__columns")
    assert "grid-template-columns: 1fr 1fr" in body
    assert "var(--grid-gutter)" in body


def test_disabled_tile_looks_inactive():
    body = rule_for(css("disabled_tile"), ".tile--disabled")
    assert "var(--color-disabled)" in body
    assert "var(--color-muted)" in body
    assert "1px dashed var(--color-border)" in body
    assert "pointer-events" not in css("disabled_tile")


def test_empty_state_is_centred_and_muted():
    sheet = css("empty_state")
    assert "text-align: center" in rule_for(sheet, ".empty-state")
    assert "var(--color-muted)" in rule_for(sheet, ".empty-state__message")


def test_page_header_title_sizes_breadcrumb_and_actions():
    sheet = css("page_header")
    assert "var(--font-24)" in rule_for(sheet, ".page-header__title")
    assert "var(--weight-bold)" in rule_for(sheet, ".page-header__title")
    assert "var(--font-32)" in rule_for(sheet, ".theme-student .page-header__title")
    crumb = rule_for(sheet, ".breadcrumb")
    assert "var(--font-14)" in crumb
    assert "var(--color-muted)" in crumb
    assert "margin-left: auto" in rule_for(sheet, ".page-header__actions")


def test_confirm_dialog_uses_backdrop_token_and_480px_width():
    sheet = css("confirm_dialog")
    assert "var(--color-backdrop)" in rule_for(sheet, ".dialog::backdrop")
    body = rule_for(sheet, ".dialog")
    assert "max-width: 480px" in body
    assert "var(--elevation-3)" in body
    assert "var(--color-surface)" in body


def test_table_header_rows_cells_and_caption():
    sheet = css("table")
    assert "width: 100%" in rule_for(sheet, ".table")
    assert "var(--color-bg-staff)" in rule_for(sheet, ".table th")
    assert "var(--weight-semibold)" in rule_for(sheet, ".table th")
    assert "1px solid var(--color-disabled)" in rule_for(sheet, ".table td")
    assert "var(--space-2) var(--space-3)" in rule_for(sheet, ".table td")
    caption = rule_for(sheet, ".table__caption")
    assert "text-align: left" in caption
    assert "var(--font-16)" in caption


# --- ui.js --------------------------------------------------------------------------------------


def test_ui_js_exists_and_is_a_dependency_free_es_module():
    source = js()
    assert not re.search(r"^\s*import\s", source, re.MULTILINE)
    assert not re.search(r"https?://", source)
    assert len(source.splitlines()) < 400


@pytest.mark.parametrize(
    "forbidden",
    ["eval(", "new Function", "window.", "globalThis", "innerHTML", "var ", "setAttribute('on"],
)
def test_ui_js_has_no_globals_eval_or_inline_handlers(forbidden):
    assert forbidden not in js()


@pytest.mark.parametrize(
    "required",
    [
        "document.addEventListener('click'",
        "showModal()",
        "!dialog.open",
        "[data-dialog-open]",
        "dataset.dialogOpen",
        "[data-dialog-close]",
        "[data-dismiss]",
        "closest('.alert')",
        "new WeakMap()",
        "input, textarea, select, button",
        ".focus()",
        "?.close()",
        "?.remove()",
    ],
)
def test_ui_js_implements_the_story_behaviour(required):
    assert required in js()


def test_ui_js_returns_focus_on_close_with_a_capture_phase_listener():
    source = js()
    assert re.search(r"document\.addEventListener\('close',[\s\S]*?,\s*true\)", source)
    assert "instanceof HTMLDialogElement" in source


def test_ui_js_starts_with_a_csp_comment():
    assert js().lstrip().startswith("/*")
    assert "CSP" in js().split("*/", 1)[0]
