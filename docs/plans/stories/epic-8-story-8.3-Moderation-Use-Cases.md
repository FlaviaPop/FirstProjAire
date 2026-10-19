### Story 8.3: Moderation Use Cases

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 8 - Content Moderation & Notifications | **ID**: 8.3 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-8-story-8.3-Moderation-Use-Cases.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 3: state machine applied; notifications on block; `MODERATION_EVENT` + `AUDIT_LOG` in the same transaction)
**Wave**: 11
**Requires**: [8.1, 8.2]
**Enables**: [8.4, 8.5]
**Files Touched**:
  - src/application/moderation/transition.py
  - src/application/moderation/flag_content.py
  - src/application/moderation/approve_content.py
  - src/application/moderation/block_content.py
  - src/application/moderation/resubmit_content.py
  - src/application/moderation/clear_block.py
  - src/infrastructure/persistence/moderation/repositories.py
  - src/infrastructure/persistence/notifications/repositories.py
  - src/infrastructure/container.py
  - tests/unit/application/moderation/**
  - tests/integration/persistence/moderation/test_moderation_repositories.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation in the use cases (callers in 8.4/8.5 enforce `content:review` / `content:block` / `content:unblock` / `content:resubmit`)
**QA Candidate**: No — application use cases and repositories with no route. Their effects (status, hiding, events, notices, audit) are user-observable through 8.4/8.5 and the E2E in 8.6, where QA checks them. They're proven here by unit and integration tests.

---

#### 👤 User Reference

**Description**:
This story makes the five moderation actions real:
- **Flag**
- **Approve**
- **Block** (with a reason)
- **Resubmit**
- **Clear the block**

Each works the same way and does everything in one go, or nothing at all if any step fails:
1. checks the action is allowed from the item's current state (the rules from Story 8.1)
2. changes the item's state; hiding from students and parents is immediate, because student pages only show "active" content
3. records the action in the moderation history
4. writes an audit log entry
5. for a block, sends an in-app notice with the reason to the teacher who created the item and the teacher who last changed it

The actions work the same for lessons, exercises and chapter tests. A blocked test hides its questions too, but already-earned scores stay, as agreed.

**Acceptance Criteria** (plain-English):
- Flag, approve, block, resubmit and clear change an item's state only when the move is allowed; otherwise nothing changes and the action is refused.
- Blocking needs a reason of 10–1,000 characters; the reason is saved on the item and in the notices.
- Each action records one moderation-history entry and one audit entry.
- A block notifies the creator and last editor once each; no notices for other actions.
- Flagged, blocked and resubmitted items disappear from student and parent views immediately; clearing or approving brings them back.
- If any part fails, nothing is saved (state, history, audit and notices stay consistent).
- Lessons, exercises and chapter tests all work the same way; unknown items are "not found".

**User Flow**:
Actor: system — no role variation.

**Flow Diagram**:

```mermaid
sequenceDiagram
  participant V as View (8.4 admin / 8.5 teacher)
  participant U as TransitionContent (Flag/Approve/Block/Resubmit/Clear)
  participant R as ModeratedContentRepository
  participant E as ModerationEventRepository
  participant N as NotifierPort
  participant A as AuditPort
  V->>U: execute(type, id, actor_id, reason?)
  Note over U: one UnitOfWork
  U->>R: get(type, id)  (None → NotFound)
  U->>U: next_status (illegal → InvalidModerationTransition 409); BLOCK → validate reason
  U->>R: set_status(new, reason, now)
  U->>E: add(event)
  alt action == BLOCK
    U->>N: notify_block(recipients(created_by, updated_by), reason)
  end
  U->>A: record("moderation.<action>", target)
  U-->>V: new status
```

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` — moderation rules table, ADR-008
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — §5 use cases, §6.3 repositories, §9 audit inside the UoW
- `docs/plans/stories/epic-8-story-8.1-Moderation-Domain-Rules.md` — `next_status`, `validate_block_reason`, `block_notice_recipients`, ports
- `docs/plans/stories/epic-8-story-8.2-Moderation-and-Notification-Data.md` — models, factories
- `docs/plans/stories/epic-3-story-3.2-Content-Data-Model.md` — `ModeratedModel` fields on Lesson/Exercise/ChapterTest

**Description**:
1. **`application/moderation/transition.py`:** `ModerationCommand(content_type, content_id, actor_id, actor_username, reason="")` and the base class `TransitionContent(content, events, notifier, audit, uow, clock)` with class attribute `action`; `execute(cmd) -> ModerationStatus`. Five thin subclasses in their own modules: `FlagContent`, `ApproveContent`, `BlockContent`, `ResubmitContent`, `ClearBlock` (one class per use case, patterns §5).
2. **Reason handling:**
   - BLOCK requires `validate_block_reason` and stores the stripped reason in `moderation_reason`
   - RESUBMIT and FLAG keep the existing reason (so teachers and admins still see why it was blocked)
   - APPROVE and CLEAR set `moderation_reason=""`
3. **`persistence/moderation/repositories.py`:** `DjangoModeratedContent` (maps `ContentType` → `LessonModel` / `ExerciseModel` / `ChapterTestModel`; `get` returns `ModeratedItem`; `set_status` updates `moderation_status`, `moderation_reason`, `moderation_updated_at` with a single `UPDATE`) and `DjangoModerationEvents`.
4. **`persistence/notifications/repositories.py`:** `DjangoNotifier.notify_block` (`bulk_create` one `NotificationModel` per recipient).
5. **Container** factories `flag_content()`, `approve_content()`, `block_content()`, `resubmit_content()`, `clear_block()`.

**Acceptance Criteria**:
1. Each use case: `get` → `None` ⇒ `NotFound`; `next_status(current, action)` ⇒ `InvalidModerationTransition` on illegal moves; BLOCK with an invalid reason ⇒ `PolicyViolation([block_reason_length])`. No writes in any of these cases.
2. On success, within one UoW:
   - `set_status` (new status, reason rules from Description item 2, `moderation_updated_at = clock.now()`)
   - `events.add(content_type, content_id, action, from, to, reason, actor_id, actor_username, at)`
   - for BLOCK only, `notifier.notify_block(block_notice_recipients(created_by, updated_by), …)`
   - `audit.record(f"moderation.{action.lower()}", actor_id=…, target=(content_type, str(content_id)), metadata={"from": from, "to": to})` (the reason is **not** in audit metadata; it's kept in the event)
3. Failure in any step (e.g. the notifier raises) rolls back all writes (integration test with a failing notifier).
4. After FLAG/BLOCK/RESUBMIT, the item is excluded by `visible_to_learners()`; after APPROVE/CLEAR, it's included again (integration).
5. The model choice values in `moderation/models.py` equal the domain enums (`ContentType`, `ModerationAction`, `ModerationStatus`); a test asserts equality.
6. Coverage: `application/moderation/**` 100%; overall ≥85%.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- No route. Views must check `REQUIRED_PERMISSION[action]` (8.1) via `@require_permission` and pass `actor_id = request.user.pk` and `actor_username = request.user.username`. The use cases never derive the actor from other input.

**System responses + error cases** (use-case contract):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| FLAG an ACTIVE lesson | `FLAGGED` | status, 1 event, 1 audit row |
| FLAG it again | `InvalidModerationTransition` | none |
| BLOCK a FLAGGED exercise with a valid reason | `BLOCKED` | status + reason, event, audit, 1–2 notifications |
| BLOCK with a 5-char reason | `PolicyViolation` | none |
| RESUBMIT a BLOCKED item | `RESUBMITTED` (reason kept) | event + audit; no notification |
| CLEAR a RESUBMITTED item | `ACTIVE` (reason cleared) | event + audit |
| CLEAR an ACTIVE item | `InvalidModerationTransition` | none |
| APPROVE a FLAGGED item | `ACTIVE` | event + audit |
| Unknown content id | `NotFound` | none |
| Notifier raises during BLOCK | exception | full rollback (status unchanged, no event/audit) |
| BLOCK a test that has attempts | `BLOCKED` | attempts untouched |

**Prerequisites**:
- Stories 8.1 and 8.2 merged; CYCLE-1 audit/UoW; CYCLE-2 content models.

**Context**: `src/domain/moderation/**`, `src/infrastructure/persistence/moderation/models.py`, `src/infrastructure/persistence/notifications/models.py`, `src/infrastructure/persistence/content/models.py`, `src/infrastructure/container.py`

**Patterns**: Use cases + UoW (§5), Repositories (§6.3), Audit inside the UoW (§9), Fakes (§12.2) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first** (unit with fakes for every row; integration for persistence, visibility and rollback).
2. **Base use case:**
   ```python
   # src/application/moderation/transition.py
   from dataclasses import dataclass

   from application.common.audit import AuditPort
   from application.common.unit_of_work import UnitOfWork
   from domain.common.clock import Clock
   from domain.common.errors import NotFound, PolicyViolation
   from domain.moderation.notifications import block_notice_recipients
   from domain.moderation.ports import ModeratedContentRepository, ModerationEventRepository, NotifierPort
   from domain.moderation.state_machine import ContentType, ModerationAction, next_status, validate_block_reason
   from domain.moderation.status import ModerationStatus


   @dataclass(frozen=True)
   class ModerationCommand:
       content_type: ContentType
       content_id: int
       actor_id: int          # request.user.pk
       actor_username: str
       reason: str = ""


   class TransitionContent:
       action: ModerationAction

       def __init__(self, content: ModeratedContentRepository, events: ModerationEventRepository,
                    notifier: NotifierPort, audit: AuditPort, uow: UnitOfWork, clock: Clock) -> None:
           self._content, self._events, self._notifier = content, events, notifier
           self._audit, self._uow, self._clock = audit, uow, clock

       def execute(self, cmd: ModerationCommand) -> ModerationStatus:
           with self._uow:
               item = self._content.get(cmd.content_type, cmd.content_id)
               if item is None:
                   raise NotFound("content")
               target = next_status(ModerationStatus(item.status), self.action)
               reason = self._reason_for(cmd, item)
               now = self._clock.now()
               self._content.set_status(cmd.content_type, cmd.content_id, target, reason, now)
               self._events.add(cmd.content_type, cmd.content_id, self.action, item.status, target, reason,
                                cmd.actor_id, cmd.actor_username, now)
               if self.action is ModerationAction.BLOCK:
                   self._notifier.notify_block(block_notice_recipients(item.created_by, item.updated_by),
                                               cmd.content_type, cmd.content_id, reason, now)
               self._audit.record(f"moderation.{self.action.lower()}", actor_id=cmd.actor_id,
                                  actor_username=cmd.actor_username,
                                  target=(cmd.content_type.value, str(cmd.content_id)),
                                  metadata={"from": item.status, "to": target.value})
           return target

       def _reason_for(self, cmd: ModerationCommand, item) -> str:
           if self.action is ModerationAction.BLOCK:
               if violations := validate_block_reason(cmd.reason):
                   raise PolicyViolation(violations)
               return cmd.reason.strip()
           if self.action in (ModerationAction.APPROVE, ModerationAction.CLEAR):
               return ""
           return item.reason  # FLAG / RESUBMIT keep the last block reason visible
   ```
   ```python
   # src/application/moderation/block_content.py
   from application.moderation.transition import TransitionContent
   from domain.moderation.state_machine import ModerationAction


   class BlockContent(TransitionContent):
       """Admin blocks content with a reason; hidden at once; creator + last editor notified (requirements)."""

       action = ModerationAction.BLOCK
   ```
3. **Repositories and container** per the Description; **run gates.**

**Tests**:

```python
# tests/unit/application/moderation/test_transitions.py
import pytest

from application.moderation.block_content import BlockContent
from application.moderation.clear_block import ClearBlock
from application.moderation.flag_content import FlagContent
from application.moderation.resubmit_content import ResubmitContent
from application.moderation.transition import ModerationCommand
from domain.common.errors import NotFound, PolicyViolation
from domain.moderation.ports import ModeratedItem
from domain.moderation.state_machine import ContentType, InvalidModerationTransition
from tests.fakes import FakeAuditPort, FakeUnitOfWork, FixedClock

REASON = "Wrong answer in exercise 3."


class FakeContent:
    def __init__(self, status, created_by=3, updated_by=5, item_reason=""):
        self.item = ModeratedItem(ContentType.LESSON, 1, status, created_by, updated_by, item_reason)
        self.updates = []

    def get(self, content_type, content_id):
        return self.item if content_id == 1 else None

    def set_status(self, content_type, content_id, status, reason, at):
        self.updates.append((status, reason))


class FakeEvents:
    def __init__(self):
        self.rows = []

    def add(self, *args):
        self.rows.append(args)


class FakeNotifier:
    def __init__(self):
        self.calls = []

    def notify_block(self, recipients, content_type, content_id, reason, at):
        self.calls.append((recipients, reason))


def run(use_case_class, status, reason="", content_id=1, **item):
    content, events, notifier, audit = FakeContent(status, **item), FakeEvents(), FakeNotifier(), FakeAuditPort()
    use_case = use_case_class(content, events, notifier, audit, FakeUnitOfWork(), FixedClock())
    result = use_case.execute(ModerationCommand(ContentType.LESSON, content_id, 9, "admin1", reason))
    return result, content, events, notifier, audit


def test_block_notifies_creator_and_editor_once_each():
    result, content, events, notifier, audit = run(BlockContent, "FLAGGED", REASON)

    assert result == "BLOCKED" and content.updates == [("BLOCKED", REASON)]
    assert notifier.calls == [((3, 5), REASON)] and len(events.rows) == 1
    assert audit.records[0]["action"] == "moderation.block" and "reason" not in audit.records[0]["metadata"]


def test_same_creator_and_editor_notified_once():
    _, _, _, notifier, _ = run(BlockContent, "ACTIVE", REASON, created_by=3, updated_by=3)

    assert notifier.calls[0][0] == (3,)


def test_short_reason_rejected_without_writes():
    with pytest.raises(PolicyViolation):
        run(BlockContent, "ACTIVE", "short")


def test_illegal_transition_rejected():
    with pytest.raises(InvalidModerationTransition):
        run(ClearBlock, "ACTIVE")


def test_resubmit_keeps_reason_and_does_not_notify():
    _, content, _, notifier, _ = run(ResubmitContent, "BLOCKED", item_reason=REASON)

    assert content.updates == [("RESUBMITTED", REASON)] and notifier.calls == []


def test_unknown_item_not_found():
    with pytest.raises(NotFound):
        run(FlagContent, "ACTIVE", content_id=99)
```

```python
# tests/integration/persistence/moderation/test_moderation_repositories.py
import pytest

from domain.moderation.state_machine import ContentType
from infrastructure import container
from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.content.models import LessonModel
from infrastructure.persistence.moderation.models import ModerationEventModel
from infrastructure.persistence.notifications.models import NotificationModel
from application.moderation.transition import ModerationCommand
from tests.factories.accounts import TeacherFactory
from tests.factories.content import LessonFactory

pytestmark = pytest.mark.django_db
REASON = "Contains a wrong example in section 2."


def cmd(lesson, reason="", admin_id=None):
    return ModerationCommand(ContentType.LESSON, lesson.pk, admin_id or 1, "admin1", reason)


def test_block_hides_records_and_notifies(admin_user):
    creator, editor = TeacherFactory(), TeacherFactory()
    lesson = LessonFactory(created_by=creator, updated_by=editor)

    container.block_content().execute(cmd(lesson, REASON, admin_user.pk))

    assert not LessonModel.objects.visible_to_learners().filter(pk=lesson.pk).exists()
    assert ModerationEventModel.objects.get().to_status == "BLOCKED"
    assert set(NotificationModel.objects.values_list("recipient_id", flat=True)) == {creator.pk, editor.pk}
    assert AuditLogModel.objects.filter(action="moderation.block").count() == 1


def test_full_cycle_restores_visibility(admin_user, teacher):
    lesson = LessonFactory()
    container.flag_content().execute(cmd(lesson, admin_id=admin_user.pk))
    container.block_content().execute(cmd(lesson, REASON, admin_user.pk))
    container.resubmit_content().execute(cmd(lesson, admin_id=teacher.pk))
    assert not LessonModel.objects.visible_to_learners().filter(pk=lesson.pk).exists()

    container.clear_block().execute(cmd(lesson, admin_id=admin_user.pk))

    lesson.refresh_from_db()
    assert (lesson.moderation_status, lesson.moderation_reason) == ("ACTIVE", "")
    assert ModerationEventModel.objects.count() == 4


def test_notifier_failure_rolls_everything_back(admin_user, monkeypatch):
    from infrastructure.persistence.notifications.repositories import DjangoNotifier

    monkeypatch.setattr(DjangoNotifier, "notify_block", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    lesson = LessonFactory()

    with pytest.raises(RuntimeError):
        container.block_content().execute(cmd(lesson, REASON, admin_user.pk))

    lesson.refresh_from_db()
    assert lesson.moderation_status == "ACTIVE"
    assert ModerationEventModel.objects.count() == 0 and AuditLogModel.objects.filter(action="moderation.block").count() == 0


def test_model_choices_equal_domain_enums():
    choices = ModerationEventModel._meta.get_field("content_type").choices
    assert {value for value, _ in choices} == {c.value for c in ContentType}
```

Manual: none (no UI); the 8.4/8.5 pages exercise these.

**Quality**: ruff 0; mypy strict for `application.moderation`; tests pass; 100% coverage for `application/moderation/**`; no reasons or PII in audit metadata; no `TODO`.

**OUT**:
- ❌ The admin queue/actions UI (8.4) and the teacher notices/resubmit UI (8.5).
- ❌ Email notifications (in-app only).
- ❌ Moderating chapter titles (architecture: not moderated).

**Evidence**: pytest output (unit + integration incl. the rollback test), 100% coverage for `application/moderation`, and DB excerpts (event, notifications, audit) for one block, all recorded in `docs/stories-implemented/story-8.3-review.md` under "## DoD Evidence".
