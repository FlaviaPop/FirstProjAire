"""AC 9 + review hand-offs: dialog keyboard behaviour, alert dismissal focus, focus not obscured."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e
TOP_BAR_HEIGHT = 64  # tokens.css --nav-height


def test_dialog_opens_traps_focus_and_returns_focus(page: Page, base_url, console_errors):
    page.goto(f"{base_url}/en/e2e/dialog/")  # anonymous: the test page only extends base.html
    trigger = page.get_by_role("button", name="Open")

    trigger.focus()
    page.keyboard.press("Enter")
    dialog = page.get_by_role("dialog", name="Confirm?")
    expect(dialog).to_be_visible()
    # A native modal <dialog> makes the rest of the page inert: Tab cycles through the dialog plus
    # one stop on the document itself (the browser UI in a real window), never page content.
    for _ in range(6):
        page.keyboard.press("Tab")
        assert page.evaluate(
            "document.activeElement.closest('dialog') !== null"
            " || document.activeElement === document.body"
        ), page.evaluate("document.activeElement.outerHTML.slice(0, 80)")
    page.keyboard.press("Escape")

    expect(dialog).to_be_hidden()
    expect(trigger).to_be_focused()


def test_dismissing_an_alert_keeps_focus_on_main(page: Page, base_url, console_errors):
    # Story 1.6 review v1 ISS-002.
    page.goto(f"{base_url}/en/e2e/dialog/")
    close = page.get_by_role("button", name="Close")

    close.focus()
    page.keyboard.press("Enter")

    expect(page.get_by_text("Saved", exact=True)).to_have_count(0)
    assert page.evaluate("document.activeElement.id") == "content"


def test_focus_is_never_hidden_under_the_sticky_top_bar(page: Page, base_url, console_errors):
    # Story 1.7 review v1 ISS-001 (WCAG 2.4.11).
    page.goto(f"{base_url}/en/e2e/dialog/")
    page.get_by_label("Field 40", exact=True).focus()  # bottom of a page taller than the viewport

    for _ in range(39):
        page.keyboard.press("Shift+Tab")

    field_1 = page.get_by_label("Field 1", exact=True)
    expect(field_1).to_be_focused()
    box = field_1.bounding_box()
    assert box is not None
    assert box["y"] >= TOP_BAR_HEIGHT, box
