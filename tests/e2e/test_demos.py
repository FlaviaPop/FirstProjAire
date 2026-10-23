"""The presenter demos in demos/ keep working: each runs headless against the live server."""

import pytest
from playwright.sync_api import Page

from demos import cycle1_happy_flow
from tests.e2e.conftest import PASSWORD
from tests.factories.accounts import AdminFactory

pytestmark = pytest.mark.e2e


def test_cycle1_happy_flow_demo(page: Page, base_url, console_errors):
    AdminFactory(username=cycle1_happy_flow.ADMIN_USERNAME, full_name="Admin Demo")

    cycle1_happy_flow.run(page, base_url, admin_password=PASSWORD)
