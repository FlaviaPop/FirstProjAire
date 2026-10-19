# Cycle Plan — Assessment, Moderation & Visibility

**Cycle ID**: cycle-3
**BUILDID**: CYCLE-3
**Dates**: 2026-11-06 → 2026-11-14
**Expected Outcome**: Every required role workflow works end to end (FC-2). Students take each chapter test once and see only their final score (1–100). Parents see only their linked children's progress and scores. Teachers and Admins see all pilot scores. The Admin flags, blocks and clears content, with teachers notified in-app and able to resubmit. The pilot dashboard reports SC-1 and SC-3.

---

## Scope

### In Scope (this cycle)

Epic and story numbers are proposed here. `aire-greenfield-plan` finalises the stories and tags each one with `BUILDID: CYCLE-3`.

- **Epic 6 — Chapter Tests & Scoring**
  - `AnswerChecker` (MCQ, TRUE_FALSE, NUMERIC with Decimal equality accepting `.`/`,`), `compute_score` (`max(1, Σ correct points)`)
  - `SubmitTest` use case: one transaction, `UNIQUE(student, test)`, `AlreadySubmitted` → 409, attempt answers stored and never shown to students
  - Student test page (PUBLISHED + ACTIVE only), confirm dialog for unanswered questions, button spinner/disable, result page with final score only
  - `ScoringLockPolicy`: after the first attempt, answer keys, points, kinds and the question set are frozen; wording and typo fixes still allowed
- **Epic 7 — Progress & Score Visibility**
  - Student `/me/progress/` (per chapter: lesson opened, exercises n/visible, test status + score)
  - Parent `/children/` and `/children/<id>/progress/`; unlinked child → 404
  - Teacher/Admin `/scores/` (all pilot students)
  - Scores of a blocked test stay visible (user decision)
- **Epic 8 — Content Moderation & Notifications**
  - `ModerationStateMachine` (ACTIVE ⇄ FLAGGED, → BLOCKED with reason, BLOCKED → RESUBMITTED → ACTIVE / BLOCKED)
  - Admin moderation queue and actions; teacher resubmit; FLAGGED/BLOCKED/RESUBMITTED hidden from students and parents immediately
  - In-app notifications to creator and last editor on every block; unread badge; mark as read
  - `MODERATION_EVENT` + `AUDIT_LOG` in the same transaction
- **Epic 5 — Pilot Reporting (part 2)**
  - `/manage/pilot/` onboarding counts (SC-1: 10 students, 2 teachers) and test completion (SC-3: ≥8 of 10 students submitted ≥1 chapter test)
- **End-to-end:** Playwright journey per role covering all FC-2 workflows

### Deferred to Next Cycle

- None for the pilot. Post-pilot items (additional grades and subjects, mobile/tablet, lesson images) remain Future Considerations in `docs/requirements.md`.

---

## Workshop Plan (4 half-days)

**Day 1**: Test taking and scoring
→ Goal: answer checking + scoring at 100% domain coverage; submission with a single attempt (including a concurrent double-submit test); result page; scoring lock.

**Day 2**: Progress and score visibility
→ Goal: student, parent and teacher/admin progress and score pages with record scoping (403/404 matrix tests extended).

**Day 3**: Moderation and notifications
→ Goal: full state machine, admin queue and actions, teacher resubmit, notifications with unread badge, audit/events; hidden content verified on every learner route.

**Day 4**: Pilot metrics, E2E, review
→ Goal: SC-1/SC-3 dashboard counts; four role journeys green in Playwright; demo and sign-off for the launch buffer.

Each day ends with **production-ready, deployable code**. No partial or broken states overnight.

---

## Acceptance Criteria

- A test whose answers are all incorrect scores 1; a perfect test scores 100; `2`, `2.0` and `2,0` are equal for numeric questions; the student never sees per-question correctness.
- A second submission (sequential or concurrent) is rejected with 409 and leaves exactly one attempt.
- Changing answer keys or points on an attempted test is refused; typo fixes to prompts succeed.
- A parent opening an unlinked child's progress gets 404; a student cannot reach another student's data.
- Flagging, blocking or resubmitting hides the item from students and parents on the next request; blocking requires a reason and notifies the teacher(s) in-app; only Admin can clear a resubmission.
- Every illegal moderation transition returns 409; every transition is written to `MODERATION_EVENT` and `AUDIT_LOG`.
- The pilot dashboard reports onboarding (SC-1) and test completion (SC-3) correctly.
- Playwright journeys for Student, Teacher, Parent and Admin pass; all quality gates green.

## Open Items

| Item | Owner |
| ---- | ----- |
| Production environment ready (single instance, persistent encrypted volume, nightly `.backup`, restore tested) before 2026-11-15 | DEVOPS |
| SC-4 feedback collection method (outside the app) prepared for pilot | Project team |
| GDPR/consent handling for minors' data (architecture risk R1) resolved before onboarding students | Project owner |

## Prerequisites

- CYCLE-2 complete and signed off (content models, authoring, learner flow)
- Some real or sample chapter content entered for realistic testing

---

## After CYCLE-3 — Launch Buffer (2026-11-15 → 2026-11-19, not a build cycle)

- User acceptance testing with teachers and admin; bug fixes only (no new scope)
- Content completeness check: all 9 chapters pass the readiness dashboard (FC-1)
- Production deploy, account onboarding (10 students, 2 teachers, linked parents), launch on 2026-11-19
