"""DEBUG-only /_styleguide/ page (Story 1.5)."""

import importlib
import re
from collections.abc import Iterator

import pytest
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.test import Client, override_settings
from django.urls import NoReverseMatch, clear_url_caches, include, path, reverse
from django.utils import translation

import config.urls
from infrastructure.web.styleguide.views import SWATCHES
from infrastructure.web.templatetags.ui import ICON_NAMES

urlpatterns = i18n_patterns(path("_styleguide/", include("infrastructure.web.styleguide.urls")))

TOKENS = (settings.BASE_DIR / "src/infrastructure/web/static/css/tokens.css").read_text("utf-8")


@pytest.fixture(autouse=True)
def locale_middleware(settings):
    """Language activation from the URL prefix belongs to Story 1.4 (LocaleMiddleware, placed
    right after SessionMiddleware per Story 1.2). Installed here so /en/ resolves as it will
    once that story is merged; the base settings are not edited by this story."""
    middleware = list(settings.MIDDLEWARE)
    if "django.middleware.locale.LocaleMiddleware" not in middleware:
        position = middleware.index("django.contrib.sessions.middleware.SessionMiddleware") + 1
        middleware.insert(position, "django.middleware.locale.LocaleMiddleware")
    settings.MIDDLEWARE = middleware


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


@pytest.mark.urls(__name__)
def test_styleguide_shows_every_variant_twice(client):
    html = client.get("/en/_styleguide/").content.decode()

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
    first = client.get("/en/_styleguide/").content

    assert client.get("/en/_styleguide/").content == first


@pytest.mark.urls(__name__)
def test_styleguide_makes_no_database_queries(client):
    """No `db` fixture: pytest-django raises RuntimeError on any database access."""
    response = client.get("/en/_styleguide/")

    assert response.status_code == 200


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
