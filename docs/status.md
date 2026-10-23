# Project Status

**Last Updated**: 2026-10-23 10:36
**Last Updated**: 2026-10-21 12:30
**Updated By**: DEV
**Overall Status**: 🟡 IN PROGRESS

---

## Project Overview

**Project**: Romanian Curriculum Learning Platform (Working Title)
**Type**: Greenfield
**Start Date**: 2026-10-19
**Target Completion**: 2026-11-19
**Active Cycle**: CYCLE-1

---

## Progress Summary

| Step | Status | Owner | Updated | Evidence | Recorded |
|------|--------|-------|---------|----------|----------|
| Requirements | ✅ Done | AIRE_ANALYST_PM_GREENFIELD | 2026-10-19 | `docs/requirements.md` | 2026-10-19 11:24 |
| Architecture | ✅ Done | AIRE_ARCHITECT | 2026-10-19 | `docs/architecture/design/00-system-architecture-greenfield.md` | 2026-10-19 14:10 |
| Patterns | ✅ Done | AIRE_ARCHITECT | 2026-10-19 | `docs/architecture/design/01-patterns-and-standards-greenfield.md` | 2026-10-19 14:34 |
| UI/UX Design | ✅ Done | AIRE_UI_UX_DESIGNER | 2026-10-19 | `docs/ui-ux/ui-ux-spec.md` | 2026-10-19 14:56 |
| Build Cycles | ✅ Done | AIRE_BUILD_CYCLE_PLANNER | 2026-10-19 | `docs/plans/builds/` · `docs/plans/build-cycles.md` | 2026-10-19 14:45 |
| Implementation Plan | ✅ Done | AIRE_PRODUCT_OWNER | 2026-10-19 | `docs/plans/implementation-plan.md` — all 3 cycles planned (45 stories) | 2026-10-19 19:23 |
| Epic 1: Foundation | 🟡 In Progress | AIRE_DEV | 2026-10-22 | 10/11 stories done (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9) | 2026-10-23 09:33 |
| Epic 2: Grade & Subject Catalogue | ✅ Done | AIRE_DEV | 2026-10-21 | 2/2 stories done (2.1, 2.2) | 2026-10-23 10:36 |
| Epic 3: Teacher Content Authoring | ⏸️ Not Started | — | — | 0/9 stories done | 2026-10-19 18:44 |
| Epic 4: Student Lessons & Practice | ⏸️ Not Started | — | — | 0/4 stories done | 2026-10-19 18:44 |
| Epic 5: Pilot Reporting | ⏸️ Not Started | — | — | 0/2 stories done (5.1 CYCLE-2, 5.2 CYCLE-3) | 2026-10-19 19:23 |
| Epic 6: Chapter Tests & Scoring | ⏸️ Not Started | — | — | 0/6 stories done | 2026-10-19 19:23 |
| Epic 7: Progress & Score Visibility | ⏸️ Not Started | — | — | 0/5 stories done | 2026-10-19 19:23 |
| Epic 8: Content Moderation & Notifications | ⏸️ Not Started | — | — | 0/6 stories done | 2026-10-19 19:23 |
| Review | 🟡 In Progress | AIRE_REVIEWER | 2026-10-22 | `docs/reviews/` — 11/45 stories reviewed (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1) | 2026-10-23 09:36 |
| QA | 🟡 In Progress | AIRE_QA | 2026-10-21 | `docs/testing/regression-report-2026-10-21.md` — 🟢 no regressions (605/605); all triaged bugs fixed | 2026-10-21 16:50 |

---

## Project Tracking

**Tracking**: Local

---

## Current Step Details

### Implementation — CYCLE-1

**Owner**: AIRE_DEV
**Status**: 🟡 In Progress
**Started**: 2026-10-21

**Progress**:
- [x] Story 1.0 Root Tooling Seed (wave 1, Dev 1): 28/28 tests, 100% coverage, all gates green ✅ (commit `26b4ece`, merged to `main` @ `2c24482`)
- [x] Story 1.0 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 2 🟡 · 5 🟢 (`docs/reviews/story-1.0-code-review-v1.md`)
- [x] Remediation from `story-1.0-code-review-v1.md`: 5 issues fixed (2 🟡, 3 🟢), 2 🟢 deferred (ISS-004 → DevOps, ISS-005 → Story 1.1)
- [x] QA test plan, scope story 1.0: `docs/testing/test-plan-story-1.0.md` (31 scenarios; 15/15 AC + 5 requirement rows traced)
- [x] QA validation of story 1.0: 🟢 PASS at commit `26b4ece`. 30/30 tests, 100% coverage, 20/20 requirements covered; BUG-001 🟢 Low (healthz logs wrong cause for read-only data dir), non-blocking (`docs/testing/validation-report-story-1.0-2026-10-21.md`)
- [x] Bug triage: 1 bug (BUG-001 🟢 Low / P3), 0 release blockers. Recommendation: approve merge; fix with Story 1.1 (`docs/testing/bug-triage-2026-10-21.md`)
- [x] Wave 2 Dev 1 (in one go, 4 isolated worktrees): 2.1, 1.5, 1.2, 1.1 implemented and merged into `feature/wave-2-dev-1` (2.1 → 1.5 → 1.2 → 1.1); 500/500 tests, coverage 100%, all gates green
- [x] Story 2.1 AC 10 owner decision (2026-10-21): 10 levels — Grădiniță (K, 5 experiential domains), Clasa pregătitoare (P), grades 1–8; subject lists confirmed
- [x] Story 1.3 RBAC Core (wave 2, Dev 2, one-by-one): 85/85 tests on its branch, coverage 100% (domain 100%), all gates green
- [x] Story 1.3 (Dev 2) committed and merged into `feature/wave-2-dev-1`; fixture stand-ins removed (1.2's conftest fixtures used); 555/555 tests
- [x] Docs updated for the 2.1 owner decision: stories 2.1 and 2.2 (10 levels, K = Grădiniță, P = Clasa pregătitoare, 111 subjects); notes in requirements, architecture and implementation plan
- [x] Story 1.8 Audit Log (Dev 2, one-by-one): 592/592 tests, coverage 100% (application 100%), all gates green — branch `feature/story-1.8-audit-log` (not merged yet)
- [x] Story 1.3 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 4 🟢 (`docs/reviews/story-1.3-code-review-v1.md`)
- [x] Story 1.8 merged into `feature/wave-2-dev-1` (`fb28aab`)
- [x] Remediation from `story-1.3-code-review-v1.md`: 4 issues fixed (1 🟡, 3 🟢), 1 🟢 deferred (ISS-004 → Story 1.6); 598/598 tests
- [x] Bug triage #2: BUG-002 🟡 P2 (`/healthz` 500 with session cookie when DB unusable), BUG-003 🟡 P2 (CSRF failures show Django's default page), BUG-001 🟢 P3 still open; all reproduced by QA; 0 blockers (`docs/testing/bug-triage-2026-10-21-2.md`)
- [x] Remediation from `bug-triage-2026-10-21-2.md` + Story 1.0 review ISS-005: BUG-002, BUG-003, BUG-001, ISS-005 fixed (+ test language-leak isolation fix); 605/605 tests; verified on a real server
- [x] QA regression vs Story 1.0 baseline: 🟢 NO REGRESSIONS — 605/605 ×4 runs (incl. reverse order), 30/30 surviving baseline cases, 15/15 manual scenarios (`docs/testing/regression-report-2026-10-21.md`)
- [x] Story 1.4 Internationalization (Dev 2, one-by-one): 659/659 tests, coverage 100%, all gates green; GNU gettext installed (user-space micromamba); branch `feature/story-1.4-i18n` → **wave 2 complete (7/7)**
- [x] Story 1.2 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 4 🟢 (`docs/reviews/story-1.2-code-review-v1.md`)
- [x] Story 1.4 merged into `feature/wave-2-dev-1` (`a5ce928`): wave 2 fully integrated
- [x] Remediation from `story-1.2-code-review-v1.md`: 4 fixed (1 🟡, 3 🟢), ISS-005 deferred to DevOps; 677/677 tests
- [x] Wave 2 pushed to `origin/main` (`1547237`); all story/worktree branches deleted (local + remote), only `main` remains
- [x] Story 1.8 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 3 🟢 (`docs/reviews/story-1.8-code-review-v1.md`)
- [x] Remediation from `story-1.8-code-review-v1.md`: ISS-001 (metadata guard), ISS-002 (SQLite append-only triggers), ISS-003 (owner decision: failed sign-ins store only real usernames, else a keyed fingerprint); ISS-004 → DevOps; 717/717 tests
- [x] Story 1.1 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 3 🟢 (`docs/reviews/story-1.1-code-review-v1.md`)
- [x] Remediation from `story-1.1-code-review-v1.md`: ISS-001 (shared redaction rule for logs + audit), ISS-002 (missing message param no longer 500s), ISS-003 (binding hand-off in Story 1.7); ISS-004 → DevOps; 744/744 tests
- [x] Story 1.4 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 2 🟢 (`docs/reviews/story-1.4-code-review-v1.md`)
- [x] Remediation from `story-1.4-code-review-v1.md`: ISS-001 (`next` must be a same-site absolute path; no URL-name resolution), ISS-002 (DB-failure test), ISS-003 (`icon_variant`; 1.7 hand-off); 757/757 tests
- [x] Story 1.5 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 2 🟢 (`docs/reviews/story-1.5-code-review-v1.md`)
- [x] Remediation from `story-1.5-code-review-v1.md`: ISS-001 (whole-number check for score/badge/progress), ISS-002 (`value=0` kept), ISS-003 (HTMX `js:` paths refused); 782/782 tests
- [x] Story 2.1 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 2 🟢 (`docs/reviews/story-2.1-code-review-v1.md`) — all implemented stories now reviewed
- [x] Remediation from `story-2.1-code-review-v1.md`: ISS-001 (factories: sequenced `sort_order`, inactive by default), ISS-002 (`__str__` by grade code), ISS-003 (non-empty name check constraints, migration `0003_name_not_empty`); 787/787 tests
- [x] Wave 3 Dev 1 (in one go: decompose-lead → 3 component workers → integrator, worktree `feature/story-1.6-molecules`): Story 1.6 Molecule Primitives + 1.3 review ISS-004; 980/980 tests, coverage 100%, 14/14 AC, DoD gates passed; merged to `main` @ `3cf8fa9` (fast-forward). Owner decision: base.html links the component CSS now
- [x] Story 1.6 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 2 🟢 (`docs/reviews/story-1.6-code-review-v1.md`)
- [x] Remediation from `story-1.6-code-review-v1.md`: ISS-001 (choice groups as fieldset/legend, `auto_id`-based ids, fail loudly without ids), ISS-002 (focus to `<main>` before alert removal; 1.10 hand-off), ISS-003 (card heading level; molecule tags moved to `ui_molecules.py`); 1001/1001 tests
- [x] Fix: mypy error from the 1.6 remediation (`ui_molecules.py:72`), caught by the 1.9 build; erratum in `story-1.6-code-review-v1.md` (`1cb6215`)
- [x] Wave 3 Dev 2 (in one go, atomic story-agent, worktree `feature/story-1.9-admin-accounts`): Story 1.9 Admin Accounts & Parent–Child Links; 1273/1273 tests, coverage 100%, 15/15 AC, DoD gates passed; merged to `main` @ `61ce5aa`. Owner decisions: role change → 2 audit rows; lockout-cleared target = user id or `(unknown):<fingerprint>`; parent guard message (7 messages); last active Admin can't be deleted → **wave 3 complete (2/2)**
- [x] Story 1.9 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 1 🟢 (`docs/reviews/story-1.9-code-review-v1.md`)
- [x] Remediation from `story-1.9-code-review-v1.md`: ISS-001 (owner decisions recorded in the story file; AC 2/4/10/15 + response rows + QA note amended), ISS-002 (lockout list masks typed text for non-accounts); 1278/1278 tests
- [x] Story 1.7 App Shell & Role Homes (wave 4, Dev 1, one-by-one): full layout (htmx 2.0.11 vendored, CSP-safe), role menus from `NAV_BY_ROLE`, role homes, db-safe shell (1.1 ISS-003), `/` redirect tests (1.4), switcher in the top bar (1.4); 1344/1344 tests, coverage 100%. Owner decision 2026-10-23: error pages may set `csrftoken` (never a session)
- [x] Story 1.7 code review v1: ⚠️ APPROVED WITH COMMENTS — 0 🔴 · 0 🟠 · 1 🟡 · 2 🟢 (`docs/reviews/story-1.7-code-review-v1.md`; same-session review, independence note in the report)
- [x] Remediation from `story-1.7-code-review-v1.md`: ISS-001 (`scroll-padding-top` for the sticky bar; 1.10 browser hand-off), ISS-002 (whitespace-safe greeting), ISS-003 (no empty nav landmark); 1350/1350 tests
- [x] Wave 4 Dev 2 (in one go, atomic story-agent, worktree `feature/story-2.2-catalogue`): Story 2.2 Catalogue & Subject Pages; 1486/1486 tests, coverage 100%, 12/12 AC, DoD gates passed; merged to `main` @ `415e3eb` → **wave 4 complete (2/2)**; Epic 2 done; Student "Learn" entry now live

### Implementation Plan

**Owner**: AIRE_PRODUCT_OWNER
**Status**: ✅ Done
**Started**: 2026-10-19

**Progress**:
- [x] Numbering confirmed (Epic 1, Story 1.0 seed) ✅
- [x] CYCLE-1 scoped; team_size 2 ✅
- [x] Dependency graph: 13 stories, 5 waves, shared_files confirmed (`docs/plans/dependency-graph.yml`) ✅
- [x] Wave workload distribution accepted (2 devs) ✅
- [x] Plan index approved (`docs/plans/implementation-plan.md`) ✅
- [x] All 13 CYCLE-1 story files written and validated (headers mirror the graph) ✅
- [ ] Tracker export decision (keep Local / GitHub Projects / Azure DevOps)
- [x] CYCLE-2 planned: numbering Epic 3 / Story 3.1, team_size 3, waves 6–9 confirmed, index approved, 14 story files written and validated ✅
- [x] CYCLE-3 planned: Epics 6–8 + Story 5.2, team_size 3, waves 10–13 confirmed, index approved, 18 story files written and validated ✅

**Epics & story counts**: CYCLE-1 — Epic 1 Foundation 11 (1.0–1.10) · Epic 2 Catalogue 2 (2.1–2.2) · CYCLE-2 — Epic 3 Teacher Content Authoring 9 (3.1–3.9) · Epic 4 Student Lessons & Practice 4 (4.1–4.4) · Epic 5 Pilot Reporting 1 (5.1) · CYCLE-3 — Epic 6 Chapter Tests & Scoring 6 (6.1–6.6) · Epic 7 Progress & Score Visibility 5 (7.1–7.5) · Epic 8 Moderation & Notifications 6 (8.1–8.6) · Epic 5 part 2: 5.2

---

## Build Cycles

| Cycle | BUILDID | Scope | Stories | Status | Start | End | Recorded |
|-------|---------|-------|---------|--------|-------|-----|----------|
| Cycle 1 | CYCLE-1 | Foundation & Access (Epics 1–2) | 8/13 | 🟡 In Progress | 2026-10-21 | — | 2026-10-22 14:30 |
| Cycle 2 | CYCLE-2 | Content Authoring & Learning (Epics 3–4, 5 part 1) | 0/14 | ⏸️ Not Started | — | — | 2026-10-19 18:44 |
| Cycle 3 | CYCLE-3 | Assessment, Moderation & Visibility (Epics 6–8, 5 part 2) | 0/18 | ⏸️ Not Started | — | — | 2026-10-19 19:23 |

_Stories `X/N` column is advisory after parallel merges; compute from Story Tracker._

---

## Story Tracker

| BUILDID | Story | Title | Start | End | Recorded |
|---------|-------|-------|-------|-----|----------|
| CYCLE-1 | 1.0 | Root Tooling Seed | 2026-10-21 | 2026-10-21 (remediation started and finished 2026-10-21) | 2026-10-21 11:20 |
| CYCLE-1 | 1.1 | Error Handling & Observability | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-22) | 2026-10-22 15:03 |
| CYCLE-1 | 1.2 | Login & Session Security | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-22) | 2026-10-22 14:40 |
| CYCLE-1 | 1.3 | RBAC Core | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-21) | 2026-10-21 16:35 |
| CYCLE-1 | 1.4 | Internationalization | 2026-10-21 | 2026-10-22 (review v1 remediated 2026-10-22) | 2026-10-22 15:15 |
| CYCLE-1 | 1.5 | Design Tokens & Atom Primitives | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-22) | 2026-10-22 15:22 |
| CYCLE-1 | 1.6 | Molecule Primitives | 2026-10-22 | 2026-10-22 (review v1 remediated 2026-10-22) | 2026-10-22 17:01 |
| CYCLE-1 | 1.7 | App Shell & Role Homes | 2026-10-23 | 2026-10-23 (review v1 remediated 2026-10-23) | 2026-10-23 09:44 |
| CYCLE-1 | 1.8 | Audit Log | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-22) | 2026-10-22 14:55 |
| CYCLE-1 | 1.9 | Admin Account Management & Parent–Child Links | 2026-10-22 | 2026-10-22 (review v1 remediated 2026-10-23) | 2026-10-23 09:13 |
| CYCLE-1 | 1.10 | Foundation E2E Journeys | — | — | 2026-10-19 16:35 |
| CYCLE-1 | 2.1 | Catalogue Data | 2026-10-21 | 2026-10-21 (review v1 remediated 2026-10-22) | 2026-10-22 16:11 |
| CYCLE-1 | 2.2 | Catalogue & Subject Pages | 2026-10-23 | 2026-10-23 | 2026-10-23 10:36 |
| CYCLE-2 | 3.1 | Content Domain Rules | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.2 | Content Data Model | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.3 | Markdown Rendering | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.4 | Authoring Web Kit | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.5 | Teacher Dashboard & Chapters | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.6 | Lesson Editor | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.7 | Exercise Editor | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.8 | Test Editor & Publishing | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 3.9 | Authoring E2E Journeys | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 4.1 | Progress Data & Use Cases | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 4.2 | Chapter List & Lesson Reading | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 4.3 | Exercise Practice | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 4.4 | Learning E2E Journeys | — | — | 2026-10-19 18:44 |
| CYCLE-2 | 5.1 | Pilot Readiness Dashboard | — | — | 2026-10-19 18:44 |
| CYCLE-3 | 5.2 | Pilot Onboarding & Completion Metrics | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.1 | Assessment Domain Rules | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.2 | Assessment Data Model | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.3 | Test Submission | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.4 | Student Test Page & Result | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.5 | Scoring Lock in the Test Editor | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 6.6 | Test-Taking E2E Journeys | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 7.1 | Progress Read Models & Web Scaffold | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 7.2 | My Progress | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 7.3 | Parent Children Pages | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 7.4 | Scores List | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 7.5 | Visibility E2E Journeys | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.1 | Moderation Domain Rules | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.2 | Moderation & Notification Data | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.3 | Moderation Use Cases | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.4 | Admin Moderation Queue & Actions | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.5 | Teacher Notifications & Resubmit | — | — | 2026-10-19 19:23 |
| CYCLE-3 | 8.6 | Moderation E2E Journeys | — | — | 2026-10-19 19:23 |

---

## Quality Metrics

| Metric | Target | Current | Status | Recorded |
|--------|--------|---------|--------|----------|
| Unit Test Coverage | ≥85% | 100% (domain 100%, application 100%) | ✅ | 2026-10-22 16:52 |
| Integration Tests | 100% pass | 100% (1486/1486 on `main`) | ✅ | 2026-10-23 10:36 |
| Code Review | All stories | 11/45 | 🟡 | 2026-10-23 09:36 |
| Documentation | All stories | 12/45 | 🟡 | 2026-10-23 10:36 |

---

## Completed Steps

- [x] **Requirements**: Done — 2026-10-19
  - Evidence: `docs/requirements.md`
- [x] **Architecture**: Done — 2026-10-19
  - Evidence: `docs/architecture/design/00-system-architecture-greenfield.md`
- [x] **Patterns**: Done — 2026-10-19
  - Evidence: `docs/architecture/design/01-patterns-and-standards-greenfield.md`
- [x] **UI/UX Design**: Done — 2026-10-19
  - Evidence: `docs/ui-ux/ui-ux-spec.md`
- [x] **Build Cycles**: Done — 2026-10-19
  - Evidence: `docs/plans/build-cycles.md`, `docs/plans/builds/cycle-1/cycle-plan.md`, `docs/plans/builds/cycle-2/cycle-plan.md`, `docs/plans/builds/cycle-3/cycle-plan.md`
- [x] **Implementation Plan — CYCLE-1 (13 stories)**: Done — 2026-10-19
  - Evidence: `docs/plans/implementation-plan.md`, `docs/plans/dependency-graph.yml`, `docs/plans/stories/` (13 files)
- [x] **Implementation Plan — CYCLE-2 (14 stories)**: Done — 2026-10-19
  - Evidence: `docs/plans/implementation-plan.md` (Epics 3–5, waves 6–9), `docs/plans/dependency-graph.yml`, `docs/plans/stories/` (14 files)
- [x] **Implementation Plan — CYCLE-3 (18 stories)**: Done — 2026-10-19
  - Evidence: `docs/plans/implementation-plan.md` (Epics 5–8, waves 10–13), `docs/plans/dependency-graph.yml`, `docs/plans/stories/` (18 files)
- [x] **Story 1.0 Root Tooling Seed**: Done — 2026-10-21
  - Evidence: `docs/stories-implemented/story-1.0-review.md` — 28/28 tests passed (7 unit, 21 integration), coverage 100%, ruff/mypy/import-linter/makemigrations clean. Deviation: production POST /healthz → 403 (CSRF), accepted by user.
- [x] **Code Review — Story 1.0 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-21
  - Evidence: `docs/reviews/story-1.0-code-review-v1.md` — gates re-run by reviewer (28/28, 100%); 0 blockers, 0 high, 2 medium (self-review evidence count, AC 9 contract text), 5 low
- [x] **Remediation — Story 1.0 (review v1)**: 🟡 Partially Remediated (5/7) — 2026-10-21
  - Evidence: `docs/reviews/story-1.0-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 30/30 tests (7 unit, 23 integration), coverage 100%, ruff/mypy/import-linter/makemigrations clean; ISS-004 deferred to DevOps, ISS-005 to Story 1.1
- [x] **QA Validation — Story 1.0**: 🟢 PASS — 2026-10-21
  - Evidence: `docs/testing/validation-report-story-1.0-2026-10-21.md` — commit `26b4ece`; 7/7 unit, 23/23 integration, coverage 100%, 4 stable runs, all gates green; 31/31 scenarios executed; BUG-001 🟢 Low open
- [x] **Story 1.3 RBAC Core**: Done — 2026-10-21
  - Evidence: `docs/stories-implemented/story-1.3-review.md` — 85/85 tests (36 unit, 49 integration), coverage 100%, `src/domain` 100%, ruff/mypy/import-linter/makemigrations clean

- [x] **Wave 2 — Dev 1 (2.1, 1.5, 1.2, 1.1)**: Done — 2026-10-21
  - Evidence: `docs/stories-implemented/story-2.1-review.md` (76/76, 10/10 AC), `story-1.5-review.md` (222/222, 10/10 AC), `story-1.2-review.md` (134/134, 15/15 AC), `story-1.1-review.md` (158/158, 16/16 AC); merged suite 500/500, coverage 100%; integration fix `AXES_VERBOSE = False`
- [x] **Story 1.8 Audit Log**: Done — 2026-10-21
  - Evidence: `docs/stories-implemented/story-1.8-review.md` — 592/592 tests (78 unit, 514 integration; 37 new), coverage 100%, `src/application` 100%, ruff/mypy/import-linter/makemigrations clean; manual audit_log SELECT recorded
- [x] **Code Review — Story 1.3 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-21
  - Evidence: `docs/reviews/story-1.3-code-review-v1.md` — 73/73 story tests + 592/592 suite re-run by reviewer; 0 blockers, 0 high, 1 medium (typo'd permission keys accepted at decoration), 4 low
- [x] **Remediation — Story 1.3 (review v1)**: 🟡 Partially Remediated (4/5) — 2026-10-21
  - Evidence: `docs/reviews/story-1.3-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 598/598 tests, coverage 100%, all gates clean; ISS-004 deferred to Story 1.6
- [x] **Remediation — bug triage #2 + 1.0 ISS-005**: ✅ Resolved — 2026-10-21
  - Evidence: `docs/testing/bug-triage-2026-10-21-2.md` (banner, per-bug resolutions, Remediation Section with real-server re-run), `docs/reviews/story-1.0-code-review-v1.md` (second pass) — 605/605 tests, coverage 100%, all gates clean
- [x] **QA Regression — wave-2 integration vs Story 1.0 baseline**: 🟢 NO REGRESSIONS — 2026-10-21
  - Evidence: `docs/testing/regression-report-2026-10-21.md` — clean env, 605/605 in 4 runs, coverage 100%, gates clean; expected changes: Argon2 hashes, localized CSRF 403 page, BUG-001 fixed
- [x] **Story 1.4 Internationalization**: Done — 2026-10-22
  - Evidence: `docs/stories-implemented/story-1.4-review.md` — 659/659 tests (98 unit, 561 integration; 52 new), coverage 100%, application/domain 100%, ruff/mypy/import-linter/makemigrations clean; makemessages/compilemessages output; real-server RO/EN + preference journey. Hand-off: `/` → `/<lang>/` tests to Story 1.7
- [x] **Code Review — Story 1.2 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.2-code-review-v1.md` — 102/102 story tests + 659/659 suite re-run; open-redirect/XSS/enumeration probes clean; 1 medium (templates bypass UI primitives), 4 low (incl. password-spraying design note for DevOps)
- [x] **Remediation — Story 1.2 (review v1)**: 🟡 Partially Remediated (4/5) — 2026-10-22
  - Evidence: `docs/reviews/story-1.2-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 677/677 tests, coverage 100%, gates clean; real-server RO/EN check; ISS-005 deferred to DevOps
- [x] **Code Review — Story 1.8 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.8-code-review-v1.md` — 37/37 story tests + 677/677 suite re-run on `main`; probes: metadata guard misses case/prefix variants (ISS-001 🟡), `_base_manager` bypass (ISS-002 🟢), verbatim failed usernames (ISS-003 🟢, needs product decision), audit growth under attack (ISS-004 🟢, DevOps)
- [x] **Remediation — Story 1.8 (review v1)**: 🟡 Partially Remediated (3/4) — 2026-10-22
  - Evidence: `docs/reviews/story-1.8-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 717/717 tests, coverage 100%, gates clean; real server + sqlite3 CLI checks; owner decision recorded in Story 1.8 and the architecture
- [x] **Code Review — Story 1.1 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.1-code-review-v1.md` — 114/114 story tests + 717/717 suite re-run; probes: JSON formatter serialises password/DOB/full_name extras (ISS-001 🟡), missing violation param → 500 (ISS-002 🟢); notes for Story 1.7 (ISS-003) and DevOps (ISS-004)
- [x] **Remediation — Story 1.1 (review v1)**: 🟡 Partially Remediated (3/4) — 2026-10-22
  - Evidence: `docs/reviews/story-1.1-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 744/744 tests, coverage 100%, gates clean; real-server check (CSRF reason kept, posted password in 0 log lines)
- [x] **Code Review — Story 1.4 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.4-code-review-v1.md` — 744/744 suite re-run, coverage 100%, gates clean; 13/13 AC (AC 2 `/` case handed off to 1.7); probes: bare/relative `next` on an invalid code → 500 (ISS-001 🟡), signed-in switch = one scoped UPDATE; DB-failure row untested (ISS-002 🟢), student duotone icon (ISS-003 🟢)
- [x] **Remediation — Story 1.4 (review v1)**: ✅ Resolved (3/3) — 2026-10-22
  - Evidence: `docs/reviews/story-1.4-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 757/757 tests, coverage 100%, gates clean; real server: bare `next` → `302 /<lang>/`, 0 ERROR lines
- [x] **Code Review — Story 1.5 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.5-code-review-v1.md` — 192/192 UI tests + 757/757 suite re-run, coverage 100%, gates clean; 10/10 AC (AC 5 partial); probes: numeric atoms truncate 87.6 → 87 and accept 100.4 (ISS-001 🟡), `ui_button value=0` dropped (ISS-002 🟢), `hx_vals='js:…'` passes (ISS-003 🟢, neutralised by CSP)
- [x] **Remediation — Story 1.5 (review v1)**: ✅ Resolved (3/3) — 2026-10-22
  - Evidence: `docs/reviews/story-1.5-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 782/782 tests, coverage 100%, gates clean; styleguide 200 in RO/EN on a real dev server, 0 ERROR lines
- [x] **Code Review — Story 2.1 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-2.1-code-review-v1.md` — 46/46 catalogue tests + 782/782 suite re-run, coverage 100%, gates clean; seed recounted (10 levels, 111 subjects) against the owner-confirmed tables; probes: factories collide on `sort_order` for new codes (ISS-001 🟡), `__str__` shows grade id `4:EN` for grade 2 (ISS-002 🟢), empty names accepted by the schema (ISS-003 🟢)
- [x] **Remediation — Story 2.1 (review v1)**: ✅ Resolved (3/3) — 2026-10-22
  - Evidence: `docs/reviews/story-2.1-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 787/787 tests, coverage 100%, gates clean; real DB: migrate → rollback to 0002 → zero → migrate OK, 10/111 rows, 3 active, empty name rejected by `subject_names_not_empty`
- [x] **Story 1.6 Molecule Primitives (+ 1.3 ISS-004)**: Done — 2026-10-22
  - Evidence: `docs/stories-implemented/story-1.6-review.md` (DoD Evidence: Gate 1 spec echo 14/14 AC + steps + Must Read + 1.3 ISS-004; Gates 2–3) — 980/980 tests ×3 in the worktree and re-run on merged `main`, coverage 100%, ruff/mypy/import-linter/makemigrations clean; real server: RO/EN styleguide 200 with every molecule in both themes, login + 404 link the component CSS, 0 ERROR lines. `docs/reviews/story-1.3-code-review-v1.md` now ✅ Fully Remediated (5/5). Open: manual browser checks (screenshots, keyboard/VoiceOver dialog walk-through) before QA
- [x] **Code Review — Story 1.6 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.6-code-review-v1.md` — 980/980 suite re-run, coverage 100%, gates clean; 14/14 AC (AC 1 partial) + 1.3 ISS-004 ✅; probes: `ui_field` on RadioSelect/CheckboxSelectMultiple/`auto_id=False` → `for=""` and shared `_help`/`_error` ids (ISS-001 🟡); alert dismiss drops focus to body (ISS-002 🟢); card title fixed `<h2>` (ISS-003 🟢); styleguide 0 duplicate ids
- [x] **Remediation — Story 1.6 (review v1)**: ✅ Resolved (3/3) — 2026-10-22
  - Evidence: `docs/reviews/story-1.6-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 1001/1001 tests ×3, coverage 100%, gates clean; module move proven behaviour-neutral (980/980) before the fixes; real server: styleguide/login 200, 0 orphan labels or `_help`/`_error` ids, 0 duplicate ids, 0 ERROR lines
- [x] **Story 1.9 Admin Accounts & Parent–Child Links**: Done — 2026-10-22
  - Evidence: `docs/stories-implemented/story-1.9-review.md` (DoD Evidence: Gate 1 spec echo 15/15 AC + steps + Must Read + 4 owner decisions; Gates 2–3) — 1273/1273 tests ×3 in the worktree and re-run on merged `main`, coverage 100% (domain/application 100%), ruff/mypy/import-linter/makemigrations clean; real server on a fresh DB: admin flows OK, 0 ERROR lines, no passwords/DOB/names in logs. Open: browser/CSP/screen-reader check of the admin pages
- [x] **Code Review — Story 1.9 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-22
  - Evidence: `docs/reviews/story-1.9-code-review-v1.md` — 1273/1273 suite re-run (each gate read from its own line), coverage 100%; probes: 35 admin routes × GET/POST × 4 roles → anonymous 302 / others 403 (70/70 each); 9 admin pages CSP-clean (0 inline script/style); real server: no DOB/password/name in logs, audit = field names only; unlock → next login 302; deactivation ends the session. Findings: story file not updated with the 4 owner decisions (ISS-001 🟡, QA would test the old contract), lockout list shows raw typed usernames (ISS-002 🟢)
- [x] **Remediation — Story 1.9 (review v1)**: ✅ Resolved (2/2) — 2026-10-23
  - Evidence: `docs/reviews/story-1.9-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 1278/1278 tests ×3, coverage 100%, every gate read from its own line; real server: typed secret shown 0×, `(unknown):<fingerprint>` label, real account by name, 0 ERROR lines
- [x] **Story 1.7 App Shell & Role Homes**: Done — 2026-10-23
  - Evidence: `docs/stories-implemented/story-1.7-review.md` (DoD: Gate 1 spec echo 11/11 AC + 3a + steps + 3 hand-offs; Gates 2–3) — 1344/1344 tests ×3, coverage 100%, every gate read from its own line; real server: 4 role homes 200 with correct theme/menu/cards, `/` redirects, 0 inline script/style, DEBUG-off 404 inside the full layout, 0 ERROR lines. Open: screenshots/console/keyboard/screen-reader pass
- [x] **Code Review — Story 1.7 (v1)**: ⚠️ APPROVED WITH COMMENTS — 2026-10-23
  - Evidence: `docs/reviews/story-1.7-code-review-v1.md` — 1344/1344 suite re-run (each gate on its own line), coverage 100%; probes: greeting, escaping, query-string marker, switch from home, DB-down login/admin/home; findings: sticky top bar without `scroll-padding-top` can hide focused controls (ISS-001 🟡, WCAG 2.4.11), leading-space name loses the greeting (ISS-002 🟢), empty nav landmark for a corrupt role (ISS-003 🟢)
- [x] **Remediation — Story 1.7 (review v1)**: ✅ Resolved (3/3) — 2026-10-23
  - Evidence: `docs/reviews/story-1.7-code-review-v1.md` (banner, per-issue resolutions, Remediation Section) — 1350/1350 tests ×3, coverage 100%, every gate read from its own line; real server: `Bună, Ana!` for a leading-space name, scroll-padding rule served, 0 ERROR lines
- [x] **Story 2.2 Catalogue & Subject Pages**: Done — 2026-10-23
  - Evidence: `docs/stories-implemented/story-2.2-review.md` (DoD: Gate 1 spec echo 12/12 AC + 7 steps; Gates 2–3) — 1486/1486 tests ×3 in the worktree and re-run on merged `main`, coverage 100%, every gate read from its own line; real server, 4 roles × RO/EN: student sees exactly 3 subject links + 108 disabled tiles, h1/10×h2/3×h3, MEM 200, inactive/unknown 404, staff read-only, anonymous 302, 0 inline script/style, 0 ERROR lines. Open: screenshots + manual Tab walk
---

## Upcoming

1. **aire-review-code** for 2.2
2. **CI pipeline** (`aire-devops-discover` → `aire-devops-pipeline`) before Wave 5 (1.10 adds Playwright E2E)
3. **Wave 5** (`aire-dev-implement`): Dev 1 → 1.10 Foundation E2E Journeys (carries hand-offs: dialog keyboard, alert-dismiss focus, focus-not-obscured) → CYCLE-1 demo and sign-off
4. Manual browser pass of the styleguide, admin pages, app shell and catalogue (both themes, keyboard/VoiceOver, console CSP)
5. **DevOps** (`aire-devops-discover`, during CYCLE-2): gettext + `compilemessages` before tests in CI/Docker; HSTS subdomains/preload (1.0 ISS-004); `python-ipware` for the axes proxy count; login rate limit (1.2 ISS-005) + audit_log retention (1.8 ISS-004) + trusted X-Request-ID only from the proxy (1.1 ISS-004)
6. Optional: update the UI canvas Catalogue screen (add Grădiniță before Clasa pregătitoare)
7. **Tracker export decision** (keep Local, or publish to GitHub Projects / Azure DevOps)

## Agent Activity

| Agent | Last Action | Status | Updated | Recorded |
|-------|------------|--------|---------|----------|
| ANALYST_PM_GREENFIELD | Requirements complete | Idle | 2026-10-19 | 2026-10-19 11:24 |
| ARCHITECT | Patterns & standards complete (approved) | Idle | 2026-10-19 | 2026-10-19 14:34 |
| UI_UX_DESIGNER | UI/UX spec complete (approved) | Idle | 2026-10-19 | 2026-10-19 14:56 |
| BUILD_CYCLE_PLANNER | Build cycles confirmed and generated | Idle | 2026-10-19 | 2026-10-19 14:45 |
| PRODUCT_OWNER | CYCLE-3 plan + 18 stories written (all cycles planned) | Idle | 2026-10-19 | 2026-10-19 19:23 |
| DEV | Story 2.2 complete (in one go) — wave 4 done | Idle | 2026-10-23 | 2026-10-23 10:36 |
| REVIEWER | Reviewed story 1.7 (approved with comments) | Idle | 2026-10-23 | 2026-10-23 09:36 |
| QA | Regression complete — 0 regressions | Idle | 2026-10-21 | 2026-10-21 16:50 |
