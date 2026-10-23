"""AC 6: five wrong passwords lock the account; the admin unlocks it; the student gets in."""

import pytest
from playwright.sync_api import Browser, Page, expect

from tests.e2e.conftest import assert_no_csp_violations, login, watch_console
from tests.factories.accounts import AdminFactory, StudentFactory

pytestmark = pytest.mark.e2e


def test_lockout_and_admin_unlock(page: Page, browser: Browser, base_url, console_errors):
    StudentFactory(username="ana", preferred_language="en")
    AdminFactory(username="boss", preferred_language="en")

    for _ in range(5):
        login(page, base_url, "ana", password="wrong-password-1")
    expect(page.get_by_role("heading", name="Too many attempts")).to_be_visible()
    login(page, base_url, "ana")  # the correct password is refused while locked
    expect(page.get_by_role("heading", name="Too many attempts")).to_be_visible()

    admin_context = browser.new_context()
    admin = admin_context.new_page()
    admin_errors = watch_console(admin)
    login(admin, base_url, "boss")
    admin.goto(f"{base_url}/en/admin/axes/accessattempt/")
    admin.get_by_role("checkbox", name="Select all objects on this page for an action").check()
    admin.get_by_label("Action:").select_option(label="Delete selected access attempts")
    admin.get_by_role("button", name="Go").click()
    admin.get_by_role("button", name="Yes, I\u2019m sure").click()  # Django admin text
    expect(admin.get_by_text("Successfully deleted 1 access attempt.")).to_be_visible()
    assert_no_csp_violations(admin_errors)
    admin_context.close()

    login(page, base_url, "ana")
    expect(page).to_have_url(f"{base_url}/en/")
