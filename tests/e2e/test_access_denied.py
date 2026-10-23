"""AC 7: non-admins get "Access denied" in the admin area; anonymous visitors must sign in."""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login
from tests.factories.accounts import ParentFactory, StudentFactory, TeacherFactory

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize(
    "factory", [StudentFactory, TeacherFactory, ParentFactory], ids=["student", "teacher", "parent"]
)
def test_non_admins_see_access_denied_in_the_admin_area(
    page: Page, base_url, console_errors, factory
):
    factory(username="e2e", preferred_language="ro")
    login(page, base_url, "e2e", lang="ro")

    response = page.goto(f"{base_url}/ro/admin/")

    assert response is not None
    assert response.status == 403
    expect(page.get_by_role("heading", name="Acces interzis")).to_be_visible()


def test_anonymous_home_redirects_to_sign_in(page: Page, base_url, console_errors):
    page.goto(f"{base_url}/ro/")

    expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/ro/accounts/login/\?next=/ro/"))
    expect(page.get_by_role("heading", name="Autentificare")).to_be_visible()
