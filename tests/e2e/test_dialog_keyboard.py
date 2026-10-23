"""AC 9 + review hand-offs: dialog keyboard behaviour, alert dismissal focus, focus not obscured."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


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
    # Story 1.7 review v1 ISS-001 (WCAG 2.4.11): a field sitting under the sticky bar is scrolled
    # clear of it when keyboard focus reaches it. Only `scroll-padding-top` does that: without it
    # the field is already "in the viewport" and the browser leaves it under the bar (1.10 review
    # v1 ISS-001: walking up to the top of the page passed either way).
    page.goto(f"{base_url}/en/e2e/dialog/")
    bar = page.get_by_role("banner").bounding_box()
    assert bar is not None
    page.get_by_label("Field 21", exact=True).focus()
    page.evaluate(  # scroll so Field 20 sits inside the viewport but under the bar
        "window.scrollBy(0, document.getElementById('field-20').getBoundingClientRect().top - 10)"
    )
    field_20 = page.get_by_label("Field 20", exact=True)
    under_bar = field_20.bounding_box()
    assert under_bar is not None
    assert under_bar["y"] < bar["y"] + bar["height"], (under_bar, bar)  # precondition

    page.keyboard.press("Shift+Tab")

    expect(field_20).to_be_focused()
    box = field_20.bounding_box()
    assert box is not None
    assert box["y"] >= bar["y"] + bar["height"], (box, bar)
