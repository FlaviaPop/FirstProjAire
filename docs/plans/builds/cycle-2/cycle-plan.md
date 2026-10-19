# Cycle Plan — Content Authoring & Learning

**Cycle ID**: cycle-2
**BUILDID**: CYCLE-2
**Dates**: 2026-10-27 → 2026-11-05
**Expected Outcome**: A teacher authors a complete chapter (lesson, 5–10 exercises, 10-question test with points totalling 100, published) in RO and EN. A student opens that chapter, reads the lesson and practises the exercises with answers and explanations revealed after "Finish exercise". The Admin sees how complete each of the 9 pilot chapters is. **From the end of this cycle, teachers enter the real pilot content.**

---

## Scope

### In Scope (this cycle)

Epic and story numbers are proposed here. `aire-greenfield-plan` finalises the stories and tags each one with `BUILDID: CYCLE-2`.

- **Epic 3 — Teacher Content Authoring**
  - Chapters: create/edit (exactly 3 per active subject, number 1–3), RO+EN titles
  - Lesson editor: RO+EN Markdown, rendered through Markdown + nh3, HTMX preview, both languages required
  - Exercise editor: MCQ / TRUE_FALSE / NUMERIC, bilingual prompts, options and explanations, max 10 per chapter
  - Test editor: 10 questions, points per question ≥1, live points total via HTMX, `TestPublicationPolicy` (10 questions, Σ = 100, valid answer keys, both languages) and publish
  - Teacher dashboard: per-chapter completeness, item status (moderation pill shown as ACTIVE until CYCLE-3)
  - Moderation fields (`ModeratedModel`, `visible_to_learners()`) are on the models from the start, so CYCLE-3 needs no data migration of content
- **Epic 4 — Student Lessons & Practice**
  - Subject → chapter list → lesson page (records `LESSON_VIEW`)
  - Exercises list + "Finish exercise" (HTMX partial with the student's answer, the correct answer and the explanation; records `EXERCISE_COMPLETION`; unscored)
  - Numeric answer display uses the domain `parse_numeric` rules (shared with CYCLE-3 scoring)
- **Epic 5 — Pilot Reporting (part 1)**
  - `/manage/pilot/` readiness section: for each of the 9 chapters, lesson present, exercise count (5–10), test published with 10 questions (SC-2 / FC-1)

### Deferred to Next Cycle

- Test taking, scoring, results → CYCLE-3 (a published test isn't shown to students yet, by design; it appears once submission exists)
- Moderation actions, notifications → CYCLE-3
- Progress pages for students and parents, score lists, completion metrics (SC-1/SC-3) → CYCLE-3

---

## Workshop Plan (4 half-days)

**Day 1**: Content model and lesson authoring
→ Goal: Chapter/Lesson/Exercise/ChapterTest/TestQuestion models with constraints and `ModeratedModel`; lesson editor with sanitized Markdown preview, RO+EN required.

**Day 2**: Exercise and test authoring
→ Goal: exercise editor (3 kinds); test editor with live total; publish blocked until all `TestPublicationPolicy` rules pass, with a listed violation for each failing rule.

**Day 3**: Student learning flow
→ Goal: student subject → chapter → lesson → exercises; "Finish exercise" reveal; lesson view and exercise completion recorded; only ACTIVE content shown.

**Day 4**: Readiness dashboard, integration, review
→ Goal: teacher dashboard and pilot readiness section; Playwright journeys (teacher authors and publishes a chapter; student reads and practises); demo and sign-off. Teachers onboarded to start content entry.

Each day ends with **production-ready, deployable code**. No partial or broken states overnight.

---

## Acceptance Criteria

- A Teacher creates a chapter with a lesson, 5–10 exercises and a 10-question test in both languages; saving with an empty RO or EN field is rejected.
- Publishing a test with Σ points ≠ 100, fewer or more than 10 questions, a question worth 0 points or an invalid answer key is refused with a message per violation.
- Lesson Markdown containing `<script>`, inline event handlers or `javascript:` links renders without them.
- A Student sees only active subjects and ACTIVE content; "Finish exercise" shows the correct answer and explanation in the current language and records completion; exercises carry no score.
- Students, parents and admins get 403 on all `/teach/` routes.
- The readiness section correctly flags each of the 9 chapters as complete or incomplete per SC-2.
- Quality gates green (coverage, lint, types, import contracts).

## Open Items

| Item | Owner |
| ---- | ----- |
| Teachers have offline drafts ready to enter on 2026-11-05 (about 2 weeks to complete 9 bilingual chapters before launch) | Teachers |
| Start `aire-devops-discover` / `aire-devops-pipeline` during this cycle so deployment is ready before the launch buffer | DEVOPS |

## Prerequisites

- CYCLE-1 complete and signed off (auth, RBAC, i18n, layout, primitives, catalogue)
- At least one Teacher account per pilot teacher created by the Admin
