"""Story 1.9 review v1 ISS-002: the lockout list never shows what was typed for a non-account.

Same rule as the audit log (owner decision 2): an existing account is shown by its username;
anything else as "(unknown):<fingerprint>", because people sometimes type a password there.
"""

import pytest
from axes.models import AccessAttempt

from infrastructure.persistence.audit.fingerprint import username_fingerprint
from tests.factories.accounts import StudentFactory
from tests.integration.web.admin.admin_helpers import ATTEMPTS

pytestmark = pytest.mark.django_db
TYPED_SECRET = "MyS3cret-Passw0rd"


def _attempt(username: str) -> AccessAttempt:
    return AccessAttempt.objects.create(
        username=username,
        ip_address="10.0.0.9",
        user_agent="",
        http_accept="",
        path_info="/ro/accounts/login/",
        get_data="",
        post_data="",
        failures_since_start=5,
    )


def test_lockout_list_masks_text_typed_for_a_non_existent_account(admin_client):
    _attempt(TYPED_SECRET)

    html = admin_client.get(ATTEMPTS).content.decode()

    assert TYPED_SECRET not in html
    assert f"(unknown):{username_fingerprint(TYPED_SECRET)}" in html


def test_lockout_detail_masks_text_typed_for_a_non_existent_account(admin_client):
    attempt = _attempt(TYPED_SECRET)

    html = admin_client.get(f"{ATTEMPTS}{attempt.pk}/change/").content.decode()

    assert TYPED_SECRET not in html
    assert f"(unknown):{username_fingerprint(TYPED_SECRET)}" in html


def test_lockout_list_shows_a_real_account_by_its_username(admin_client):
    StudentFactory(username="ana")
    _attempt("ana")

    html = admin_client.get(ATTEMPTS).content.decode()

    assert ">ana<" in html


def test_search_still_finds_a_known_username(admin_client):
    StudentFactory(username="ana")
    _attempt("ana")
    _attempt("bogdan")

    html = admin_client.get(ATTEMPTS, {"q": "ana"}).content.decode()

    assert ">ana<" in html
    assert username_fingerprint("bogdan") not in html


def test_unlocking_a_masked_attempt_still_works(admin_client):
    attempt = _attempt(TYPED_SECRET)

    response = admin_client.post(f"{ATTEMPTS}{attempt.pk}/delete/", {"post": "yes"})

    assert response.status_code == 302
    assert not AccessAttempt.objects.exists()
