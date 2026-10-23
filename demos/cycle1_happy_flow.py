"""CYCLE-1 happy-flow demo: accounts -> sign-in per role -> language -> catalogue -> subject page.

    uv run python demos/cycle1_happy_flow.py            # visible browser, demo pace
    uv run python demos/cycle1_happy_flow.py --slowmo 900 --pause 2500   # slower, for presenting

Starts a dev server on a throwaway database in a temporary directory (your data/ is never
touched), creates the demo admin, plays the flow in Chromium and stops everything afterwards.
`run()` is also exercised headless by tests/e2e/test_demos.py, so the demo can't silently rot.
"""

import argparse
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
ADMIN_USERNAME = "admin"
DEMO_PASSWORD = "Demo-Pass-2026!"  # noqa: S105 — throwaway local demo database only
LABELS = {
    "en": ("Username", "Password", "Sign in"),
    "ro": ("Nume de utilizator", "Parolă", "Autentificare"),
}
ACCOUNT_MENU = re.compile("Account menu|Meniul contului")
SIGN_OUT = re.compile("Sign out|Deconectare")
PEOPLE = (
    ("ana", "Ana Pop", "Student"),
    ("ion", "Ion Ionescu", "Teacher"),
    ("maria", "Maria Pop", "Parent/Guardian"),
)


class Demo:
    """The happy flow on one page; `pause_ms` slows it down for an audience (0 in tests)."""

    def __init__(self, page: Page, base_url: str, admin_password: str, pause_ms: int) -> None:
        self.page = page
        self.base = base_url
        self.admin_password = admin_password
        self.pause_ms = pause_ms

    def step(self, text: str) -> None:
        print(f"▶ {text}", flush=True)
        self.hold()

    def hold(self) -> None:
        """Keep the current screen up long enough for the audience to read it."""
        self.page.wait_for_timeout(self.pause_ms)

    def sign_in(self, username: str, password: str, lang: str) -> None:
        user_label, password_label, button = LABELS[lang]
        self.page.goto(f"{self.base}/{lang}/accounts/login/")
        self.page.get_by_label(user_label).fill(username)
        self.page.get_by_label(password_label).fill(password)
        self.page.get_by_role("button", name=button).click()

    def sign_out(self) -> None:
        button = self.page.get_by_role("button", name=SIGN_OUT)
        if not button.is_visible():  # a second click would close the <details> menu
            self.page.get_by_label(ACCOUNT_MENU).click()
        button.click()

    def create_account(self, username: str, full_name: str, role: str) -> None:
        self.page.goto(f"{self.base}/en/admin/accounts/usermodel/add/")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Full name").fill(full_name)
        self.page.get_by_label("Date of birth").fill("2018-03-02")
        self.page.get_by_label("Role").select_option(label=role)
        self.page.get_by_label(re.compile(r"^Password:?$")).fill(DEMO_PASSWORD)
        self.page.get_by_label("Password confirmation").fill(DEMO_PASSWORD)
        self.page.get_by_role("button", name="Save", exact=True).click()
        expect(self.page.get_by_text("was added successfully")).to_be_visible()

    def admin_sets_up_accounts(self) -> None:
        self.step("1. Admin signs in")
        self.sign_in(ADMIN_USERNAME, self.admin_password, "en")
        expect(
            self.page.get_by_role("link", name=re.compile("^(Accounts|Conturi)$")).first
        ).to_be_visible()
        for username, full_name, role in PEOPLE:
            self.step(f"   Admin creates {role}: {full_name}")
            self.create_account(username, full_name, role)
        self.step("   Admin links Maria (parent) to Ana (student)")
        self.page.goto(f"{self.base}/en/admin/accounts/parentchildlinkmodel/add/")
        self.page.get_by_label("Parent/Guardian").select_option(label="maria")
        self.page.get_by_label("Student").select_option(label="ana")
        self.page.get_by_role("button", name="Save", exact=True).click()
        expect(self.page.get_by_text("was added successfully")).to_be_visible()
        self.step("   Admin checks the audit log")
        self.page.goto(f"{self.base}/en/admin/audit/auditlogmodel/")
        created = self.page.get_by_role("cell", name="accounts.created", exact=True)
        expect(created).to_have_count(len(PEOPLE))
        self.hold()
        self.page.goto(f"{self.base}/en/")
        self.sign_out()

    def student_explores(self) -> None:
        self.step("2. Student Ana signs in (Romanian)")
        self.sign_in("ana", DEMO_PASSWORD, "ro")
        expect(self.page.get_by_role("heading", level=1)).to_have_text("Bună, Ana!")
        self.step("   Ana switches to English")
        self.page.get_by_role("button", name="EN").click()
        expect(self.page.get_by_role("heading", level=1)).to_have_text("Hello, Ana!")
        self.step("   Ana opens Learn: the K-8 catalogue")
        self.page.get_by_role("navigation", name="Main").get_by_role("link", name="Learn").click()
        grade_2 = self.page.get_by_role("region", name="Grade 2")
        grade_2.scroll_into_view_if_needed()
        expect(grade_2.get_by_role("link")).to_have_count(3)
        self.step("   Grade 2 (Pilot): three subjects open")
        self.page.get_by_role("region", name="Grade 5").scroll_into_view_if_needed()
        self.step("   Other grades: Unavailable")
        self.step("   Ana opens Mathematics and Environmental Exploration")
        subject = "Mathematics and Environmental Exploration"
        self.page.get_by_role("region", name="Grade 2").get_by_role("link", name=subject).click()
        expect(self.page.get_by_role("heading", level=1)).to_have_text(subject)
        self.step("   Ana signs out and back in: lands in English")
        self.sign_out()
        self.sign_in("ana", DEMO_PASSWORD, "ro")
        expect(self.page).to_have_url(f"{self.base}/en/")
        self.hold()
        self.sign_out()

    def staff_sign_in(self) -> None:
        for username, full_name, role in PEOPLE[1:]:
            self.step(f"3. {role} {full_name} signs in and sees their home")
            self.sign_in(username, DEMO_PASSWORD, "ro")
            self.page.get_by_label(ACCOUNT_MENU).click()
            expect(self.page.get_by_text(full_name, exact=True)).to_be_visible()
            self.hold()
            if role == "Teacher":
                self.step("   The teacher views the catalogue (read-only)")
                self.page.goto(f"{self.base}/ro/catalogue/")
                self.page.get_by_role("region", name="Clasa a II-a").scroll_into_view_if_needed()
                self.hold()
            self.sign_out()


def run(page: Page, base_url: str, admin_password: str = DEMO_PASSWORD, pause_ms: int = 0) -> None:
    """Play the whole CYCLE-1 happy flow; expects an admin `admin` and the seeded catalogue."""
    demo = Demo(page, base_url, admin_password, pause_ms)
    demo.admin_sets_up_accounts()
    demo.student_explores()
    demo.staff_sign_in()
    demo.step("Done: accounts -> sign-in per role -> language -> catalogue -> subject -> sign out")


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _manage(env: dict[str, str], *args: str) -> None:
    subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [sys.executable, "manage.py", *args],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_until_up(url: str, seconds: float = 20) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/healthz", timeout=1):  # noqa: S310 — local http
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"The demo server did not start at {url}")


@contextmanager
def demo_server() -> Iterator[str]:
    """A dev server on a fresh database in a temporary directory, with the demo admin."""
    with tempfile.TemporaryDirectory(prefix="learnplat-demo-") as tmp:
        env = os.environ | {
            "DJANGO_SETTINGS_MODULE": "config.settings.dev",
            "DATABASE_PATH": str(Path(tmp) / "demo.sqlite3"),
            "DJANGO_SUPERUSER_PASSWORD": DEMO_PASSWORD,
        }
        _manage(env, "migrate")
        _manage(
            env,
            "createsuperuser",
            "--noinput",
            "--username",
            ADMIN_USERNAME,
            "--full_name",
            "Admin Demo",
            "--date_of_birth",
            "1980-01-01",
        )
        url = f"http://127.0.0.1:{_free_port()}"
        server = subprocess.Popen(  # noqa: S603 — fixed interpreter and arguments
            [sys.executable, "manage.py", "runserver", url.removeprefix("http://"), "--noreload"],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            _wait_until_up(url)
            yield url
        finally:
            server.terminate()
            server.wait(timeout=10)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--slowmo", type=int, default=450, help="ms between browser actions")
    parser.add_argument("--pause", type=int, default=1500, help="ms to hold each step")
    parser.add_argument("--headless", action="store_true", help="no visible browser window")
    options = parser.parse_args(argv)
    with demo_server() as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=options.headless, slow_mo=options.slowmo)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        run(page, url, pause_ms=options.pause)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
