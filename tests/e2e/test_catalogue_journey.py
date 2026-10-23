"""AC 10: grade 2 CLR/MEM/EN open; other subjects are unavailable, even by typing their URL."""

import pytest
from playwright.sync_api import Page, expect

from infrastructure.persistence.catalogue.models import SubjectModel
from tests.e2e.conftest import login
from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.e2e
ACTIVE = ["Communication in Romanian", "Mathematics and Environmental Exploration", "English"]


def test_student_catalogue_active_and_unavailable(page: Page, base_url, console_errors):
    StudentFactory(username="ana", preferred_language="en")
    login(page, base_url, "ana")

    page.get_by_role("navigation", name="Main").get_by_role("link", name="Learn").click()

    grade_2 = page.get_by_role("region", name="Grade 2")
    expect(grade_2.get_by_role("link")).to_have_count(len(ACTIVE))
    for subject in ACTIVE:
        expect(grade_2.get_by_role("link", name=subject)).to_be_visible()
    grade_5 = page.get_by_role("region", name="Grade 5")
    expect(grade_5.get_by_text("Mathematics", exact=True)).to_be_visible()
    expect(grade_5.get_by_role("link")).to_have_count(0)
    expect(grade_5.get_by_text("Unavailable").first).to_be_visible()

    inactive = SubjectModel.objects.filter(is_active=False, grade__code="5", code="MAT").get()
    response = page.goto(f"{base_url}/en/subjects/{inactive.pk}/")
    assert response is not None
    assert response.status == 404
    expect(page.get_by_role("heading", name="Page not found")).to_be_visible()

    page.goto(f"{base_url}/en/catalogue/")
    page.get_by_role("region", name="Grade 2").get_by_role(
        "link", name="Mathematics and Environmental Exploration"
    ).click()
    expect(page.get_by_role("heading", level=1)).to_have_text(
        "Mathematics and Environmental Exploration"
    )
    expect(page.get_by_text("No chapters are published yet.")).to_be_visible()
