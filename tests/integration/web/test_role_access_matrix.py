# Seeded by Story 1.0; Stories 1.3, 1.7 and 2.2 add rows.
import pytest
from django.urls import reverse

from infrastructure.web.common.decorators import PUBLIC_URL_NAMES

pytestmark = pytest.mark.django_db
# Story 1.2: public routes that only accept POST (GET -> 405 by design).
POST_ONLY_PUBLIC_URL_NAMES = frozenset({"accounts:logout", "set_language"})  # + Story 1.4


@pytest.mark.parametrize("url_name", sorted(PUBLIC_URL_NAMES - POST_ONLY_PUBLIC_URL_NAMES))
def test_public_routes_are_reachable_anonymously(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200


# --- Story 1.2: POST-only public routes ---
@pytest.mark.parametrize("url_name", sorted(POST_ONLY_PUBLIC_URL_NAMES))
def test_post_only_public_routes_accept_anonymous_post(client, url_name):
    assert client.get(reverse(url_name)).status_code == 405
    assert client.post(reverse(url_name)).status_code == 302


# --- Story 1.3: role-by-route harness (patterns §12.4) --------------------------------------
# Role clients come from tests/conftest.py (Story 1.2 fixtures).
CLIENT_FOR_ROLE = {
    "anonymous": "client",
    "Student": "student_client",
    "Teacher": "teacher_client",
    "Parent/Guardian": "parent_client",
    "Admin": "admin_client",
}
# (role, path, expected_status) — append one block per story, grouped by route.
ROWS = [(role, "/healthz", 200) for role in CLIENT_FOR_ROLE]
# Story 1.7 — home
ROWS += [("anonymous", "/ro/", 302)] + [
    (role, "/ro/", 200) for role in ("Student", "Teacher", "Parent/Guardian", "Admin")
]


@pytest.mark.parametrize(("role", "path", "expected"), ROWS)
def test_role_access_matrix(request, role, path, expected):
    client = request.getfixturevalue(CLIENT_FOR_ROLE[role])

    assert client.get(path).status_code == expected
