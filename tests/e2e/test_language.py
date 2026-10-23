"""AC 5: switching to English is remembered on the account across sign-out and sign-in."""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login, logout
from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.e2e


def test_switch_to_english_survives_sign_out_and_sign_in(page: Page, base_url, console_errors):
    StudentFactory(username="ana", full_name="Ana Pop", preferred_language="ro")
    login(page, base_url, "ana", lang="ro")
    expect(page).to_have_url(f"{base_url}/ro/")
    expect(page.locator("html")).to_have_attribute("lang", "ro")

    page.get_by_role("button", name="EN").click()

    expect(page).to_have_url(f"{base_url}/en/")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    logout(page)
    expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/en/accounts/login/"))
    login(page, base_url, "ana", lang="en")
    expect(page).to_have_url(f"{base_url}/en/")
