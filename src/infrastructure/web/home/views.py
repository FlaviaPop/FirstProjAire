"""GET /<lang>/: the signed-in user's role home (Story 1.7)."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from infrastructure.web.common.decorators import require_authenticated
from infrastructure.web.home.navigation import HOME, available_sections

TEMPLATE_BY_ROLE = {
    "STUDENT": "home/student.html",
    "TEACHER": "home/teacher.html",
    "PARENT": "home/parent.html",
    "ADMIN": "home/admin.html",
}


@require_authenticated
def index(request: HttpRequest) -> HttpResponse:
    """Greeting + a card per available section; the role comes from the session only."""
    user = request.user
    role = getattr(user, "role", "")
    context = {
        "greeting_name": (getattr(user, "full_name", "") or "").split(" ")[0],
        "sections": [(e, url) for e, url in available_sections(user) if e is not HOME],
        "icon_variant": "duotone" if role == "STUDENT" else "regular",
    }
    return render(request, TEMPLATE_BY_ROLE[role], context)
