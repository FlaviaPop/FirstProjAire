### Story 8.6: Moderation E2E Journeys

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 8 - Content Moderation & Notifications | **ID**: 8.6 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-8-story-8.6-Moderation-E2E-Journeys.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 4: Playwright journeys; FC-2 "content block/notification handling")
**Wave**: 13
**Requires**: [8.4, 8.5]
**Enables**: []
**Files Touched**:
  - tests/e2e/test_moderation_flow.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation in *this story's code* (test-only; exercises Admin, Teacher and Student behaviour from 8.4/8.5)
**QA Candidate**: No — test-only story. It automates Epic 8 QA Group 1; its green run is CYCLE-3 sign-off evidence for FC-2 "incorrect content block/notification handling".

---

#### 👤 User Reference

**Description**:
Browser "robot" tests that play out the whole moderation story with three people (an administrator, a teacher and a student) in separate browser sessions:
1. The administrator flags a lesson, and the student immediately gets "Page not found" for it.
2. The administrator approves it, and the student can read it again.
3. The administrator blocks an exercise with a reason. The exercise disappears for the student, and the teacher sees a notification badge and the reason.
4. The teacher resubmits the exercise. It stays hidden from the student.
5. The administrator clears the block. The student sees it again.

The tests also check that a repeated action is refused and that a block without a proper reason is refused.

**Acceptance Criteria** (plain-English):
- One command runs the moderation journey in a real browser with three separate sign-ins.
- Flagging and blocking hide content from the student at once; approving and clearing bring it back.
- Blocking requires a reason; the teacher sees the reason in a notification and on the Dashboard.
- Resubmitted content stays hidden until the administrator clears it.
- Repeating an action shows "no longer possible".
- No browser security-policy errors occur.

**User Flow**:
Actor: system — no role variation.

**Flow Diagram**:

```mermaid
sequenceDiagram
  participant AD as Admin context
  participant TE as Teacher context
  participant ST as Student context
  AD->>AD: Moderation → lesson → Flag
  ST->>ST: lesson URL → Page not found
  AD->>AD: Approve
  ST->>ST: lesson visible
  AD->>AD: exercise → Block (short reason refused → valid reason)
  ST->>ST: exercise absent from list
  TE->>TE: badge 1 → notice with reason → Dashboard → Resubmit
  ST->>ST: still absent
  AD->>AD: Needs review → Clear block; repeat Clear → no longer possible
  ST->>ST: exercise visible again
```

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/plans/implementation-plan.md` — Epic 8 QA Group 1
- `docs/plans/stories/epic-1-story-1.10-Foundation-E2E-Journeys.md` — harness rules
- `docs/plans/stories/epic-8-story-8.4-Admin-Moderation-Queue-and-Actions.md`, `docs/plans/stories/epic-8-story-8.5-Teacher-Notifications-and-Resubmit.md` — labels/messages

**Description**:
`tests/e2e/test_moderation_flow.py` with one end-to-end test `test_flag_block_resubmit_clear_cycle`, using three Playwright browser contexts (`browser.new_context()`) so the three users are signed in simultaneously, plus `test_block_requires_reason_and_repeat_is_refused`. The seed (factories): MEM chapter 1 with an ACTIVE lesson and 5 exercises created and last edited by the Teacher.

**Acceptance Criteria**:
1. `uv run pytest -m e2e tests/e2e/test_moderation_flow.py` is green three times in a row, in < 2 min.
2. Each step of the Flow Diagram is asserted through the UI (no direct DB state changes after seeding).
3. The block dialog is operated by keyboard (Enter to open, type the reason, Enter to confirm). A 5-character reason shows the 10–1,000 characters message.
4. The teacher's badge reads 1 after the block and disappears after "Mark as read".
5. A repeat "Clear block" (stale page via `page.go_back()` + resubmit) shows "This action is no longer possible for this item."
6. `console_errors` in every context; no `time.sleep`.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- Test-only; three real sign-ins.

**System responses + error cases** (harness behaviour):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| `uv run pytest` | e2e deselected | none |
| `-m e2e` | journey runs | transactional DB discarded |
| Failure | trace + screenshot per context | artefacts |
| CSP console error (any context) | test fails | none |

**Prerequisites**:
- Stories 8.4 and 8.5 merged (and their dependencies); Chromium installed.

**Context**: `tests/e2e/conftest.py`, `tests/factories/content.py`

**Patterns**: E2E tests (§12.5) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Contexts helper** (excerpt):
   ```python
   # tests/e2e/test_moderation_flow.py
   def signed_in(browser, base_url, username):
       context = browser.new_context()
       page = context.new_page()
       login(page, base_url, username, lang="en")
       return page


   def test_flag_block_resubmit_clear_cycle(browser, base_url, seeded):
       admin, teacher, student = (signed_in(browser, base_url, u) for u in ("admin-e2e", "teacher-e2e", "student-e2e"))
       lesson_url = f"{base_url}/en/chapters/{seeded.chapter_id}/lesson/"

       admin.goto(f"{base_url}/en/manage/moderation/lesson/{seeded.lesson_id}/")
       admin.get_by_role("button", name="Flag for review").click()
       admin.get_by_role("dialog").get_by_role("button", name="Flag").click()
       expect(admin.get_by_text("Content flagged.")).to_be_visible()
       student.goto(lesson_url)
       expect(student.get_by_role("heading", name="Page not found")).to_be_visible()
   ```
   Every remaining Flow Diagram step is implemented explicitly in the final file. Console-error checks are attached per page via `page.on("console", …)` (the shared `console_errors` fixture covers only the default `page`, so the test adds an equivalent listener for each context).
2. **Run three times**; one deliberate local failure; revert.

**Tests**: this story *is* tests (3 green runs + deliberate failure).

Manual: one `--headed --slowmo=200` run to watch the three contexts.

**Quality**: ruff 0; role/label/text locators; no `time.sleep`; 3 green runs.

**OUT**:
- ❌ Test-taking and visibility journeys (6.6, 7.5).
- ❌ Production-code changes.

**Evidence**: 3-run output, step → assertion table, deliberate-failure trace, all recorded in `docs/stories-implemented/story-8.6-review.md` under "## DoD Evidence".
