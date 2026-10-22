"""Design tokens, self-hosted assets and translations behind the atoms (Story 1.5).

The expected values are copied from docs/ui-ux/ui-ux-spec.md and 08-visual-foundation.md, so a
drift between the approved spec and tokens.css fails here.
"""

import re

import pytest
from django.conf import settings

from infrastructure.web.templatetags.ui import ICON_NAMES, STATUS_LABELS

WEB_DIR = settings.BASE_DIR / "src/infrastructure/web"
STATIC = WEB_DIR / "static"
TOKENS = (STATIC / "css/tokens.css").read_text(encoding="utf-8")
ATOMS = ["button", "icon", "badge", "status_pill", "avatar", "score", "progress_meter"]
LOCALE = settings.BASE_DIR / "src/infrastructure/i18n/locale"

SPEC_TOKENS = {
    "--color-primary": "#0E7490",
    "--color-primary-hover": "#155E75",
    "--color-accent": "#FBBF24",
    "--color-focus": "#C2410C",
    "--color-success": "#15803D",
    "--color-error": "#B91C1C",
    "--color-warning": "#B45309",
    "--color-text": "#1F2937",
    "--color-muted": "#4B5563",
    "--color-border": "#6B7280",
    "--color-bg-student": "#FFF8EC",
    "--color-bg-staff": "#F5F7FA",
    "--color-surface": "#FFFFFF",
    "--color-disabled": "#F3F4F6",
    "--pill-active-bg": "#DCFCE7",
    "--pill-active-fg": "#14532D",
    "--pill-flagged-bg": "#FEF3C7",
    "--pill-flagged-fg": "#78350F",
    "--pill-blocked-bg": "#FEE2E2",
    "--pill-blocked-fg": "#7F1D1D",
    "--pill-resubmitted-bg": "#CFFAFE",
    "--pill-resubmitted-fg": "#164E63",
    "--pill-draft-bg": "#F3F4F6",
    "--pill-draft-fg": "#1F2937",
    "--pill-published-bg": "#CFFAFE",
    "--pill-published-fg": "#164E63",
    "--space-1": "4px",
    "--space-2": "8px",
    "--space-3": "12px",
    "--space-4": "16px",
    "--space-6": "24px",
    "--space-8": "32px",
    "--space-12": "48px",
    "--space-16": "64px",
    "--font-family": "'Atkinson Hyperlegible Next', system-ui, sans-serif",
    "--font-size-base-student": "18px",
    "--font-size-base-staff": "16px",
    "--font-14": "14px",
    "--font-16": "16px",
    "--font-18": "18px",
    "--font-20": "20px",
    "--font-24": "24px",
    "--font-32": "32px",
    "--font-40": "40px",
    "--weight-regular": "400",
    "--weight-semibold": "600",
    "--weight-bold": "700",
    "--line-height-body": "1.6",
    "--line-height-heading": "1.25",
    "--radius-student": "16px",
    "--radius-staff": "8px",
    "--radius-pill": "999px",
    "--elevation-0": "none",
    "--elevation-1": "0 1px 2px rgba(31, 41, 55, .08), 0 1px 3px rgba(31, 41, 55, .12)",
    "--elevation-2": "0 4px 8px rgba(31, 41, 55, .12)",
    "--elevation-3": "0 12px 32px rgba(31, 41, 55, .24)",
    "--touch-min": "32px",
    "--touch-student": "44px",
    # Story 1.6 Design Tokens — Dialog: "backdrop rgba(31,41,55,.5)" (the text colour at 50%).
    "--color-backdrop": "rgba(31, 41, 55, .5)",
}


def rule(selector: str) -> str:
    """Body of the first CSS rule whose selector is exactly `selector`."""
    match = re.search(re.escape(selector) + r"\s*\{(.*?)\}", TOKENS, re.S)
    assert match, f"no rule for {selector}"
    return " ".join(match.group(1).split())


def declarations(selector: str) -> dict[str, str]:
    return {
        name.strip(): value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", rule(selector))
    }


def relative_luminance(hex_colour: str) -> float:
    channels = [int(hex_colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(fg: str, bg: str) -> float:
    lighter, darker = sorted((relative_luminance(fg), relative_luminance(bg)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


# --- tokens.css --------------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "value"), SPEC_TOKENS.items())
def test_root_token_matches_the_approved_spec(name, value):
    assert declarations(":root")[name] == value


@pytest.mark.parametrize(
    ("theme", "expected"),
    [
        (
            ".theme-student",
            {
                "--font-size-base": "var(--font-size-base-student)",
                "--radius": "var(--radius-student)",
                "--bg": "var(--color-bg-student)",
                "--touch": "var(--touch-student)",
                "--icon-variant": "duotone",
            },
        ),
        (
            ".theme-staff",
            {
                "--font-size-base": "var(--font-size-base-staff)",
                "--radius": "var(--radius-staff)",
                "--bg": "var(--color-bg-staff)",
                "--touch": "var(--touch-min)",
                "--icon-variant": "regular",
            },
        ),
    ],
)
def test_theme_class_sets_the_role_dependent_tokens(theme, expected):
    assert declarations(theme) == expected


def test_body_uses_the_tokens_for_font_colour_background_and_line_height():
    body = rule("body")

    for fragment in (
        "font-family: var(--font-family)",
        "font-size: var(--font-size-base, 16px)",
        "color: var(--color-text)",
        "background: var(--bg, var(--color-surface))",
        "line-height: var(--line-height-body)",
    ):
        assert fragment in body


def test_headings_use_the_heading_line_height():
    assert "line-height: var(--line-height-heading)" in rule("h1, h2, h3")


def test_focus_visible_is_a_3px_focus_colour_outline_with_2px_offset():
    focus = rule(":focus-visible")

    assert "outline: 3px solid var(--color-focus)" in focus
    assert "outline-offset: 2px" in focus


def test_visually_hidden_utility_hides_visually_but_not_from_screen_readers():
    hidden = rule(".visually-hidden")

    assert "position: absolute" in hidden
    assert "clip-path: inset(50%)" in hidden
    assert "display: none" not in hidden


def test_reduced_motion_disables_animations_and_transitions():
    block = TOKENS.split("@media (prefers-reduced-motion: reduce)")[1]

    assert "animation: none !important" in block
    assert "transition: none !important" in block


def test_important_appears_only_in_the_reduced_motion_block():
    before, after = TOKENS.split("@media (prefers-reduced-motion: reduce)")

    assert "!important" not in before
    assert after.count("!important") == 2


@pytest.mark.parametrize(("weight", "file"), [(400, "Regular"), (600, "SemiBold"), (700, "Bold")])
def test_font_face_is_self_hosted_with_swap(weight, file):
    faces = [" ".join(face.split()) for face in re.findall(r"@font-face\s*\{(.*?)\}", TOKENS, re.S)]

    assert any(
        f"font-weight: {weight}" in face
        and "font-display: swap" in face
        and f"url('../fonts/AtkinsonHyperlegibleNext-{file}.woff2') format('woff2')" in face
        for face in faces
    )


# --- contrast (spec says every pair is WCAG AA) ------------------------------------------------


@pytest.mark.parametrize(
    ("fg", "bg", "minimum"),
    [
        ("--color-surface", "--color-primary", 4.5),  # primary button
        ("--color-surface", "--color-primary-hover", 4.5),
        ("--color-surface", "--color-error", 4.5),  # danger button
        ("--color-primary", "--color-surface", 4.5),  # secondary / link button
        ("--color-primary", "--color-bg-student", 4.5),
        ("--color-muted", "--color-disabled", 4.5),  # disabled button
        ("--color-text", "--color-accent", 4.5),
        ("--color-text", "--color-bg-student", 4.5),
        ("--color-text", "--color-bg-staff", 4.5),
        ("--color-border", "--color-surface", 3.0),  # UI component boundary
        ("--color-focus", "--color-surface", 3.0),  # focus ring
        ("--color-focus", "--color-bg-student", 3.0),
        ("--color-focus", "--color-bg-staff", 3.0),
        ("--pill-active-fg", "--pill-active-bg", 4.5),
        ("--pill-flagged-fg", "--pill-flagged-bg", 4.5),
        ("--pill-blocked-fg", "--pill-blocked-bg", 4.5),
        ("--pill-resubmitted-fg", "--pill-resubmitted-bg", 4.5),
        ("--pill-draft-fg", "--pill-draft-bg", 4.5),
        ("--pill-published-fg", "--pill-published-bg", 4.5),
    ],
)
def test_colour_pair_meets_wcag_aa(fg, bg, minimum):
    assert contrast(SPEC_TOKENS[fg], SPEC_TOKENS[bg]) >= minimum


# --- fonts and icons ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "AtkinsonHyperlegibleNext-Regular.woff2",
        "AtkinsonHyperlegibleNext-SemiBold.woff2",
        "AtkinsonHyperlegibleNext-Bold.woff2",
    ],
)
def test_font_file_is_a_committed_woff2(name):
    assert (STATIC / "fonts" / name).read_bytes()[:4] == b"wOF2"


def test_font_licence_is_shipped_alongside():
    assert "SIL OPEN FONT LICENSE" in (STATIC / "fonts/OFL.txt").read_text(encoding="utf-8")


def test_icon_licence_is_shipped_alongside():
    licence = (STATIC / "icons/LICENSE").read_text(encoding="utf-8")

    assert "MIT License" in licence
    assert "Phosphor Icons" in licence


def test_sprite_has_regular_and_duotone_symbols_for_exactly_the_icon_names():
    sprite = (STATIC / "icons/sprite.svg").read_text(encoding="utf-8")

    ids = set(re.findall(r'<symbol id="([\w-]+)" viewBox="0 0 256 256"', sprite))

    assert ids == set(ICON_NAMES) | {f"{name}-duotone" for name in ICON_NAMES}
    assert len(ICON_NAMES) == 25


def test_sprite_starts_with_a_comment_naming_version_and_icons():
    sprite = (STATIC / "icons/sprite.svg").read_text(encoding="utf-8")
    comment = sprite[: sprite.index("-->")]

    assert sprite.startswith("<!-- Phosphor Icons 2.1.1")
    assert all(name in comment for name in ICON_NAMES)


def test_duotone_layer_is_accent_filled_at_twenty_percent_via_a_class():
    sprite = (STATIC / "icons/sprite.svg").read_text(encoding="utf-8")
    duotones = re.findall(r'<symbol id="[\w-]+-duotone"[^>]*>(.*?)</symbol>', sprite, re.S)

    assert ".icon-duotone-layer { fill: var(--color-accent); opacity: 0.2; }" in sprite
    assert len(duotones) == 25
    assert all('class="icon-duotone-layer"' in body for body in duotones)
    assert sprite.count('fill="currentColor"') == 50


# --- component CSS -----------------------------------------------------------------------------


@pytest.mark.parametrize("atom", ATOMS)
def test_each_atom_has_its_own_stylesheet_built_only_on_tokens(atom):
    css = (STATIC / "css/components" / f"{atom}.css").read_text(encoding="utf-8")

    assert "var(--" in css
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not re.search(r"rgba?\(", css)
    assert "!important" not in css


def test_stylesheets_outside_tokens_never_use_raw_hex():
    sheets = [p for p in (STATIC / "css").rglob("*.css") if p.name != "tokens.css"]

    offenders = [str(p) for p in sheets if re.search(r"#[0-9a-fA-F]{3,8}\b", p.read_text())]

    assert offenders == []


def test_button_loading_state_shows_spinner_and_blocks_pointer():
    css = " ".join((STATIC / "css/components/button.css").read_text(encoding="utf-8").split())

    assert ".button.htmx-request { pointer-events: none; }" in css
    assert ".button.htmx-request .button__spinner { display: inline-block; }" in css
    assert "min-height: var(--touch, var(--touch-min))" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


# --- translations ------------------------------------------------------------------------------


def catalogue(language: str) -> dict[str, str]:
    text = (LOCALE / language / "LC_MESSAGES/django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, re.M))


def story_msgids() -> set[str]:
    templates = [
        *(WEB_DIR / "templates/components").glob("*.html"),
        *(WEB_DIR / "templates/styleguide").glob("*.html"),
    ]
    sources = [p.read_text(encoding="utf-8") for p in templates]
    python = [
        (WEB_DIR / "templatetags/ui.py").read_text(encoding="utf-8"),
        (WEB_DIR / "styleguide/views.py").read_text(encoding="utf-8"),
    ]
    ids = {m for s in sources for m in re.findall(r'{% translate "([^"]+)" %}', s)}
    ids |= {m for s in python for m in re.findall(r'_\("([^"]+)"\)', s)}
    ids |= {"Score: %(value)s out of 100", "%(done)s of %(total)s"}
    return ids


@pytest.mark.parametrize("language", ["ro", "en"])
def test_every_new_ui_string_is_in_the_catalogue(language):
    entries = catalogue(language)

    missing = sorted(i for i in story_msgids() if not entries.get(i))

    assert missing == []


@pytest.mark.parametrize(
    ("msgid", "romanian"),
    [
        ("Active", "Activ"),
        ("Flagged", "Semnalat"),
        ("Blocked", "Blocat"),
        ("Resubmitted", "Retrimis"),
        ("Draft", "Ciornă"),
        ("Published", "Publicat"),
        ("User", "Utilizator"),
        ("Score: %(value)s out of 100", "Punctaj: %(value)s din 100"),
        # Story 1.6 AC 14 (molecules)
        ("(required)", "(obligatoriu)"),
        ("Close", "Închide"),
        ("Unavailable", "Indisponibil"),
        ("Cancel", "Anulează"),
        ("Breadcrumb", "Fir de navigare"),
        ("Română", "Română"),
        ("English", "English"),
        (
            "JavaScript is required to confirm this action.",
            "Este necesar JavaScript pentru a confirma această acțiune.",
        ),
    ],
)
def test_romanian_translation_matches_the_story(msgid, romanian):
    assert catalogue("ro")[msgid] == romanian


def test_status_labels_are_the_six_canonical_states():
    expected = {"ACTIVE", "FLAGGED", "BLOCKED", "RESUBMITTED", "DRAFT", "PUBLISHED"}

    assert set(STATUS_LABELS) == expected
