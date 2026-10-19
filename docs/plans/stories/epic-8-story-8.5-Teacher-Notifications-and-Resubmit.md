### Story 8.5: Teacher Notifications & Resubmit

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 8 - Content Moderation & Notifications | **ID**: 8.5 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-8-story-8.5-Teacher-Notifications-and-Resubmit.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 3: teacher resubmit; notifications with unread badge; mark as read)
**Wave**: 12
**Requires**: [8.3]
**Enables**: [8.6]
**Files Touched**:
  - src/application/notifications/**
  - src/infrastructure/persistence/notifications/queries.py
  - src/infrastructure/persistence/notifications/repositories.py
  - src/infrastructure/container.py
  - src/infrastructure/web/notifications/**
  - src/infrastructure/web/templates/notifications/**
  - src/infrastructure/web/templates/layouts/_top_bar.html
  - src/infrastructure/web/templatetags/notifications.py
  - src/infrastructure/web/content/views/resubmit.py
  - src/infrastructure/web/content/urls.py
  - src/infrastructure/persistence/content/queries/teacher.py
  - src/infrastructure/web/templates/content/dashboard/**
  - src/config/urls.py
  - src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po
  - src/infrastructure/i18n/locale/en/LC_MESSAGES/django.po
  - tests/integration/web/test_role_access_matrix.py
  - docs/architecture/design/00-system-architecture-greenfield.md
  - tests/unit/application/notifications/**
  - tests/integration/web/notifications/**
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — personas this story differentiates: Teacher, Admin, Student, Parent/Guardian
**QA Candidate**: Yes — **Observable:**
- Teachers see an unread-count badge on "Notifications" in the top bar.
- The Notifications page lists their block notices (newest unread first), with the item, the reason and the date; each can be marked as read.
- On the Dashboard, blocked items show a "Blocked" pill, the admin's reason and a "Resubmit" button. Resubmitted items show "Resubmitted, waiting for review" and stay hidden from students.

**Mechanism:**
- `GET /teach/notifications/` (`notifications:list`, `content:edit`) → `notifications_for(request.user.pk)`.
- `POST /teach/notifications/<id>/read/` (`notifications:read`, `content:edit`) → `MarkNotificationRead` (recipient must be `request.user`, else `NotFound`; idempotent).
- `{% unread_badge %}` (1 query) in `_top_bar.html` for teachers.
- `POST /teach/content/<type>/<id>/resubmit/` (`content:resubmit`, `content:resubmit`) → `ResubmitContent` (Story 8.3) → 302 dashboard; illegal → 409.
- `teacher_dashboard()` (Story 3.5) now carries reasons and blocked exercises.

**Authz & preconditions:** Teacher (`content:edit` for notices, `content:resubmit` for resubmit); notices are scoped to the recipient. **Edge & idempotency:**
- Marking an already-read notice keeps its first `read_at`.
- Another teacher's notice id → 404.
- Resubmitting an item that isn't BLOCKED → 409.
- The badge is hidden at 0.
- Both pilot teachers can resubmit any pilot content (no per-teacher ownership), but notices go only to the creator/last editor (8.3).

**Regression:** notice privacy between teachers, badge count accuracy, resubmit keeps content hidden until cleared, 403 for non-teachers.

---

#### 👤 User Reference

**Description**:
When an administrator blocks content, the teachers concerned need to know why and to send the fix back.
- **Notifications badge:** a small number next to "Notifications" in the top bar counts unread notices.
- **Notifications page:**
  - each notice says what was blocked (for example "Exercise 3 · MEM · Chapter 1"), the administrator's reason and when
  - it links to the editor, and can be marked as read
  - each teacher sees only their own notices
- **Dashboard:**
  - blocked lessons, exercises and tests are clearly marked "Blocked" with the reason
  - after fixing an item in its editor, the teacher presses **"Resubmit"**; the item becomes "Resubmitted, waiting for review"
  - it stays hidden from students until the administrator clears it

**Acceptance Criteria** (plain-English):
- Teachers see an unread count next to "Notifications" when they have unread notices; no badge when there are none.
- The Notifications page lists the teacher's own notices, unread first, each with the item, the reason, the date and a link to fix it.
- A notice can be marked as read; marking it again changes nothing.
- A teacher can't see or mark another teacher's notices ("Page not found").
- The Dashboard shows blocked items with their reason and a "Resubmit" button.
- Resubmitting changes the item to "Resubmitted"; it remains hidden from students until the administrator clears it.
- Resubmitting something that isn't blocked is refused with a clear message.
- Students, parents and administrators get "Access denied" on these teacher pages.

**User Flow** (role-differentiated):

### Teacher
**Scenario / narrative**: As the Teacher who wrote MEM exercise 3, I see "Notificări (1)" in the top bar. The page says "Exercise 3 · MEM · Chapter 1 was blocked: The correct answer should be 42, not 52. Please fix." with a link. I fix the answer in the exercise editor, return to the Dashboard where exercise 3 shows "Blocked · reason…" with "Resubmit", and press it. It now shows "Resubmitted, waiting for review". I mark the notice as read, and the badge disappears.
**Steps**:
1. Every page: `_top_bar.html` → `{% unread_badge %}` → `unread_count(request.user.pk)` (1 query) → `ui_badge` linking to `notifications:list`.
2. `GET /ro/teach/notifications/` → `@require_permission(CONTENT_EDIT)` → `notifications_for(user.pk)` → list with links (`content:exercise_edit` etc. via `{% url … as %}`).
3. "Mark as read" → `POST …/notifications/<nid>/read/` → `MarkNotificationRead.execute(nid, recipient_id=user.pk)` → 302 list.
4. Dashboard → POST `/ro/teach/content/exercise/<eid>/resubmit/` → `@require_permission(CONTENT_RESUBMIT)` → `container.resubmit_content().execute(ModerationCommand(EXERCISE, eid, user.pk, user.username))` → 302 dashboard + "Sent for review again."

### Admin
**Scenario / narrative**: As the Admin, I don't receive teacher notices or resubmit. The resubmitted item appears in my "Needs review" queue (8.4). Teacher notification URLs answer "Access denied".
**Steps**:
1. `/ro/teach/notifications/` → 403; resubmit POST → 403 (Admin lacks `content:resubmit`).

### Student
**Scenario / narrative**: As a Student, I never see blocked or resubmitted items or teacher notices; these URLs answer "Access denied".
**Steps**:
1. All routes → 403.

### Parent/Guardian
**Scenario / narrative**: As a Parent, I have no access to teacher notices: "Access denied".
**Steps**:
1. All routes → 403.

**Flow Diagram**:

```mermaid
flowchart TD
  A[Admin blocks item (8.4)] --> B[Notification rows for creator + last editor]
  B --> C[Teacher top bar badge: unread count]
  C --> D[Notifications page: own notices only]
  D --> E[Mark as read → read_at set once]
  D --> F[Fix item in editor]
  F --> G[Dashboard: Blocked + reason + Resubmit]
  G --> H{content:resubmit and status BLOCKED?}
  H -- no --> I[403 / 409]
  H -- yes --> J[RESUBMITTED — still hidden → Admin queue]
```

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/requirements.md` — "When content is blocked, notify its teacher in-app with the reason… Resubmitted content remains hidden until an admin clears the block."
- `docs/architecture/design/00-system-architecture-greenfield.md` — routes `/teach/notifications/`, `/teach/notifications/<id>/read/`, `/teach/content/<type>/<id>/resubmit/`
- `docs/plans/stories/epic-8-story-8.3-Moderation-Use-Cases.md` — `ResubmitContent`, `ModerationCommand`
- `docs/plans/stories/epic-3-story-3.5-Teacher-Dashboard-and-Chapters.md` — `teacher_dashboard()` DTOs and templates being extended
- `docs/plans/stories/epic-1-story-1.7-App-Shell-and-Role-Homes.md` — `_top_bar.html`, registry `notifications:list`

**Description**:
1. **Application** `application/notifications/mark_notification_read.py`: `MarkNotificationRead(notifications: NotificationRepositoryPort, uow, clock).execute(notification_id, recipient_id) -> bool`. It raises `NotFound` when the notice doesn't belong to `recipient_id` and returns `False` if already read (port declared in the module, as in Story 1.4).
2. **Persistence:**
   - `notifications/queries.py`: `notifications_for(recipient_id) -> tuple[NoticeDTO]` (item label resolved via content models: type, subject, chapter number, position/title; `NotFound`-safe if the item was deleted → label "Removed item") and `unread_count(recipient_id) -> int`
   - `notifications/repositories.py` gains `DjangoNotificationRepository` (`owner_of`, `mark_read_if_unread`)
3. **Web:**
   - `web/notifications/` (`app_name = "notifications"`, included at `teach/notifications/` in `i18n_patterns`): `list`, `mark_read`
   - `templatetags/notifications.py::unread_badge` (takes context; renders nothing unless the role is TEACHER)
   - `_top_bar.html` includes it next to the "Notifications" nav item
4. **Resubmit:** `web/content/views/resubmit.py` + route in `web/content/urls.py`: `"content/<str:content_type>/<int:content_id>/resubmit/"` (`content:resubmit`).
5. **Dashboard:**
   - `queries/teacher.py` adds `lesson_reason`, `test_reason`, and `blocked_exercises: tuple[(id, position, reason, status)]` per slot (statuses BLOCKED/RESUBMITTED/FLAGGED), keeping ≤ 4 queries
   - dashboard templates render the reasons and Resubmit forms (POST with CSRF) for BLOCKED items, and "Resubmitted, waiting for review" for RESUBMITTED

**Design Tokens** (FE — staff theme):
- Badge: `ui_badge count label="unread notifications"` beside the nav item; bg `#B45309`, text `#FFFFFF` (5.02:1), min 20px circle; hidden at 0.
- Notifications page: `ui_page_header` "Notifications"; each notice as `ui_card`: unread → left border 4px `#B45309` + bold title; read → muted `#4B5563`; reason in a quote block; "Fix it" link (`#0E7490`); "Mark as read" `ui_button` secondary (POST). Empty: `ui_empty_state` "No notifications."
- Dashboard: blocked item row → `ui_status_pill BLOCKED` + reason (`#7F1D1D` on `#FEE2E2` block) + "Resubmit" `ui_button` primary (icon `arrow-counter-clockwise`); resubmitted → `ui_status_pill RESUBMITTED` + "Waiting for review" (`#164E63`); flagged → `ui_status_pill FLAGGED` + "Under review".

**Acceptance Criteria**:
1. `notifications:list` → `GET /<lang>/teach/notifications/` (`CONTENT_EDIT`). It shows only `recipient = request.user` notices, unread first (newest first within each group), with item label, reason, date and a fix link to the right editor.
2. `notifications:read` → `POST /<lang>/teach/notifications/<int:id>/read/` (`CONTENT_EDIT`) → `MarkNotificationRead`. Another recipient's id or unknown → 404. Already read → 302 and `read_at` unchanged.
3. `{% unread_badge %}` renders a badge with the count for teachers with ≥ 1 unread; nothing for count 0 or other roles; 1 SQL query.
4. `content:resubmit` → `POST /<lang>/teach/content/<type>/<id>/resubmit/` (`CONTENT_RESUBMIT`); `type` must be `lesson|exercise|test` (else 404). BLOCKED → RESUBMITTED, 302 dashboard + "Sent for review again." Not BLOCKED → 409 (registered message from 8.4). Unknown → 404.
5. The dashboard shows reasons and Resubmit for BLOCKED lessons, tests and exercises; "Waiting for review" for RESUBMITTED; "Under review" for FLAGGED. `teacher_dashboard()` stays ≤ 4 queries (asserted).
6. After resubmit, learner routes still hide the item (404/absent) until the Admin clears it (8.4).
7. Matrix rows: `/ro/teach/notifications/` → Teacher 200; Admin/Student/Parent 403; anonymous 302. The registry entry `notifications:list` (Story 1.7) now resolves for teachers.
8. Route catalogue + RO/EN translations.

**RBAC Enforcement**:

| Persona | Permission key | Guarded route/endpoint | Allowed | Denied behavior | UI when denied |
|---------|----------------|------------------------|---------|-----------------|----------------|
| Teacher | `content:edit` | `GET /<lang>/teach/notifications/`, `POST …/<id>/read/` | own notices only | others' ids → 404 | badge + menu item |
| Teacher | `content:resubmit` | `POST /<lang>/teach/content/<type>/<id>/resubmit/` | BLOCKED items | not BLOCKED → 409 | button only on BLOCKED rows |
| Admin | — | all three | no | 403 | not in menu |
| Student | — | all three | no | 403 | — |
| Parent/Guardian | — | all three | no | 403 | — |
| Anonymous | — | all three | no | 302 login | sign-in |

- **Enforcement point(s):** `@require_permission` on the views; ownership inside `MarkNotificationRead` and `notifications_for(request.user.pk)`; transition legality in `ResubmitContent`.
- **Denied-access contract:** 403 roles; 404 for notices not owned by the viewer (no existence leak); 409 for illegal resubmits.
- **Scope derivation:** `recipient_id`/`actor_id` = `request.user.pk`; no notice is fetched by id without the recipient filter.

**System responses + error cases**:

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| Teacher with 2 unread GET any page | badge "2" | none (1 query) |
| Teacher GET notifications | `200` own notices, unread first | none |
| POST mark read (own, unread) | `302` | `read_at` set |
| Same POST again | `302` | none |
| POST mark read for another teacher's notice | `404` | none |
| POST resubmit BLOCKED exercise | `302` "Sent for review again." | RESUBMITTED, event, audit (8.3) |
| POST resubmit again (now RESUBMITTED) | `409` | none |
| POST resubmit `/content/video/1/` | `404` | none |
| Admin/Student/Parent any route | `403` | none |
| Notice whose item was deleted | listed with "Removed item" (no link) | none |

**QA-observable behaviour**:
- After a block, the creator/editor badge shows the unread count. Marking read decrements it; at 0 the badge disappears.
- Teacher A never sees Teacher B's notices (list and URL).
- After resubmit, `moderation_status='RESUBMITTED'`, the item is still absent from learner routes, and it appears in the Admin "Needs review".
- **What does NOT change**: content text; notices are never deleted by reading; the admin's reason is never editable by teachers.

**Prerequisites**:
- Story 8.3 merged (and 8.2 models); CYCLE-1 top bar; CYCLE-2 dashboard.

**Context**: `src/application/moderation/resubmit_content.py`, `src/infrastructure/persistence/notifications/models.py`, `src/infrastructure/persistence/content/queries/teacher.py`, `src/infrastructure/web/templates/layouts/_top_bar.html`, `src/infrastructure/web/templates/content/dashboard/`

**Patterns**: Use cases for writes (§5), Query services with scope (§6.3), Thin views (§7.1–7.2), Responses 404/409 (§7.5), Primitives — badge, card (§11.2) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first** (privacy, badge, idempotent read, resubmit legality, dashboard query bound).
2. **Use case:**
   ```python
   # src/application/notifications/mark_notification_read.py
   class NotificationRepositoryPort(Protocol):
       def owner_of(self, notification_id: int) -> int | None: ...
       def mark_read_if_unread(self, notification_id: int, at: datetime) -> bool: ...


   class MarkNotificationRead:
       def __init__(self, notifications: NotificationRepositoryPort, uow: UnitOfWork, clock: Clock) -> None:
           self._notifications, self._uow, self._clock = notifications, uow, clock

       def execute(self, notification_id: int, recipient_id: int) -> bool:
           """Only the recipient may mark it; returns False if it was already read (idempotent)."""
           with self._uow:
               if self._notifications.owner_of(notification_id) != recipient_id:
                   raise NotFound("notification")
               return self._notifications.mark_read_if_unread(notification_id, self._clock.now())
   ```
3. **Badge tag:**
   ```python
   # src/infrastructure/web/templatetags/notifications.py
   @register.inclusion_tag("notifications/_badge.html", takes_context=True)
   def unread_badge(context) -> dict:
       user = context["request"].user
       if not user.is_authenticated or user.role != "TEACHER":
           return {"count": 0}
       return {"count": unread_count(user.pk)}
   ```
4. **Views, resubmit route, dashboard query/template changes, top bar include, container (`mark_notification_read()`), URLs, matrix rows, route catalogue, translations,** then **all gates**.

**Tests**:

```python
# tests/unit/application/notifications/test_mark_notification_read.py
import pytest

from application.notifications.mark_notification_read import MarkNotificationRead
from domain.common.errors import NotFound
from tests.fakes import FakeUnitOfWork, FixedClock


class FakeNotifications:
    def __init__(self):
        self.owner, self.read = {1: 7}, set()

    def owner_of(self, notification_id):
        return self.owner.get(notification_id)

    def mark_read_if_unread(self, notification_id, at):
        first = notification_id not in self.read
        self.read.add(notification_id)
        return first


def test_owner_marks_once():
    use_case = MarkNotificationRead(FakeNotifications(), FakeUnitOfWork(), FixedClock())

    assert use_case.execute(1, 7) is True
    assert use_case.execute(1, 7) is False


@pytest.mark.parametrize(("notification_id", "recipient"), [(1, 8), (99, 7)])
def test_other_or_unknown_is_not_found(notification_id, recipient):
    with pytest.raises(NotFound):
        MarkNotificationRead(FakeNotifications(), FakeUnitOfWork(), FixedClock()).execute(notification_id, recipient)
```

```python
# tests/integration/web/notifications/test_notifications_and_resubmit.py
import pytest

from infrastructure.persistence.content.models import ExerciseModel
from infrastructure.persistence.notifications.models import NotificationModel
from tests.factories.accounts import TeacherFactory
from tests.factories.content import ExerciseFactory
from tests.factories.moderation import NotificationFactory

pytestmark = pytest.mark.django_db
REASON = "The correct answer should be 42, not 52."


def test_badge_counts_unread_and_hides_at_zero(teacher_client, teacher):
    note = NotificationFactory(recipient=teacher, reason=REASON, read_at=None)

    assert 'aria-label="1 unread notifications"' in teacher_client.get("/en/").content.decode()

    teacher_client.post(f"/en/teach/notifications/{note.pk}/read/")
    assert "unread notifications" not in teacher_client.get("/en/").content.decode()


def test_notices_are_private_between_teachers(teacher_client, teacher):
    other = TeacherFactory()
    theirs = NotificationFactory(recipient=other, reason="Their secret reason text")
    NotificationFactory(recipient=teacher, reason=REASON)

    html = teacher_client.get("/en/teach/notifications/").content.decode()

    assert REASON in html and "Their secret reason text" not in html
    assert teacher_client.post(f"/en/teach/notifications/{theirs.pk}/read/").status_code == 404


def test_mark_read_is_idempotent(teacher_client, teacher):
    note = NotificationFactory(recipient=teacher, read_at=None)
    teacher_client.post(f"/en/teach/notifications/{note.pk}/read/")
    first = NotificationModel.objects.get(pk=note.pk).read_at

    teacher_client.post(f"/en/teach/notifications/{note.pk}/read/")

    assert NotificationModel.objects.get(pk=note.pk).read_at == first


def test_resubmit_blocked_exercise_keeps_it_hidden(teacher_client, student_client):
    exercise = ExerciseFactory(moderation_status="BLOCKED", moderation_reason=REASON)

    response = teacher_client.post(f"/en/teach/content/exercise/{exercise.pk}/resubmit/")

    assert response.status_code == 302
    assert ExerciseModel.objects.get(pk=exercise.pk).moderation_status == "RESUBMITTED"
    page = student_client.get(f"/en/chapters/{exercise.chapter_id}/exercises/").content.decode()
    assert exercise.prompt_en not in page
    assert teacher_client.post(f"/en/teach/content/exercise/{exercise.pk}/resubmit/").status_code == 409


def test_dashboard_shows_reason_and_resubmit(teacher_client):
    exercise = ExerciseFactory(moderation_status="BLOCKED", moderation_reason=REASON,
                               chapter__subject__grade__code="2", chapter__subject__code="MEM")

    html = teacher_client.get("/en/teach/").content.decode()

    assert REASON in html and f"/teach/content/exercise/{exercise.pk}/resubmit/" in html


@pytest.mark.parametrize("fixture", ["admin_client", "student_client", "parent_client"])
def test_non_teachers_are_denied(request, fixture):
    client, exercise = request.getfixturevalue(fixture), ExerciseFactory(moderation_status="BLOCKED")

    assert client.get("/ro/teach/notifications/").status_code == 403
    assert client.post(f"/ro/teach/content/exercise/{exercise.pk}/resubmit/").status_code == 403
```

Manual: as Admin block an item (8.4); as its Teacher check the badge, read the notice, fix the item, resubmit from the Dashboard, and confirm the student still can't see it; as Admin clear it (visible again). As another teacher, the notice isn't visible. As Admin/Student/Parent: 403.

**Quality**: ruff 0; mypy strict for `application.notifications`; tests pass; dashboard ≤ 4 queries; badge 1 query; coverage ≥85%; no `TODO`.

**OUT**:
- ❌ Email/push notifications (in-app only per requirements).
- ❌ Notices for flag/approve/clear (requirements: notify on block).
- ❌ Teachers editing the admin's reason or replying in-app (not required).

**Evidence**: pytest output, coverage %, screenshots of the badge, the Notifications page (RO), the Dashboard with a blocked item + reason + Resubmit, and the "Waiting for review" state, all recorded in `docs/stories-implemented/story-8.5-review.md` under "## DoD Evidence".
