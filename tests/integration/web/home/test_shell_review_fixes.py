"""Story 1.7 review v1: sticky-bar offset (ISS-001), greeting (ISS-002), empty nav (ISS-003)."""

import re
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders

from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db


def test_scroll_padding_clears_the_sticky_top_bar():
    # WCAG 2.4.11: scrolling to a focused control or #target must not hide it under the bar.
    css = Path(finders.find("css/layout.css")).read_text(encoding="utf-8")

    assert "position: sticky" in css
    assert re.search(r"html\s*\{[^}]*scroll-padding-top:\s*calc\(var\(--nav-height\)", css)


@pytest.mark.parametrize("name", ["  Ana Pop", "Ana\tPop", "Ana  Pop", " Ana"])
def test_greeting_ignores_surrounding_whitespace(client, name):
    client.force_login(UserFactory(role="STUDENT", full_name=name))

    assert "Hello, Ana!" in client.get("/en/").content.decode()


def test_no_empty_navigation_landmark_for_a_corrupt_role(client):
    client.force_login(UserFactory(role="WIZARD"))

    html = client.get("/en/").content.decode()

    assert 'class="main-nav"' not in html
    assert 'class="top-bar"' in html
