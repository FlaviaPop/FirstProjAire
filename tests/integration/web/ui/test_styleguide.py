"""DEBUG-only /_styleguide/ page (Story 1.5 atoms, Story 1.6 molecules)."""

import importlib
import re
from collections.abc import Iterator

import pytest
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.staticfiles import finders
from django.test import Client, override_settings
from django.urls import NoReverseMatch, clear_url_caches, include, path, reverse
from django.utils import translation

import config.urls
from infrastructure.web.styleguide.views import SWATCHES
from infrastructure.web.templatetags.ui import ICON_NAMES

urlpatterns = i18n_patterns(path("_styleguide/", include("infrastructure.web.styleguide.urls")))

TOKENS = (settings.BASE_DIR / "src/infrastructure/web/static/css/tokens.css").read_text("utf-8")


@pytest.fixture
def debug_urlconf() -> Iterator[None]:
    """Re-import the real root URLConf with DEBUG=True, then restore the production routing."""
    try:
        with override_settings(DEBUG=True):
            importlib.reload(config.urls)
            clear_url_caches()
            yield
    finally:
        importlib.reload(config.urls)
        clear_url_caches()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_styleguide_renders_all_atoms_in_both_themes(client, lang):
    html = client.get(f"/{lang}/_styleguide/").content.decode()

    assert html.count('class="theme-student"') == 1
    assert html.count('class="theme-staff"') == 1
    for marker in (
        "button--primary",
        "button--danger",
        "pill--blocked",
        "score__value",
        "<progress",
        "ș ț ă â î",
    ):
        assert marker in html


@pytest.mark.urls(__name__)
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_styleguide_language_follows_the_url_prefix(client, lang):
    html = client.get(f"/{lang}/_styleguide/").content.decode()

    assert f'<html lang="{lang}">' in html


def theme_sections(html: str) -> dict[str, str]:
    """The markup of each `.theme-<name>` section, keyed by theme name."""
    return dict(re.findall(r'<section class="theme-(\w+)".*?>(.*?)</section>', html, re.S))


def without_molecules(html: str) -> str:
    """The page minus the Story 1.6 molecule blocks, so the atom counts stay exact."""
    return re.sub(r'<div class="sg-molecules">.*?</section>', "</section>", html, flags=re.S)


@pytest.mark.urls(__name__)
def test_styleguide_shows_every_variant_twice(client):
    html = without_molecules(client.get("/en/_styleguide/").content.decode())

    for variant in ("primary", "secondary", "danger", "link"):
        assert html.count(f'class="button button--{variant}') == 2 * 3 * 2  # states x icon x theme
    assert html.count('aria-busy="true"') == 2 * 4 * 2
    for status in ("active", "flagged", "blocked", "resubmitted", "draft", "published"):
        assert html.count(f"pill--{status}") == 2
    for name in ICON_NAMES:
        for size in (20, 24, 32):
            assert html.count(f'width="{size}" height="{size}"') >= 2 * 25 * 2
        assert html.count(f"#{name}-duotone") >= 2 * 3
    for value in (1, 50, 100):
        assert html.count(f'aria-label="Score: {value} out of 100"') == 2
    for done, total in ((0, 0), (3, 8), (8, 8)):
        assert html.count(f'<span class="progress__text">{done}/{total}</span>') == 2
    assert html.count('class="avatar"') == 4
    assert html.count('class="badge"') == 4


@pytest.mark.urls(__name__)
def test_styleguide_shows_the_type_scale_sample_with_diacritics(client):
    html = client.get("/ro/_styleguide/").content.decode()

    assert "ș ț ă â î Ș Ț Ă Â Î — Matematică și explorarea mediului" in html


@pytest.mark.urls(__name__)
def test_styleguide_loads_only_same_origin_stylesheets(client):
    html = client.get("/en/_styleguide/").content.decode()

    hrefs = re.findall(r'(?:href|src)="([^"#]+)', html)

    assert "/static/css/tokens.css" in hrefs
    assert "/static/css/components/button.css" in hrefs
    assert all(h.startswith("/static/") for h in hrefs)


@pytest.mark.urls(__name__)
def test_styleguide_is_deterministic(client):
    """Identical apart from the CSRF token, which Django re-masks on every response (Story 1.6)."""

    def page() -> str:
        html = client.get("/en/_styleguide/").content.decode()
        return re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "CSRF", html)

    first = page()

    assert page() == first


@pytest.mark.urls(__name__)
def test_styleguide_makes_no_database_queries(client):
    """No `db` fixture: pytest-django raises RuntimeError on any database access."""
    response = client.get("/en/_styleguide/")

    assert response.status_code == 200


# --- Story 1.6: molecules ----------------------------------------------------------------------

MOLECULE_STYLESHEETS = (
    "form_field",
    "alert",
    "card",
    "disabled_tile",
    "empty_state",
    "page_header",
    "confirm_dialog",
    "table",
)
# marker -> occurrences inside ONE theme's molecule block
MOLECULE_MARKERS = {
    '<fieldset class="field-pair">': 2,  # clean pair + pair with errors
    'lang="ro" ': 2,
    'lang="en" ': 2,
    'class="field field--invalid"': 3,  # single field + both pair columns
    'aria-invalid="true"': 3,
    'class="field__help"': 2,
    'class="alert alert--info" role="status"': 1,
    'class="alert alert--success" role="status"': 1,
    'class="alert alert--warning" role="alert"': 1,
    'class="alert alert--error" role="alert"': 1,
    'class="alert__close" data-dismiss': 4,
    '<article class="card">': 1,
    '<article class="card card--link">': 1,
    'class="tile tile--disabled" aria-disabled="true"': 1,
    'class="empty-state"': 2,  # empty state sample + empty table
    "empty-state__action": 1,
    '<nav class="breadcrumb"': 1,
    'aria-current="page"': 1,
    'class="page-header__actions"': 1,
    "<dialog ": 1,
    "data-dialog-open=": 1,
    "data-dialog-close": 1,
    'name="csrfmiddlewaretoken"': 1,
    "<noscript>": 1,
    "<table": 1,  # the empty table renders its empty state instead
    "<caption": 1,
    'scope="col"': 4,
    "pill--active": 1,
    "pill--flagged": 1,
}


def molecule_blocks(html: str) -> dict[str, str]:
    return {
        theme: section.split('<div class="sg-molecules">', 1)[1]
        for theme, section in theme_sections(html).items()
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_styleguide_shows_every_molecule_in_both_themes(client, lang):
    blocks = molecule_blocks(client.get(f"/{lang}/_styleguide/").content.decode())

    assert set(blocks) == {"student", "staff"}
    for theme, block in blocks.items():
        for marker, count in MOLECULE_MARKERS.items():
            assert block.count(marker) == count, (theme, marker)


@pytest.mark.urls(__name__)
def test_molecules_follow_the_atoms_in_each_theme(client):
    sections = theme_sections(client.get("/en/_styleguide/").content.decode())
    index = (
        settings.BASE_DIR / "src/infrastructure/web/templates/styleguide/index.html"
    ).read_text()

    for section in sections.values():
        assert 0 < section.index('class="pill pill--draft"') < section.index('class="sg-molecules"')
    atoms_include = index.index('{% include "styleguide/_atoms.html" %}')
    assert atoms_include < index.index('{% include "styleguide/_molecules.html"')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize(
    ("lang", "words"),
    [
        (
            "ro",
            [
                "(obligatoriu)",
                'aria-label="Închide"',
                "Indisponibil",
                "Anulează",
                'aria-label="Fir de navigare"',
                "Română",
                "English",
                "Este necesar JavaScript pentru a confirma această acțiune.",
            ],
        ),
        (
            "en",
            [
                "(required)",
                'aria-label="Close"',
                "Unavailable",
                "Cancel",
                'aria-label="Breadcrumb"',
                "Română",
                "English",
                "JavaScript is required to confirm this action.",
            ],
        ),
    ],
)
def test_molecule_strings_follow_the_url_language(client, lang, words):
    html = client.get(f"/{lang}/_styleguide/").content.decode()

    for word in words:
        assert word in html, word


@pytest.mark.urls(__name__)
def test_styleguide_loads_ui_js_once_as_a_same_origin_module(client):
    html = client.get("/en/_styleguide/").content.decode()

    assert re.findall(r"<script\b[^>]*>", html) == ['<script type="module" src="/static/js/ui.js">']
    assert html.index('src="/static/js/ui.js"') < html.index("</head>")
    assert finders.find("js/ui.js")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize("name", MOLECULE_STYLESHEETS)
def test_styleguide_links_each_molecule_stylesheet(client, name):
    html = client.get("/en/_styleguide/").content.decode()

    assert f'<link rel="stylesheet" href="/static/css/components/{name}.css">' in html
    assert finders.find(f"css/components/{name}.css")


@pytest.mark.urls(__name__)
def test_molecule_ids_are_unique_and_every_reference_resolves(client):
    html = client.get("/en/_styleguide/").content.decode()
    blocks = molecule_blocks(html)
    page_ids = re.findall(r'\sid="([^"]+)"', html)

    molecule_ids = [i for block in blocks.values() for i in re.findall(r'\sid="([^"]+)"', block)]
    references = [
        ref
        for block in blocks.values()
        for attr in re.findall(
            r'(?:for|aria-labelledby|aria-describedby|data-dialog-open)="([^"]+)"', block
        )
        for ref in attr.split()
    ]

    assert molecule_ids
    assert len(molecule_ids) == len(set(molecule_ids))
    assert all(page_ids.count(i) == 1 for i in molecule_ids)
    assert references
    assert set(references) <= set(molecule_ids)


@pytest.mark.urls(__name__)
def test_dialog_ids_are_theme_suffixed(client):
    blocks = molecule_blocks(client.get("/en/_styleguide/").content.decode())

    for theme, block in blocks.items():
        assert f'<dialog id="sg-dialog-{theme}"' in block
        assert f'data-dialog-open="sg-dialog-{theme}"' in block


@pytest.mark.urls(__name__)
@pytest.mark.parametrize(("theme", "variant"), [("student", "duotone"), ("staff", "regular")])
def test_empty_states_use_the_theme_icon_variant(client, theme, variant):
    block = molecule_blocks(client.get("/en/_styleguide/").content.decode())[theme]

    symbols = re.findall(r'class="empty-state">\s*<svg[^>]*><use href="[^"#]+#([\w-]+)"', block)

    expected = "list-checks-duotone" if variant == "duotone" else "list-checks"
    assert symbols == [expected, expected]


def test_swatch_hex_values_match_tokens_css():
    for swatch in SWATCHES:
        assert re.search(rf"{re.escape(swatch.token)}:\s*{swatch.hex};", TOKENS), swatch.token


def test_styleguide_is_not_routed_when_debug_is_false():
    with pytest.raises(NoReverseMatch):
        reverse("styleguide:index")


@pytest.mark.parametrize("lang", ["ro", "en"])
def test_styleguide_returns_404_in_production(client, lang):
    assert client.get(f"/{lang}/_styleguide/").status_code == 404


@pytest.mark.usefixtures("debug_urlconf")
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_root_urlconf_registers_styleguide_when_debug_is_true(lang):
    with translation.override(lang):
        url = reverse("styleguide:index")

    response = Client().get(url)

    assert url == f"/{lang}/_styleguide/"
    assert response.status_code == 200
    assert reverse("healthz") == "/healthz"


def test_production_routing_is_restored_after_the_debug_reload(client):
    assert client.get("/ro/_styleguide/").status_code == 404
