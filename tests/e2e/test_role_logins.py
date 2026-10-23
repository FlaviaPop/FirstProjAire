"""AC 4: every role signs in, lands on its language home with its theme and menu, signs out."""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login, logout
from tests.factories.accounts import AdminFactory, ParentFactory, StudentFactory, TeacherFactory

pytestmark = pytest.mark.e2e
CASES = [
    (StudentFactory, "theme-student", ["Home", "Learn"]),
    (TeacherFactory, "theme-staff", ["Home"]),
    (ParentFactory, "theme-staff", ["Home"]),
    (AdminFactory, "theme-staff", ["Home", "Accounts"]),
]


@pytest.mark.parametrize(
    ("factory", "theme", "menu"), CASES, ids=["student", "teacher", "parent", "admin"]
)
def test_role_login_home_and_logout(page: Page, base_url, console_errors, factory, theme, menu):
    user = factory(username="e2e", full_name="Ana Pop", preferred_language="en")

    login(page, base_url, "e2e")

    expect(page).to_have_url(f"{base_url}/en/")
    expect(page.locator("body")).to_have_class(re.compile(rf"\b{theme}\b"))
    nav = page.get_by_role("navigation", name="Main")
    expect(nav.get_by_role("link")).to_have_text(menu)
    expect(page.get_by_role("heading", level=1)).to_have_text("Hello, Ana!")
    page.get_by_label("Account menu").click()
    expect(page.get_by_text(user.full_name, exact=True)).to_be_visible()
    logout(page)
    expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/en/accounts/login/"))
