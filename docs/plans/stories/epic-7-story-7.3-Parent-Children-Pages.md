### Story 7.3: Parent Children Pages

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 7 - Progress & Score Visibility | **ID**: 7.3 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-7-story-7.3-Parent-Children-Pages.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 2: Parent `/children/` and `/children/<id>/progress/`; unlinked child → 404)
**Wave**: 12
**Requires**: [7.1]
**Enables**: [7.5]
**Files Touched**:
  - src/infrastructure/web/progress/views/children.py
  - src/infrastructure/web/templates/progress/children/**
  - src/infrastructure/web/progress/urls.py
  - src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po
  - src/infrastructure/i18n/locale/en/LC_MESSAGES/django.po
  - tests/integration/web/test_role_access_matrix.py
  - docs/architecture/design/00-system-architecture-greenfield.md
  - tests/integration/web/progress/children/**
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — personas this story differentiates: Parent/Guardian, Student, Teacher, Admin
**QA Candidate**: Yes — **Observable:** "My children" in the Parent menu lists only the children the administrator linked to that parent, each with tests submitted out of available. Opening a child shows that child's per-chapter progress and test scores, read-only. Any other child's id in the URL gives "Page not found". **Mechanism:**
- `GET /children/` (`progress:children`, `child-progress:view`) → `linked_children(request.user.pk)`
- `GET /children/<student_id>/progress/` (`progress:child`, `child-progress:view` + `child-scores:view`) → `student_progress_for(request.user.pk, "PARENT", student_id)` (Story 7.1: linked ids loaded from the DB; `NotFound` otherwise) → shared partial with `interactive=False` (no learner action links)

**Authz & preconditions:** Parent only; a link must exist (admin-created). **Edge & idempotency:**
- No links → empty state "No children linked yet. Ask the administrator."
- Unlinking (admin) takes effect on the next request (404).
- Repeat loads are read-only.
- Earned scores of blocked tests stay visible (user decision).

**Regression:** IDOR on `student_id` (release-blocking privacy requirement), 403 for other roles, read-only (no learner links), counts match 7.1.

---

#### 👤 User Reference

**Description**:
Parents and guardians can follow their children's learning.
- **"My children":** from the menu, it lists the children the administrator has linked to their account, with how many chapter tests each has completed.
- **A child's page:** opening a child shows the same overview the child sees on "My progress": for each chapter, whether the lesson was read, how many exercises are finished, and the test score. There are no buttons to start lessons or tests, because parents watch progress rather than doing work on the child's behalf.

**Privacy:** a parent can never see a child who isn't linked to them. Even changing the number in the address only shows "Page not found", which doesn't confirm whether such a child exists. If the administrator removes a link, that child disappears from the parent's view immediately.

**Acceptance Criteria** (plain-English):
- Parents see "My children" in their menu and on their home page.
- The list shows only children linked to that parent by the administrator, with tests completed out of available.
- With no linked children, a friendly message says to ask the administrator.
- A child's page shows per-chapter progress and test scores, read-only (no start buttons).
- Opening any child not linked to the parent shows "Page not found".
- When the administrator removes a link, the child disappears and their page shows "Page not found".
- Scores already earned stay visible even if a test is later blocked.
- Students, teachers and administrators get "Access denied" on these parent pages.

**User Flow** (role-differentiated):

### Parent/Guardian
**Scenario / narrative**: As Ana's mother, I sign in and open "My children". I see "Ana Pop — 2 of 3 chapter tests completed". I open Ana's page and see MEM chapter 1 "Lesson read · Exercises 4/6 · Test 87/100". Curious, I change the number in the address to another id and get "Page not found". When I had no children linked yet, the page told me to ask the administrator.
**Steps**:
1. `GET /ro/children/` → `@require_permission(CHILD_PROGRESS_VIEW)` → `linked_children(user.pk)` → list (or empty state).
2. Click → `GET /ro/children/<sid>/progress/` → `@require_permission(CHILD_PROGRESS_VIEW, CHILD_SCORES_VIEW)` → `student_progress_for(user.pk, "PARENT", sid)` → 404 if not linked → render with `interactive=False`.

### Student
**Scenario / narrative**: As a Student, parent pages aren't for me; typing `/ro/children/` gives "Access denied".
**Steps**:
1. Both routes → 403.

### Teacher
**Scenario / narrative**: As a Teacher, I see all students on the Scores list (7.4); parent pages give "Access denied".
**Steps**:
1. Both routes → 403.

### Admin
**Scenario / narrative**: As the Admin, I manage links in the admin area and see scores on the Scores list; parent pages give "Access denied".
**Steps**:
1. Both routes → 403.

**Flow Diagram**:

```mermaid
flowchart TD
  A[Parent: GET /lang/children/] --> B[linked_children: only admin-linked]
  B --> C{any?}
  C -- no --> D[empty state: ask the administrator]
  C -- yes --> E[list with tests completed]
  E --> F[GET /lang/children/sid/progress/]
  F --> G{sid linked to this parent? (loaded from DB)}
  G -- no --> N[404]
  G -- yes --> H[read-only progress + scores]
```

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/requirements.md` — "Parents have read-only access to progress and scores for linked children only"
- `docs/architecture/design/00-system-architecture-greenfield.md` — routes `/children/`, `/children/<student_id>/progress/` (404 if not linked)
- `docs/plans/stories/epic-7-story-7.1-Progress-Read-Models-and-Web-Scaffold.md` — `linked_children`, `student_progress_for`, partial (`interactive`)
- `docs/plans/stories/epic-1-story-1.3-RBAC-Core.md` — IDOR guard rules

**Description**:
`web/progress/views/children.py` with `children` and `child_progress`; routes `"children/"` (`progress:children`) and `"children/<int:student_id>/progress/"` (`progress:child`) appended to `web/progress/urls.py`; templates `progress/children/list.html`, `detail.html` (staff theme for parents); matrix rows; route catalogue; translations.

**Design Tokens** (FE — staff theme):
- List: `ui_page_header` "My children"; `ui_table` caption "Linked children", columns Name · Chapter tests completed · (link "View progress"); empty `ui_empty_state` "No children linked yet. Ask the administrator." (icon `users`).
- Detail: `ui_page_header` "{child name}" with breadcrumb My children › {name}; subjects as h2 20px/600; chapters via the shared partial `interactive=False`.
- Generic avatar (`ui_avatar`) beside each child's name; no photos.

**Acceptance Criteria**:
1. `progress:children` → `GET /<lang>/children/`, `@require_safe` + `@require_permission(CHILD_PROGRESS_VIEW)`. Renders `linked_children(request.user.pk)` or the empty state.
2. `progress:child` → `GET /<lang>/children/<int:student_id>/progress/`, `@require_safe` + `@require_permission(CHILD_PROGRESS_VIEW, CHILD_SCORES_VIEW)`. Calls `student_progress_for(request.user.pk, request.user.role, student_id)`. A non-linked, non-student or unknown id → 404 (identical page).
3. The detail uses the partial with `interactive=False`: no lesson/practice/test links render.
4. Removing the link (admin) → next request to the detail returns 404 and the child disappears from the list.
5. Matrix rows: `/ro/children/` → Parent 200; Student/Teacher/Admin 403; anonymous 302. The detail route is asserted in this story's tests (dynamic ids).
6. Route catalogue + RO/EN translations ("My children", "Linked children", "Chapter tests completed", "View progress", "No children linked yet. Ask the administrator.").

**RBAC Enforcement**:

| Persona | Permission key | Guarded route/endpoint | Allowed | Denied behavior | UI when denied |
|---------|----------------|------------------------|---------|-----------------|----------------|
| Parent/Guardian | `child-progress:view` | `GET /<lang>/children/` | own links only | — | empty state when none |
| Parent/Guardian | `child-progress:view` + `child-scores:view` | `GET /<lang>/children/<id>/progress/` | linked children only | unlinked/unknown → 404 | link absent from list |
| Student | — | both | no | 403 | not in menu |
| Teacher | — | both | no | 403 | not in menu |
| Admin | — | both | no | 403 | not in menu |
| Anonymous | — | both | no | 302 login | sign-in |

- **Enforcement point(s):** `@require_permission` in `views/children.py`; linkage enforced inside `student_progress_for` (7.1) with `linked_student_ids` loaded from `ParentChildLinkModel` for `request.user.pk`.
- **Denied-access contract:** role → 403; record out of scope → 404 (never reveals existence).
- **Scope derivation:** the parent identity is `request.user.pk`; `student_id` in the URL is only the requested subject, checked against server-loaded links (IDOR guard).

**System responses + error cases**:

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| Parent with 1 link GET list | `200` one row | none |
| Parent with no links GET list | `200` empty state | none |
| Parent GET linked child detail | `200` read-only progress | none |
| Same GET repeated | identical `200` | none |
| Parent GET unlinked / unknown / teacher id | `404` | none |
| Link removed, parent GET detail | `404` | none |
| Child's test blocked after attempt | detail shows score | none |
| Student/Teacher/Admin GET | `403` | none |
| Anonymous GET | `302` login | none |

**QA-observable behaviour**:
- The list's student ids equal the parent's `accounts_parent_child_link` rows exactly.
- For every student id not linked (including other existing students), the detail returns 404 with the same template as a non-existent id.
- The detail page contains no `/chapters/` or `/tests/` action links.
- **What does NOT change**: no writes; links are managed only in the admin area (Story 1.9).

**Prerequisites**:
- Story 7.1 merged; Story 1.9 links (`linked_parent` fixture).

**Context**: `src/infrastructure/persistence/progress/queries.py`, `src/infrastructure/web/templates/progress/_chapter_progress.html`, `tests/conftest.py` (`linked_parent`, `unlinked_parent`)

**Patterns**: Thin views + decorators (§7.1–7.2), scope inside the query (§6.3), Primitives (§11.2) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first** (IDOR cases first).
2. **Views:**
   ```python
   # src/infrastructure/web/progress/views/children.py
   @require_safe
   @require_permission(Permission.CHILD_PROGRESS_VIEW)
   def children(request):
       """GET /<lang>/children/ — the parent's admin-linked children only."""
       return render(request, "progress/children/list.html", {"children": linked_children(request.user.pk)})


   @require_safe
   @require_permission(Permission.CHILD_PROGRESS_VIEW, Permission.CHILD_SCORES_VIEW)
   def child_progress(request, student_id: int):
       """GET /<lang>/children/<id>/progress/ — linked child only; otherwise 404 (no existence leak)."""
       progress = student_progress_for(request.user.pk, request.user.role, student_id)
       return render(request, "progress/children/detail.html", {"progress": progress})
   ```
3. **URLs, templates, matrix rows, route catalogue, translations,** then **all gates**.

**Tests**:

```python
# tests/integration/web/progress/children/test_children_pages.py
import pytest

from infrastructure.persistence.accounts.models import ParentChildLinkModel
from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db


def test_list_shows_only_linked_children(client, linked_parent, student):
    StudentFactory(full_name="Not Mine")
    client.force_login(linked_parent)

    html = client.get("/en/children/").content.decode()

    assert student.full_name in html and "Not Mine" not in html


def test_parent_without_links_sees_empty_state(client, unlinked_parent):
    client.force_login(unlinked_parent)

    assert "No children linked yet." in client.get("/en/children/").content.decode()


def test_linked_child_detail_is_read_only(client, linked_parent, student):
    client.force_login(linked_parent)

    response = client.get(f"/en/children/{student.pk}/progress/")

    assert response.status_code == 200
    assert "/chapters/" not in response.content.decode() and "/tests/" not in response.content.decode()


@pytest.mark.parametrize("target", ["other_student", "unknown", "teacher"])
def test_idor_attempts_are_404(client, linked_parent, teacher, target):
    ids = {"other_student": StudentFactory().pk, "unknown": 999999, "teacher": teacher.pk}
    client.force_login(linked_parent)

    assert client.get(f"/en/children/{ids[target]}/progress/").status_code == 404


def test_unlinking_takes_effect_immediately(client, linked_parent, student):
    client.force_login(linked_parent)
    ParentChildLinkModel.objects.filter(parent=linked_parent, student=student).delete()

    assert client.get(f"/en/children/{student.pk}/progress/").status_code == 404


@pytest.mark.parametrize("fixture", ["student_client", "teacher_client", "admin_client"])
def test_other_roles_are_denied(request, fixture, student):
    client = request.getfixturevalue(fixture)

    assert client.get("/ro/children/").status_code == 403
    assert client.get(f"/ro/children/{student.pk}/progress/").status_code == 403
```

Manual: as a linked Parent (RO/EN) open the list and detail; change the id in the URL (404); have the Admin remove the link and refresh (404); as other roles, 403.

**Quality**: ruff 0; mypy passes; tests pass; coverage ≥85%; no `TODO`.

**OUT**:
- ❌ Parents linking themselves or editing anything (admin-only, Story 1.9).
- ❌ Messaging teachers, notifications to parents, email reports (not required).

**Evidence**: pytest output (incl. all IDOR cases), coverage %, screenshots of the children list and a child's detail (RO), and the 404 for an unlinked id, all recorded in `docs/stories-implemented/story-7.3-review.md` under "## DoD Evidence".
