"""BUG-004 (docs/testing/bug-triage-2026-10-23.md): lockouts and audit rows use the real client IP.

Behind Nginx every request comes from the proxy (REMOTE_ADDR) and the client is in
X-Forwarded-For, which Nginx OVERWRITES with one value (`X-Forwarded-For $remote_addr`,
PR #1 nginx/conf.d/proxy_headers.inc). These tests send exactly that header shape.
"""

import pytest
from axes.models import AccessAttempt

from config.settings.base import PROXIED_IP_HEADERS
from infrastructure.persistence.audit.models import AuditLogModel
from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db
LOGIN = "/en/accounts/login/"
PASSWORD = "pilot-pass-123"
PROXY = "127.0.0.1"
ATTACKER = "203.0.113.10"
STUDENT = "198.51.100.20"


@pytest.fixture
def behind_nginx(settings):
    """The prod values (prod.py): read X-Forwarded-For, which Nginx overwrites with one address."""
    settings.AXES_IPWARE_META_PRECEDENCE_ORDER = PROXIED_IP_HEADERS
    settings.AXES_IPWARE_PROXY_COUNT = 0


def _sign_in(client, client_ip, password=PASSWORD):
    return client.post(
        LOGIN,
        {"username": "ana", "password": password},
        REMOTE_ADDR=PROXY,
        HTTP_X_FORWARDED_FOR=client_ip,
    )


def _lock_out_from(client, client_ip):
    return [_sign_in(client, client_ip, "wrong-pass-1").status_code for _ in range(5)]


def test_axes_can_resolve_proxied_clients():
    from axes.helpers import IPWARE_INSTALLED

    # Without django-ipware, axes silently falls back to REMOTE_ADDR (the proxy).
    assert IPWARE_INSTALLED is True


def test_behind_nginx_a_lockout_only_blocks_the_attacking_client(client, behind_nginx):
    StudentFactory(username="ana", preferred_language="en")

    assert _lock_out_from(client, ATTACKER)[-1] == 429
    response = _sign_in(client, STUDENT)

    assert response.status_code == 302
    assert response["Location"] == "/en/"


def test_behind_nginx_the_attacker_stays_locked_out(client, behind_nginx):
    StudentFactory(username="ana", preferred_language="en")
    _lock_out_from(client, ATTACKER)

    assert _sign_in(client, ATTACKER).status_code == 429


def test_behind_nginx_attempts_and_audit_rows_record_the_real_client(client, behind_nginx):
    StudentFactory(username="ana", preferred_language="en")

    _lock_out_from(client, ATTACKER)
    _sign_in(client, STUDENT)

    assert list(AccessAttempt.objects.values_list("ip_address", flat=True)) == [ATTACKER]
    rows = set(AuditLogModel.objects.values_list("action", "ip_address"))
    assert rows == {
        ("auth.login_failed", ATTACKER),
        ("auth.lockout", ATTACKER),
        ("auth.login", STUDENT),
    }


def test_without_the_proxy_a_forged_forwarded_for_is_ignored(client):
    StudentFactory(username="ana")

    _sign_in(client, ATTACKER, "wrong-pass-1")

    assert AccessAttempt.objects.get().ip_address == PROXY


def test_proxy_count_one_cannot_read_the_single_value_nginx_header(client, behind_nginx, settings):
    # Why AXES_PROXY_COUNT must be 0 with Nginx's overwrite-style header: ipware's proxy count
    # counts proxies listed INSIDE X-Forwarded-For, and there are none, so 1 yields no address.
    settings.AXES_IPWARE_PROXY_COUNT = 1
    StudentFactory(username="ana")

    _sign_in(client, ATTACKER, "wrong-pass-1")

    assert AccessAttempt.objects.get().ip_address is None
