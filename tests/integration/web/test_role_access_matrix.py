# Seeded by Story 1.0; Stories 1.3, 1.7 and 2.2 add rows.
import pytest
from django.urls import reverse

from infrastructure.web.common.decorators import PUBLIC_URL_NAMES

pytestmark = pytest.mark.django_db
# Story 1.2: public routes that only accept POST (GET -> 405 by design).
POST_ONLY_PUBLIC_URL_NAMES = frozenset({"accounts:logout"})


@pytest.mark.parametrize("url_name", sorted(PUBLIC_URL_NAMES - POST_ONLY_PUBLIC_URL_NAMES))
def test_public_routes_are_reachable_anonymously(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200


# --- Story 1.2: POST-only public routes ---
@pytest.mark.parametrize("url_name", sorted(POST_ONLY_PUBLIC_URL_NAMES))
def test_post_only_public_routes_accept_anonymous_post(client, url_name):
    assert client.get(reverse(url_name)).status_code == 405
    assert client.post(reverse(url_name)).status_code == 302
