"""AC 3: the admin creates a student, a teacher and a parent, links them, sees the audit trail."""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import login
from tests.factories.accounts import AdminFactory

pytestmark = pytest.mark.e2e
NEW_PASSWORD = "Pilot-Journey-2026!"
ACCOUNTS = [
    ("e2e-student", "Ana Elev", "Student"),
    ("e2e-teacher", "Ion Profesor", "Teacher"),
    ("e2e-parent", "Maria Parinte", "Parent/Guardian"),
]


def _create_account(page: Page, base_url: str, username: str, full_name: str, role: str) -> None:
    page.goto(f"{base_url}/en/admin/accounts/usermodel/add/")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Full name").fill(full_name)
    page.get_by_label("Date of birth").fill("2018-03-02")
    page.get_by_label("Role").select_option(label=role)
    # Admin labels end with ":"; "Password" alone would also match "Password confirmation:".
    page.get_by_label(re.compile(r"^Password:?$")).fill(NEW_PASSWORD)
    page.get_by_label("Password confirmation").fill(NEW_PASSWORD)
    page.get_by_role("button", name="Save", exact=True).click()
    expect(page.get_by_text("was added successfully")).to_be_visible()


def _link(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/en/admin/accounts/parentchildlinkmodel/add/")
    page.get_by_label("Parent/Guardian").select_option(label="e2e-parent")
    page.get_by_label("Student").select_option(label="e2e-student")
    page.get_by_role("button", name="Save", exact=True).click()


def test_admin_creates_accounts_links_parent_and_sees_audit(page: Page, base_url, console_errors):
    AdminFactory(username="boss", preferred_language="en")
    login(page, base_url, "boss")

    for username, full_name, role in ACCOUNTS:
        _create_account(page, base_url, username, full_name, role)
    _link(page, base_url)
    expect(page.get_by_text("was added successfully")).to_be_visible()
    _link(page, base_url)  # the same pair again
    expect(page.get_by_text("This parent is already linked to this student.")).to_be_visible()

    page.goto(f"{base_url}/en/admin/audit/auditlogmodel/")
    expect(page.get_by_role("cell", name="accounts.created", exact=True)).to_have_count(3)
    expect(page.get_by_role("cell", name="accounts.parent_linked", exact=True)).to_have_count(1)
