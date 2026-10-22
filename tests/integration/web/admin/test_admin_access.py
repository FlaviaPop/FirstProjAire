"""Story 1.9 AC 1, 2, 14: only an active Admin enters the admin area (RBAC Enforcement table)."""

from urllib.parse import quote

import pytest
from django.urls import reverse

from infrastructure.persistence.accounts.admin import PlatformAdminSite, platform_admin_site
from tests.factories.accounts import AdminFactory, UserFactory

pytestmark = pytest.mark.django_db

# Index, user list, link add, audit list (QA-observable) plus every other registered screen.
ADMIN_URLS = [
    "/ro/admin/",
    "/ro/admin/accounts/usermodel/",
    "/ro/admin/accounts/usermodel/add/",
    "/ro/admin/accounts/parentchildlinkmodel/",
    "/ro/admin/accounts/parentchildlinkmodel/add/",
    "/ro/admin/axes/accessattempt/",
    "/ro/admin/audit/auditlogmodel/",
    "/ro/admin/password_change/",
    "/ro/admin/jsi18n/",
    "/ro/admin/accounts/",
    "/en/admin/",
]
DENIED_CLIENTS = ["student_client", "teacher_client", "parent_client"]


# --- AC 14: role-access rows for /ro/admin/ ---------------------------------------------------
@pytest.mark.parametrize(
    ("fixture", "status"),
    [
        ("client", 302),
        ("student_client", 403),
        ("teacher_client", 403),
        ("parent_client", 403),
        ("admin_client", 200),
    ],
)
def test_only_admin_role_enters_admin(request, fixture, status):
    assert request.getfixturevalue(fixture).get("/ro/admin/").status_code == status


@pytest.mark.parametrize("fixture", DENIED_CLIENTS)
@pytest.mark.parametrize("url", [*ADMIN_URLS, "/ro/admin/login/", "/ro/admin/no-such-page/"])
def test_non_admin_roles_get_the_platform_403_everywhere(request, fixture, url):
    response = request.getfixturevalue(fixture).get(url)

    assert response.status_code == 403
    templates = [t.name for t in response.templates]
    assert "errors/403.html" in templates
    assert "admin/login.html" not in templates  # never a second sign-in form


@pytest.mark.parametrize("fixture", DENIED_CLIENTS)
def test_non_admin_post_is_refused_and_creates_nothing(request, fixture):
    from infrastructure.persistence.accounts.models import UserModel

    client = request.getfixturevalue(fixture)
    before = UserModel.objects.count()

    response = client.post("/ro/admin/accounts/usermodel/add/", {"username": "intruder"})

    assert response.status_code == 403
    assert UserModel.objects.count() == before


@pytest.mark.parametrize("url", [*ADMIN_URLS, "/ro/admin/login/"])
def test_anonymous_goes_to_platform_login_with_next(client, url):
    response = client.get(url)

    lang = url.split("/")[1]
    assert response.status_code == 302
    assert response["Location"] == f"/{lang}/accounts/login/?next={quote(url)}"


def test_anonymous_index_redirect_matches_the_system_responses_table(client):
    assert client.get("/ro/admin/")["Location"] == "/ro/accounts/login/?next=/ro/admin/"


@pytest.mark.parametrize("url", ADMIN_URLS)
def test_admin_reaches_every_admin_screen(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_signed_in_admin_opening_the_admin_login_goes_to_the_index(admin_client):
    response = admin_client.get("/ro/admin/login/")

    assert response.status_code == 302
    assert response["Location"] == "/ro/admin/"


def test_demoted_admin_loses_access_on_the_next_request(admin_client, admin_user):
    AdminFactory(username="other-admin")
    assert admin_client.get("/ro/admin/").status_code == 200

    admin_user.role = "TEACHER"
    admin_user.save()

    assert admin_client.get("/ro/admin/").status_code == 403


def test_promoted_teacher_gains_access_on_the_next_request(teacher_client, teacher):
    assert teacher_client.get("/ro/admin/").status_code == 403

    teacher.role = "ADMIN"
    teacher.save()

    assert teacher_client.get("/ro/admin/").status_code == 200


def test_deactivated_admin_is_treated_as_signed_out(admin_client, admin_user):
    admin_user.is_active = False
    admin_user.save()

    response = admin_client.get("/ro/admin/")

    assert response.status_code == 302
    assert response["Location"].startswith("/ro/accounts/login/")


def test_corrupt_role_with_forced_staff_flags_is_still_denied(client):
    # Even a row whose flags were set behind the ORM's back: the site checks the role itself.
    user = UserFactory(role="SUPERHERO")
    type(user).objects.filter(pk=user.pk).update(is_staff=True, is_superuser=True)
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")

    assert client.get("/ro/admin/").status_code == 403


def test_has_permission_requires_active_admin_role(rf, admin_user, teacher):
    site = PlatformAdminSite(name="probe")
    request = rf.get("/")

    request.user = admin_user
    assert site.has_permission(request) is True
    request.user = teacher
    assert site.has_permission(request) is False
    admin_user.is_active = False
    request.user = admin_user
    assert site.has_permission(request) is False


def test_site_is_named_admin_and_routed_inside_the_language_prefix():
    assert platform_admin_site.name == "admin"
    assert reverse("admin:index") == "/ro/admin/"


@pytest.mark.parametrize(
    ("url", "header", "index_title"),
    [
        ("/en/admin/", "Learning Platform administration", "Accounts and links"),
        ("/ro/admin/", "Administrarea platformei de învățare", "Conturi și legături"),
    ],
)
def test_branding_is_translated(admin_client, url, header, index_title):
    content = admin_client.get(url).content.decode()

    assert header in content
    assert index_title in content
