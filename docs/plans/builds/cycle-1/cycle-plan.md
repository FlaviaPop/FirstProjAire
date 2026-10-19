# Cycle Plan — Foundation & Access

**Cycle ID**: cycle-1
**BUILDID**: CYCLE-1
**Dates**: 2026-10-19 → 2026-10-26
**Expected Outcome**: A deployable skeleton. Every role (Student, Teacher, Parent/Guardian, Admin) logs in, uses the app in RO or EN, sees a role-specific home page and the K–8 catalogue (only grade 2 CLR/MEM/EN active). The Admin creates accounts and parent–child links.

---

## Scope

### In Scope (this cycle)

Epic and story numbers are proposed here. `aire-greenfield-plan` finalises the stories and tags each one with `BUILDID: CYCLE-1`.

- **Epic 1 — Foundation** (FE + BE setup, per the greenfield rulebook)
  - Project scaffold: uv + Python 3.12 pin, Django 5.2, `src/` layered layout, settings split (base/dev/test/prod), env helper, `.env.example`, README
  - SQLite configuration (WAL, `IMMEDIATE` transactions, timeout), `AUTH_USER_MODEL` in `accounts` migration `0001`
  - Quality tooling: ruff, mypy, import-linter contracts, pytest + coverage gates (≥85% overall, 100% domain, ≥95% application), Playwright harness
  - Accounts: custom user (role, full name, date of birth, preferred language), Argon2id, django-axes lockout, session hardening, login/logout
  - RBAC: `Role`, `Permission`, `ROLE_PERMISSIONS` (verbatim from the requirements matrix), the `@require_permission` decorator, `PUBLIC_URL_NAMES`
  - Django admin limited to Admin: account CRUD, password reset, parent–child links (`LinkParent` use case, role checks)
  - i18n: `LocaleMiddleware`, `i18n_patterns` (`/ro/`, `/en/`), language switcher saving `preferred_language`, RO/EN catalogues
  - Web platform: base layout with top navigation per role, design tokens (`tokens.css`), the 16 UI primitives, the `/_styleguide/` page (DEBUG only), error pages (403/404/409/500), `DomainErrorMiddleware`, CSP and security headers
  - Observability: JSON logging, `RequestIdMiddleware`, `AUDIT_LOG` + `AuditPort` (logins, failed logins, lockouts, account and link changes), `/healthz`
  - Cross-cutting tests: permission matrix = requirements, every URL protected or public, role access matrix, no unsafe HTML, layer contracts, translations complete
- **Epic 2 — Grade & Subject Catalogue**
  - Grade/Subject models and a data migration seeding K–8 and their subject categories, with only grade 2 CLR, MEM and EN active
  - Catalogue page: inactive grades and subjects shown as disabled tiles (no link, `aria-disabled`); their routes return 404

### Deferred to Next Cycle

- All content authoring and learner content pages → CYCLE-2 (needs the Epic 1 platform and Epic 2 catalogue)
- Tests, scoring, moderation, progress pages → CYCLE-3

---

## Workshop Plan (4 half-days)

**Day 1**: Scaffold and quality gates
→ Goal: production-ready repo skeleton: layered `src/`, settings, SQLite config, custom user migration, CI-equivalent local checks (ruff, mypy, import-linter, pytest + coverage) all green; `/healthz` live.

**Day 2**: Authentication, roles and admin
→ Goal: login/logout with Argon2id and lockout, `ROLE_PERMISSIONS` + decorator + matrix tests, Django admin for accounts and parent links, audit log entries for these actions.

**Day 3**: Web platform and i18n
→ Goal: base layout, top navigation per role, tokens and the 16 primitives on `/_styleguide/`, RO/EN switching, error pages, domain error middleware, JSON logs with request ids.

**Day 4**: Catalogue, integration and stakeholder review
→ Goal: seeded K–8 catalogue with active/inactive behaviour; role home pages; Playwright smoke test per role (login → home → catalogue); demo and sign-off.

Each day ends with **production-ready, deployable code**. No partial or broken states overnight.

---

## Acceptance Criteria

- An Admin creates Student, Teacher, Parent and Admin accounts in Django admin and links a parent to a student; non-Admin roles get 403 on `/admin/`.
- Each role logs in, lands on its role home in its `preferred_language`, and can switch RO/EN; the switch persists.
- 5 failed logins lock the account for 15 minutes; the lockout is written to `AUDIT_LOG`.
- The catalogue shows grades K–8. Only grade 2 CLR, MEM and EN are interactive; every other grade or subject is visibly unavailable and its URL returns 404.
- `ROLE_PERMISSIONS` exactly matches the matrix in `docs/requirements.md` (test-proven); every URL is either permission-protected or in `PUBLIC_URL_NAMES` (test-proven).
- `/_styleguide/` renders all 16 primitives in RO and EN (DEBUG only; 404 when `DEBUG=False`).
- Data survives an app restart (SQLite file on disk).
- Quality gates are green: coverage ≥85% overall, domain 100%, application ≥95%; ruff, mypy and import-linter clean.

## Open Items

| Item | Owner |
| ---- | ----- |
| Finish `aire-ui-ux-design` (paused at Step 05: icon set and spacing scale pending) before Day 3; otherwise Day 3 uses the provisional tokens from `docs/ui-ux/03-inspiration.md` and the Step 04 proposal | Project owner / UI_UX_DESIGNER |
| Confirm Atkinson Hyperlegible Next renders Romanian diacritics (ș ț ă â î); fall back to `system-ui` if not | DEV (Day 3) |
| Subject categories to show for non-pilot grades (K, 1, 3–8) for the catalogue seed | Project owner / teachers |
| Teachers start drafting chapter content offline (RO + EN Markdown per chapter, exercises, 10 test questions with points totalling 100) so it can be entered after CYCLE-2 | Teachers |

## Prerequisites

- Approved: `docs/requirements.md`, `docs/architecture/design/00-system-architecture-greenfield.md`, `docs/architecture/design/01-patterns-and-standards-greenfield.md`
- `uv` 0.13.1 and Python 3.12.15 installed on the dev machine (done 2026-10-19)
- Implementation plan with CYCLE-1 stories (`aire-greenfield-plan`)
