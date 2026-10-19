# UI/UX Discovery

**Date**: 2026-10-19
**Author**: UI_UX_DESIGNER
**Inputs**: `docs/requirements.md` v1.0 · `docs/architecture/design/00-system-architecture-greenfield.md` v1.0 · `docs/architecture/design/01-patterns-and-standards-greenfield.md` v1.0 (all Approved)
**References**: `SPEC/references/` contains no design files (builds/ and devops/ are empty)

## Constraints extracted

| Item | Value | Source |
|------|-------|--------|
| Platform | Web, desktop/laptop only; mobile/tablet out of scope | Requirements: Technical Constraints, OUT of Scope |
| Tech | Django templates + HTMX 2.0, plain CSS with tokens (`static/css/tokens.css`), no JS build, no CDN | ADR-003; Patterns §1, §7.4, §11 |
| Charts | none required | Requirements |
| Auth | Admin-created username/password; login page only | Requirements; Architecture Security Design |
| Languages | RO (default) + EN for UI and content; switcher in header | Requirements NFR; Architecture i18n |
| Avatar | generic icon only; no uploads | Requirements |
| Shared primitives | 16 primitives defined (button, status pill, badge, alert, form field, card, avatar, icon, progress meter, score, empty state, confirm dialog, page header, table, language switcher, disabled tile) | Patterns §11.2 |
| A11y baseline | labels on inputs, status not by colour alone, visible focus, ≥16px body text, semantic elements, `lang` attribute | Patterns §11.4 |
| Icons | inline SVG sprite at `static/icons/sprite.svg` | Patterns §11.2 |

## Users & key flows

| Role | Profile | Key flows |
|------|---------|-----------|
| Student | 7–8 years old, grade 2, early reader | catalogue → subject → chapter → lesson → exercises ("Finish exercise" shows answers + explanations) → chapter test (one attempt) → score; own progress |
| Teacher | adult, 2 in the pilot | dashboard (chapter completeness, item statuses, block reasons) → edit lesson (RO+EN Markdown, preview) / exercises / test (10 questions, points total 100, publish) → notifications → resubmit blocked content; all scores |
| Parent/Guardian | adult | linked children list → child progress & scores (read-only) |
| Admin | adult | Django admin (accounts, links) → moderation queue (flag / approve / block with reason / clear) → pilot dashboard; all scores |

## Screen states the UI must express

- Catalogue: active (grade 2 CLR/MEM/EN) vs **visible but unavailable** (K–8 others), not clickable
- Moderation: ACTIVE / FLAGGED / BLOCKED / RESUBMITTED (pill with text + colour)
- Test: DRAFT / PUBLISHED; available / submitted (score only, no per-question marks)
- Points total live indicator in the test editor (must reach exactly 100 to publish)
- Errors: 400/422 form, 403, 404, 409 ("already submitted"), 500 with request id

## Design answers (Step 02, user — 2026-10-19)

| # | Question | Answer |
|---|----------|--------|
| 1 | Target emotion | **Split by role**: Student = friendly and playful (warm, rounded, larger type); Teacher/Parent/Admin = calm and efficient; one shared token set |
| 2 | Design system | **Custom** (derived: plain CSS tokens per approved patterns) |
| 3 | Data density | **Low for students, medium for staff** |
| 4 | Navigation | **Top navigation bar** (role-specific links + language switcher + avatar) |
| 5 | Error display | **Inline below field + summary banner at top of form** |
| 6 | Loading states | **Button spinner + disabled** during HTMX/form requests; normal page loads otherwise |
| 7 | Colour | **Teal-blue primary** with warm orange/yellow accents for students; red not used as a main colour |
| 8 | Accessibility | **WCAG AA** |
| 9 | Inspiration | **None**: children's-learning best practice (large cards, one primary action per screen, friendly icons) |
| 10 | Responsive target | **Desktop-only** (derived: requirements) |
