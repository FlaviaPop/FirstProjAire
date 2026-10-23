"""AC 8: friendly 404 pages in Romanian and English, each with a way back home."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    ("path", "lang", "heading", "back"),
    [
        ("/ro/nu-exista/", "ro", "Pagina nu a fost găsită", "Înapoi la pagina principală"),
        ("/en/missing/", "en", "Page not found", "Back to home"),
    ],
    ids=["ro", "en"],
)
def test_not_found_page(page: Page, base_url, console_errors, path, lang, heading, back):
    response = page.goto(f"{base_url}{path}")

    assert response is not None
    assert response.status == 404
    expect(page.locator("html")).to_have_attribute("lang", lang)
    expect(page.get_by_role("heading", name=heading)).to_be_visible()
    expect(page.get_by_role("link", name=back)).to_be_visible()
