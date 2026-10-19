### Story 7.5: Visibility E2E Journeys

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 7 - Progress & Score Visibility | **ID**: 7.5 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-7-story-7.5-Visibility-E2E-Journeys.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 4: Playwright journey per role; FC-2 unauthorized-access checks; SC-1/SC-3 dashboard)
**Wave**: 13
**Requires**: [5.2, 6.4, 7.2, 7.3, 7.4]
**Enables**: []
**Files Touched**:
  - tests/e2e/test_progress_visibility.py
  - tests/e2e/test_pilot_metrics.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation in *this story's code* (test-only; exercises Student, Parent/Guardian, Teacher and Admin visibility from 7.2–7.4 and 5.2)
**QA Candidate**: No — test-only story. It automates Epic 7 Group 1 and Epic 5 Group 2; its green run is the CYCLE-3 sign-off evidence for FC-2 ("unauthorized access to another user's data") and SC-1/SC-3 reporting.

---

#### 👤 User Reference

**Description**:
Browser "robot" tests that sign in as each kind of user and check that everyone sees exactly what they should, and nothing more:
- **Student:** sees their own progress and score, and nothing of a classmate's.
- **Parent:** sees their own child's page; trying another child's address shows "Page not found".
- **Teacher and administrator:** see everyone's scores.
- **Blocked tests:** after a test is blocked, already-earned scores still appear everywhere.
- **Pilot page:** the administrator's Pilot page counts the onboarded accounts and the students who've taken a test correctly.

**Acceptance Criteria** (plain-English):
- One command runs the visibility journeys in a real browser.
- Each role sees exactly its own allowed data; cross-student and cross-family attempts show "Page not found" or "Access denied".
- A score earned before a test was blocked remains visible to the student, the linked parent, teachers and administrators.
- The Pilot page shows the correct onboarding and test-completion numbers.
- No browser security-policy errors occur.

**User Flow**:
Actor: system — no role variation.

**Flow Diagram**:

```mermaid
flowchart TD
  A[seed: MEM ch.1 complete; students Ana (score 80) + Ion (none); parent linked to Ana; 2nd parent unlinked] --> B[Ana: My progress shows 80; no Ion data]
  B --> C[Parent: My children → Ana 80; /children/Ion/progress/ → Page not found]
  C --> D[Teacher + Admin: Scores shows Ana 80, Ion —]
  D --> E[Block the test (DB) → scores still visible in all views]
  E --> F[Admin Pilot: onboarding counts + 1 of N students tested]
```

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/plans/implementation-plan.md` — Epic 7 Group 1, Epic 5 Group 2
- `docs/plans/stories/epic-1-story-1.10-Foundation-E2E-Journeys.md` — harness rules
- Stories 7.2, 7.3, 7.4, 5.2 — labels and messages

**Description**:
- `tests/e2e/test_progress_visibility.py`: `test_student_sees_only_own_progress`, `test_parent_sees_only_linked_child`, `test_staff_see_all_scores`, `test_blocked_test_scores_remain_visible`, all on a module-local factory seed.
- `tests/e2e/test_pilot_metrics.py`: `test_admin_sees_onboarding_and_completion_counts`.

**Acceptance Criteria**:
1. Both files are green three times in a row, in < 2 min total.
2. Student journey: "My progress" shows "Score: 80 out of 100" for MEM chapter 1. The page doesn't contain Ion's name. `/en/scores/` → "Access denied".
3. Parent journey: "My children" lists Ana only. Her page shows the score. Navigating to Ion's progress URL shows "Page not found". `/en/scores/` → "Access denied".
4. Staff journeys: Teacher and Admin "Scores" show Ana 80 and Ion "—" (by accessible label "Not taken").
5. After `ChapterTestModel` is set to BLOCKED (test setup via the ORM), the score still appears for the student, the parent and the staff views.
6. Pilot metrics: with 2 active students, 1 teacher (fixture) and 1 linked parent, the Pilot page shows the onboarding numbers against the targets and "1 of 2 students have taken a chapter test" (target 8 of 10), using the Story 5.2 wording.
7. `console_errors` used everywhere; no `time.sleep`.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- Test-only; signs in as each role via the real login page.

**System responses + error cases** (harness behaviour):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| `uv run pytest` | e2e deselected | none |
| `-m e2e` | journeys run | transactional DB discarded |
| Assertion failure | trace + screenshot | artefacts |
| CSP console error | test fails | none |

**Prerequisites**:
- Stories 5.2, 6.4, 7.2, 7.3 and 7.4 merged; Chromium installed.

**Context**: `tests/e2e/conftest.py`, `tests/factories/*`

**Patterns**: E2E tests (§12.5) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Seed fixture** (factories: `complete_chapter`, `attempt_for(ana, test, {1..8})`, `ParentChildLinkFactory(parent, ana)`), then the journeys (excerpt):
   ```python
   def test_parent_sees_only_linked_child(page: Page, base_url, console_errors, seeded):
       ana, ion, parent = seeded["ana"], seeded["ion"], seeded["parent"]
       login(page, base_url, parent.username, lang="en")

       page.get_by_role("navigation", name="Main").get_by_role("link", name="My children").click()
       expect(page.get_by_role("link", name="View progress")).to_have_count(1)
       page.goto(f"{base_url}/en/children/{ion.pk}/progress/")

       expect(page.get_by_role("heading", name="Page not found")).to_be_visible()
   ```
   All AC steps are implemented explicitly in the final files.
2. **Run three times**; one deliberate local failure; revert.

**Tests**: this story *is* tests (3 green runs + deliberate failure).

Manual: one `--headed` run.

**Quality**: ruff 0; role/label/text locators; no `time.sleep`; 3 green runs.

**OUT**:
- ❌ Test-taking (6.6) and moderation (8.6) journeys.
- ❌ Production-code changes.

**Evidence**: 3-run output, AC → step table, deliberate-failure trace, all recorded in `docs/stories-implemented/story-7.5-review.md` under "## DoD Evidence".
