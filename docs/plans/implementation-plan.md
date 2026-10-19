# Romanian Curriculum Learning Platform (Working Title) - Implementation Plan

**Project**: Romanian Curriculum Learning Platform | **Version**: 1.0 | **Created**: 2026-10-19
**Author**: PRODUCT_OWNER | **Status**: CYCLE-1 APPROVED (2026-10-19) · CYCLE-2 APPROVED (2026-10-19)
**Scope of this plan version**: CYCLE-1 (Epics 1–2, waves 1–5) and CYCLE-2 (Epics 3–5, waves 6–9). CYCLE-3 (Epics 5–8) is appended by a later `aire-greenfield-plan` session — see `docs/plans/build-cycles.md`.

---

## Dependency Graph

> Source of truth: `docs/plans/dependency-graph.yml`. If the Mermaid drifts from the YAML, the YAML wins. The plan workflow re-renders the Mermaid whenever the graph changes.

```mermaid
graph TD
  S10["1.0 Root tooling seed"]
  S11["1.1 Errors & observability"]
  S12["1.2 Login & session security"]
  S13["1.3 RBAC core"]
  S14["1.4 Internationalization"]
  S15["1.5 Tokens & atom primitives"]
  S18["1.8 Audit log"]
  S21["2.1 Catalogue data"]
  S16["1.6 Molecule primitives"]
  S19["1.9 Admin accounts & parent links"]
  S17["1.7 App shell & role homes"]
  S22["2.2 Catalogue & subject pages"]
  S110["1.10 Foundation E2E journeys"]

  S10 --> S11 & S12 & S13 & S14 & S15 & S18 & S21
  S15 --> S16
  S13 --> S19
  S18 --> S19
  S12 --> S17
  S13 --> S17
  S14 --> S17
  S16 --> S17
  S12 --> S22
  S13 --> S22
  S16 --> S22
  S21 --> S22
  S11 --> S110
  S17 --> S110
  S19 --> S110
  S22 --> S110

  classDef w1 fill:#FEF3C7,stroke:#B45309,color:#1F2937
  classDef w2 fill:#CFFAFE,stroke:#0E7490,color:#1F2937
  classDef w3 fill:#DCFCE7,stroke:#15803D,color:#1F2937
  classDef w4 fill:#EDE9FE,stroke:#6D28D9,color:#1F2937
  classDef w5 fill:#FEE2E2,stroke:#B91C1C,color:#1F2937
  class S10 w1
  class S11,S12,S13,S14,S15,S18,S21 w2
  class S16,S19 w3
  class S17,S22 w4
  class S110 w5
```

| Wave | Stories | Notes |
|------|---------|-------|
| 1 | 1.0 | Root tooling seed — single story, one branch (creates every shared file + custom user model) |
| 2 | 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 2.1 | Disjoint packages — true parallel; overlap only on seeded `shared_files` |
| 3 | 1.6, 1.9 | Disjoint files |
| 4 | 1.7, 2.2 | Disjoint files |
| 5 | 1.10 | E2E journeys — needs all CYCLE-1 features merged |

📊 **Wave Workload Distribution (team_size: 2)**

| Wave | Stories | Per Dev | Dev Assignments | Notes |
|------|---------|---------|-----------------|-------|
| 1 | 1 | 1 / 0 | Dev-1: [1.0] / Dev-2: — | ⚠️ 1 dev idles (R1 seed constraint) |
| 2 | 7 | 4 / 3 | Dev-1: [1.5, 1.2, 2.1, 1.1] / Dev-2: [1.3, 1.8, 1.4] | ✅ All devs active |
| 3 | 2 | 1 each | Dev-1: [1.6] / Dev-2: [1.9] | ✅ All devs active |
| 4 | 2 | 1 each | Dev-1: [1.7] / Dev-2: [2.2] | ✅ All devs active |
| 5 | 1 | 1 / 0 | Dev-1: [1.10] / Dev-2: — | ⚠️ 1 dev idles (integration must follow features) |

### CYCLE-2 (waves 6–9, team_size 3)

```mermaid
graph TD
  S110["1.10 CYCLE-1 complete"]
  S31["3.1 Content domain rules"]
  S32["3.2 Content data model"]
  S33["3.3 Markdown rendering"]
  S34["3.4 Authoring web kit"]
  S41["4.1 Progress data & use cases"]
  S51["5.1 Pilot readiness dashboard"]
  S35["3.5 Teacher dashboard & chapters"]
  S36["3.6 Lesson editor"]
  S37["3.7 Exercise editor"]
  S38["3.8 Test editor & publishing"]
  S42["4.2 Chapter list & lesson reading"]
  S43["4.3 Exercise practice"]
  S39["3.9 Authoring E2E"]
  S44["4.4 Learning E2E"]

  S110 --> S31 & S32 & S33
  S31 --> S34
  S31 --> S41
  S32 --> S41
  S32 --> S51
  S31 --> S35
  S32 --> S35
  S34 --> S35
  S32 --> S36
  S33 --> S36
  S34 --> S36
  S31 --> S37
  S32 --> S37
  S34 --> S37
  S31 --> S38
  S32 --> S38
  S34 --> S38
  S33 --> S42
  S41 --> S42
  S31 --> S43
  S41 --> S43
  S35 & S36 & S37 & S38 & S51 --> S39
  S42 & S43 --> S44

  classDef done fill:#F3F4F6,stroke:#6B7280,color:#1F2937
  classDef w6 fill:#FEF3C7,stroke:#B45309,color:#1F2937
  classDef w7 fill:#CFFAFE,stroke:#0E7490,color:#1F2937
  classDef w8 fill:#DCFCE7,stroke:#15803D,color:#1F2937
  classDef w9 fill:#FEE2E2,stroke:#B91C1C,color:#1F2937
  class S110 done
  class S31,S32,S33 w6
  class S34,S41,S51 w7
  class S35,S36,S37,S38,S42,S43 w8
  class S39,S44 w9
```

| Wave | Stories | Notes |
|------|---------|-------|
| 6 | 3.1, 3.2, 3.3 | Need only CYCLE-1 complete (1.10); separate packages (domain / persistence / rendering) |
| 7 | 3.4, 4.1, 5.1 | Separate packages; 3.4 creates `web/content/urls.py` (shared from wave 8) |
| 8 | 3.5, 3.6, 3.7, 3.8, 4.2, 4.3 | One file per feature; overlap only on shared files |
| 9 | 3.9, 4.4 | Separate E2E files |

📊 **Wave Workload Distribution (team_size: 3)**

| Wave | Stories | Per Dev | Dev Assignments | Notes |
|------|---------|---------|-----------------|-------|
| 6 | 3 | 1 each | Dev-1: [3.1] / Dev-2: [3.2] / Dev-3: [3.3] | ✅ All devs active |
| 7 | 3 | 1 each | Dev-1: [3.4] / Dev-2: [4.1] / Dev-3: [5.1] | ✅ All devs active |
| 8 | 6 | 2 each | Dev-1: [3.5, 3.8] / Dev-2: [3.6, 4.2] / Dev-3: [3.7, 4.3] | ✅ All devs active |
| 9 | 2 | 1 / 1 / 0 | Dev-1: [3.9] / Dev-2: [4.4] / Dev-3: — | ⚠️ 1 dev idles (E2E must follow features) |

---

## 1. Overview

**Success Criteria** (from `docs/requirements.md`):
- SC-1: 10 students and 2 teachers onboarded via admin-created accounts
- SC-2: 3 subjects × 3 chapters; each chapter has a main lesson, 5–10 higher-difficulty exercises and one 10-question test
- SC-3: ≥ 8 of 10 students complete a chapter test
- SC-4: feedback collected from all 10 students and both teachers
- FC-1 / FC-2: no missing chapter content; every role workflow passes its acceptance criteria (incl. no unauthorized access)

**CYCLE-1 contribution**: the platform foundation every later criterion depends on — accounts and roles (SC-1 enabler), record isolation primitives (FC-2), bilingual UI, and the K–8 catalogue.

**Epic Breakdown** (CYCLE-1):
- Epic 1: Foundation — deployable, secure, bilingual walking skeleton with accounts, roles, audit and the UI primitive library
- Epic 2: Grade & Subject Catalogue — K–8 catalogue with only grade 2 CLR/MEM/EN active

---

## EPIC 1: FOUNDATION

**Owner**: DEV | **Goal**: Every role logs in (RO/EN), lands on a role home inside the shared app shell; the Admin manages accounts and parent links; security, audit, error handling and quality gates are in place.

**Must Read References**:
- `docs/architecture/design/00-system-architecture-greenfield.md` — architecture (ADR-001…011, security, error handling, observability)
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — patterns, boundary map, quality checklist
- `docs/ui-ux/ui-ux-spec.md` + `docs/ui-ux/08-visual-foundation.md` — design tokens and visual foundation (FE stories)
- `docs/plans/builds/cycle-1/cycle-plan.md` — CYCLE-1 scope

**Prerequisites**: uv 0.13.1 + Python 3.12.15 installed | **Completion**: all Epic 1 stories Done, CYCLE-1 acceptance criteria for accounts/RBAC/i18n/primitives pass, quality gates green.

| Story | Title | BUILDID | Wave | One-line objective |
|-------|-------|---------|------|--------------------|
| 1.0 | Root tooling seed | CYCLE-1 | 1 | Create the uv/Django project, layered `src/`, settings, custom user model (migration 0001), quality tooling and `/healthz` — every shared file exists after this story |
| 1.1 | Error handling & observability | CYCLE-1 | 2 | Domain error hierarchy mapped to localized 403/404/409/500 pages in one middleware; JSON logs with request id; injectable clock |
| 1.2 | Login & session security | CYCLE-1 | 2 | Admin-created accounts can log in/out with Argon2id hashing, 5-strikes/15-min lockout, hardened sessions and a redirect to their role home in their language |
| 1.3 | RBAC core | CYCLE-1 | 2 | Encode the Roles & Permissions Matrix verbatim, enforce it with `@require_permission` (403) and record scoping (404), and prove every URL is protected |
| 1.4 | Internationalization | CYCLE-1 | 2 | `/ro/` and `/en/` URLs, a language switcher that persists `preferred_language`, and a `localized` helper for bilingual content |
| 1.5 | Design tokens & atom primitives | CYCLE-1 | 2 | `tokens.css` from the UI/UX spec, Phosphor sprite, self-hosted font, 7 atom primitives and the DEBUG-only `/_styleguide/` page |
| 1.6 | Molecule primitives | CYCLE-1 | 3 | The remaining 8 shared primitives (form field with RO|EN pair, alert, card, disabled tile, empty state, page header, confirm dialog, data table) on the styleguide |
| 1.7 | App shell & role homes | CYCLE-1 | 4 | Base layout with role-specific top bar, avatar menu, flash messages, HTMX/CSRF wiring and a home page per role |
| 1.8 | Audit log | CYCLE-1 | 2 | Append-only `AUDIT_LOG` with an `AuditPort`, recording logins, failed logins and lockouts |
| 1.9 | Admin account management & parent–child links | CYCLE-1 | 3 | Admin-only Django admin for accounts and parent–child links with role validation and audit entries |
| 1.10 | Foundation E2E journeys | CYCLE-1 | 5 | Playwright harness and per-role journeys proving the CYCLE-1 outcome end to end |

---

## EPIC 2: GRADE & SUBJECT CATALOGUE

**Owner**: DEV | **Goal**: Users see grades K–8 with their subject categories; only grade 2 CLR, MEM and EN are interactive.

**Must Read References**:
- `docs/requirements.md` — Feature "Grade and subject catalogue"
- `docs/architecture/design/00-system-architecture-greenfield.md` — `catalogue` module, route catalogue
- `docs/ui-ux/ui-ux-spec.md` — tokens; `disabled_tile`, `card` primitives

**Prerequisites**: Story 1.0 (data), Stories 1.2/1.3/1.6 (pages); subject categories for non-pilot grades supplied by the project owner (open item, CYCLE-1 plan) | **Completion**: catalogue AC in `docs/plans/builds/cycle-1/cycle-plan.md` pass.

| Story | Title | BUILDID | Wave | One-line objective |
|-------|-------|---------|------|--------------------|
| 2.1 | Catalogue data | CYCLE-1 | 2 | Grade and Subject models with constraints and a reversible data migration seeding K–8, with only grade 2 CLR/MEM/EN active |
| 2.2 | Catalogue & subject pages | CYCLE-1 | 4 | Catalogue grid with active cards and unavailable tiles; inactive routes return 404; active subjects open a chapter-list shell |

---

## EPIC 3: TEACHER CONTENT AUTHORING

**Owner**: DEV | **Goal**: A Teacher authors a complete chapter in RO and EN (lesson, 5–10 exercises, a 10-question test whose points total 100) and publishes the test; content is live for students immediately and carries moderation fields for CYCLE-3.

**Must Read References**:
- `docs/requirements.md` — Features "Course lessons and practice", "Chapter tests", "Teacher-managed content and admin moderation"
- `docs/architecture/design/00-system-architecture-greenfield.md` — `content` module, Data Model, answer-key formats, route catalogue (`/teach/…`), ADR-006/008/010
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — use cases, repositories, forms, HTMX, primitives
- `docs/ui-ux/ui-ux-spec.md` — `editors: ro_en_side_by_side`, confirm before publish
- `docs/plans/builds/cycle-2/cycle-plan.md`

**Prerequisites**: CYCLE-1 complete (Story 1.10) | **Completion**: CYCLE-2 authoring acceptance criteria pass; Story 3.9 journeys green.

| Story | Title | BUILDID | Wave | One-line objective |
|-------|-------|---------|------|--------------------|
| 3.1 | Content domain rules | CYCLE-2 | 6 | Pure rules for question kinds, answer-key validation, numeric parsing, test publication (10 questions, points ≥1, Σ = 100, bilingual), chapter numbering, and the moderation status enum |
| 3.2 | Content data model | CYCLE-2 | 6 | Chapter, Lesson, Exercise, ChapterTest and TestQuestion tables with DB constraints and moderation fields (default ACTIVE), plus test factories |
| 3.3 | Markdown rendering | CYCLE-2 | 6 | Safe Markdown → HTML (nh3 allowlist) with a `render_markdown` tag and a guard test that forbids unsafe HTML anywhere else |
| 3.4 | Authoring web kit | CYCLE-2 | 7 | Shared teacher-area URL scaffold, RO\|EN bilingual form mixin, reusable question-fields form (MCQ/TF/numeric) and editor styles |
| 3.5 | Teacher dashboard & chapters | CYCLE-2 | 8 | Teacher dashboard showing each pilot chapter's completeness and item status; create/edit up to 3 chapters per active subject |
| 3.6 | Lesson editor | CYCLE-2 | 8 | Side-by-side RO\|EN Markdown lesson editor with live preview; saved lessons are visible to students immediately |
| 3.7 | Exercise editor | CYCLE-2 | 8 | Create, edit and remove bilingual exercises (MCQ, true/false, numeric) with explanations; at most 10 per chapter |
| 3.8 | Test editor & publishing | CYCLE-2 | 8 | Edit the 10-question chapter test with per-question points and a live total; publishing is allowed only when every rule passes |
| 3.9 | Authoring E2E journeys | CYCLE-2 | 9 | Playwright: a teacher authors and publishes a full chapter; the admin readiness page marks it complete |

---

## EPIC 4: STUDENT LESSONS & PRACTICE

**Owner**: DEV | **Goal**: A Student opens an active subject, reads each chapter's lesson in the active language and practises its exercises, seeing the correct answers and explanations after "Finish exercise"; lesson views and exercise completions are recorded for progress (CYCLE-3).

**Must Read References**:
- `docs/requirements.md` — Feature "Course lessons and practice"
- `docs/architecture/design/00-system-architecture-greenfield.md` — `progress` module, route catalogue (`/chapters/<id>/lesson/`, `/chapters/<id>/exercises/`, `/exercises/<id>/finish/`), moderation visibility rule
- `docs/ui-ux/ui-ux-spec.md` — student theme, `success_feedback: in_place`, `loading: button_spinner_disable`

**Prerequisites**: Stories 3.1–3.3 | **Completion**: CYCLE-2 learner acceptance criteria pass; Story 4.4 journeys green.

| Story | Title | BUILDID | Wave | One-line objective |
|-------|-------|---------|------|--------------------|
| 4.1 | Progress data & use cases | CYCLE-2 | 7 | LessonView and ExerciseCompletion records with idempotent RecordLessonView and FinishExercise use cases |
| 4.2 | Chapter list & lesson reading | CYCLE-2 | 8 | Subject page lists visible chapters; lesson page renders the ACTIVE lesson in the current language and records the first view |
| 4.3 | Exercise practice | CYCLE-2 | 8 | Exercise list with completion marks; "Finish exercise" reveals the student's answer, the correct answer and the explanation in place (unscored) |
| 4.4 | Learning E2E journeys | CYCLE-2 | 9 | Playwright: a student reads a lesson and finishes exercises; non-ACTIVE content never appears |

---

## EPIC 5: PILOT REPORTING

**Owner**: DEV | **Goal**: The Admin sees, per pilot chapter, whether content is launch-ready (SC-2 / FC-1); CYCLE-3 adds onboarding and completion counts (SC-1 / SC-3).

**Must Read References**:
- `docs/requirements.md` — SC-1…SC-3, FC-1
- `docs/architecture/design/00-system-architecture-greenfield.md` — `reporting` module, `/manage/pilot/`, Observability "Pilot metrics"

**Prerequisites**: Story 3.2 | **Completion**: readiness section matches the content state for all 9 chapters.

| Story | Title | BUILDID | Wave | One-line objective |
|-------|-------|---------|------|--------------------|
| 5.1 | Pilot readiness dashboard | CYCLE-2 | 7 | Admin-only page listing the 9 pilot chapters with lesson present, exercise count (5–10) and published 10-question test, and an overall ready/not-ready verdict |

---

## Quality Gates

**Per Story**: patterns followed, tests written first and passing, ruff/mypy/import-linter clean, coverage ≥85% overall (domain 100%, application ≥95%), AC met, DoD Gates 1–3 evidence in `docs/stories-implemented/story-N.M-review.md`
**Per Epic**: all stories Done, full suite green, feature demonstrable, route catalogue/README updated
**Cycle**: CYCLE-1 acceptance criteria (`docs/plans/builds/cycle-1/cycle-plan.md`) pass at the Day-4 review

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Seed story 1.0 is large (project + user model + tooling) and blocks all of wave 2 | H | Keep it to skeleton + stubs; Dev-2 reviews it immediately so wave 2 starts the same day |
| Subject categories for non-pilot grades not supplied before Story 2.1 | M | Story 2.1 seeds from one data module; project owner supplies the list (open item) |
| Atkinson Hyperlegible Next lacks a Romanian glyph (ș ț ă â î) | L | Story 1.5 verifies glyphs; falls back to `system-ui` |
| Shared-file merge conflicts in wave 2 (settings, urls, `.po`) | M | One appended block per story (alphabetical); `makemessages` only at story end |

---

## QA Manual Testing Groups

### Epic 1: Foundation

**Group 1** — Stories: 1.0 `[backend]`, 1.1, 1.8 `[backend]`
Once these are done, QA can verify the platform's operational baseline: `/healthz` returns `200 {"status":"ok","db":"ok"}`; visiting an unknown URL shows the localized 404 page; forcing a server error shows the 500 page with a request id that also appears in the JSON log line for that request; the seed's quality gates (lint, types, import contracts, coverage) run green. The audit table (inspected via the Django shell or admin once 1.9 lands) receives entries for logins, failed logins and lockouts.

**Group 2** — Stories: 1.2, 1.3 `[backend]`, 1.4
QA logs in as each role with admin-created credentials, confirms the redirect to the role's home in that user's preferred language, switches RO↔EN and sees the choice persist across logout/login, triggers a lockout with 5 wrong passwords (then confirms login is refused for 15 minutes), and confirms role boundaries: a Student or Parent opening a teacher or admin URL gets the 403 page; logged-out access to any protected page redirects to login.

**Group 3** — Stories: 1.5, 1.6
With `DEBUG=True`, QA opens `/_styleguide/` and checks all 16 primitives in RO and EN: colours and contrast match the UI/UX spec, focus outline visible on every interactive element, confirm dialog traps focus and closes with Esc, status pills show text plus colour, disabled tiles are not clickable; with `DEBUG=False` the styleguide returns 404.

**Group 4** — Stories: 1.7, 1.9, 1.10
End-to-end: the Admin creates a Teacher, a Student and a Parent in the admin area, links the Parent to the Student (and sees an error when linking two students or a teacher as parent), each new user logs in and sees the correct top bar (role menu, language switcher, avatar menu) and role home; flash messages appear after actions; non-Admins get 403 on the admin area. The Playwright suite from 1.10 runs these journeys automatically.

### Epic 2: Grade & Subject Catalogue

**Group 1** — Stories: 2.1 `[backend]`, 2.2
After migrations, QA opens the catalogue as each role: grades K–8 appear with their subject categories; only grade 2 CLR, MEM and EN are clickable cards; every other grade/subject is a visibly unavailable tile with no link, and typing its URL directly returns 404; opening an active subject shows its chapter-list shell (empty until CYCLE-2 content exists, with an empty-state message). Data survives an app restart.

### Epic 3: Teacher Content Authoring

**Group 1** — Stories: 3.1 `[backend]`, 3.2 `[backend]`, 3.3 `[backend]`, 3.4, 3.5
The domain rules, tables and Markdown renderer provide the base; the web kit and dashboard make it testable. QA signs in as a Teacher, opens the Dashboard from the menu, and sees the three pilot subjects with their chapter slots. QA creates chapters 1–3 for MEM (titles in RO and EN), confirms a 4th chapter is refused, confirms an empty RO or EN title is refused with field errors, and edits a title. Each chapter row shows lesson/exercises/test completeness and status pills. Students, Parents and Admins get 403 on every `/teach/` page.

**Group 2** — Stories: 3.6, 3.7, 3.8, 3.9
QA writes a lesson in both languages (with headings, a list and a link) and checks the live preview. A `<script>` pasted into the Markdown never runs and doesn't appear in the preview. QA adds 5 exercises (one of each kind), confirms the 11th is refused, edits and removes one. In the test editor, QA fills 10 questions, watches the points total update, tries to publish at 95 points (refused, with the reason listed), fixes it to 100, publishes after the confirmation dialog, and sees the PUBLISHED pill. The Story 3.9 Playwright journey repeats this end to end.

### Epic 4: Student Lessons & Practice

**Group 1** — Stories: 4.1 `[backend]`, 4.2, 4.3, 4.4
With content authored (Group 2 of Epic 3), QA signs in as a Student: the subject page lists the chapters; the lesson opens in the current language and switching RO↔EN shows the other version. The exercise list shows each exercise. "Finish exercise" reveals the student's answer, the correct answer and the explanation in place with no score; reopening the list shows a completion mark. QA then sets a lesson to a non-ACTIVE status in the DB (moderation UI arrives in CYCLE-3) and confirms students get "Page not found" for it. The lesson view and completion rows exist once per student and item, even after repeats.

### Epic 5: Pilot Reporting

**Group 1** — Stories: 5.1
As Admin, QA opens "Pilot" from the menu: all 9 pilot chapters are listed (3 subjects × chapters 1–3) with lesson ✓/✗, exercise count against the 5–10 range and test status. The overall verdict says "Not ready" until every chapter is complete. Authoring a full chapter (Epic 3 Group 2) turns that row green. Teachers, Students and Parents get 403.
