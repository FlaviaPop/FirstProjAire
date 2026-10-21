# Requirements - Romanian Curriculum Learning Platform (Working Title)

**Date**: 2026-10-19  
**Author**: ANALYST_PM_GREENFIELD  
**Status**: Approved  
**Version**: 1.0

---

## Project Overview

### Vision

A bilingual web learning platform that helps Romanian school students learn the Romanian curriculum through grade- and subject-organized lessons, practice, and chapter tests.

### Problem Statement

Students need an accessible way to study curriculum-aligned content and practice independently. The pilot will provide original learning materials, unscored exercises with explanations, and scored chapter tests.

### Target Users

Second-grade students, teachers, parents/guardians, and administrators. The pilot target is 10 students and 2 teachers; administrators manage accounts and content moderation. Parents have read-only access to linked children’s progress and scores.

### Business Value

Support student learning and practice, give teachers a way to maintain course materials and assessments, and allow parents and administrators to see student progress.

---

## Roles & Permissions Matrix

> Canonical source of truth for all personas/roles. Every story's User Flow by Persona
> and RBAC Enforcement block references these role names + permission keys verbatim.

| Role (canonical) | Description | Key Permissions (allow) | Explicitly Denied | Auth Source |
|------------------|-------------|-------------------------|-------------------|-------------|
| Student | Second-grade learner | `lessons:view`, `exercises:complete`, `tests:submit`, `scores:view-own` | Manage content/accounts; view other students’ records | Admin-created username/password account with Student role |
| Teacher | Pilot teacher; may manage all three pilot subjects | `content:create`, `content:edit`, `tests:configure`, `scores:view-all`, `content:resubmit` | Manage accounts; link parents; clear admin blocks | Admin-managed username/password account with Teacher role |
| Parent/Guardian | A child’s parent or guardian | `child-progress:view`, `child-scores:view` for admin-linked child only | Modify content/accounts; view unlinked children’s data | Admin-managed username/password account with Parent role; admin links child |
| Admin | Platform and pilot administrator | `accounts:manage`, `parents:link`, `content:review`, `content:block`, `content:unblock`, `scores:view-all` | None specified | Admin-managed username/password account with Admin role |

**Permission keys**: `lessons:view`, `exercises:complete`, `tests:submit`, `scores:view-own`, `content:create`, `content:edit`, `tests:configure`, `scores:view-all`, `content:resubmit`, `child-progress:view`, `child-scores:view`, `accounts:manage`, `parents:link`, `content:review`, `content:block`, `content:unblock`.

**Role hierarchy**: No additive hierarchy specified; permissions are role-specific. Parent access is limited to children linked by an admin. Students see their own results; teachers and admins can see pilot student results.

---

## Project Type

| Attribute | Value |
|-----------|-------|
| Type | Greenfield - New System |
| Quality Level | MVP for real users |
| Timeline | One month from 2026-10-19; target pilot launch 2026-11-19 |
| Hard Deadline | Not specified; one-month target |

---

## Success Criteria (MUST HAVE)

| ID | Criterion | Measurement | Target |
|----|-----------|-------------|--------|
| SC-1 | Pilot is provisioned | Admin-created accounts | 10 students and 2 teachers onboarded |
| SC-2 | Pilot learning content is complete | Chapter content audit | 3 subjects × 3 chapters; every chapter has a main lesson, 5–10 higher-difficulty exercises, and one 10-question test |
| SC-3 | Students use the test workflow | Pilot completion records | At least 8 of 10 students complete a chapter test |
| SC-4 | Pilot feedback is collected | Structured feedback collection by the project team | Feedback collected from all 10 students and both teachers |

No learning-outcome improvement target is required for this pilot; success is based on completion and participant feedback.

---

## Failure Criteria (UNACCEPTABLE)

| ID | Criterion | Description |
|----|-----------|-------------|
| FC-1 | Missing required content | Launch is unacceptable if any of the 9 pilot chapters lacks its main lesson, has fewer than 5 higher-difficulty exercises, or lacks its 10-question chapter test. |
| FC-2 | Incorrect or unsafe core workflows | Launch is unacceptable if a required Student, Teacher, Parent/Guardian, or Admin workflow fails its acceptance criteria, including unauthorized access to another user’s data, incorrect test scoring/result display, or incorrect content block/notification handling. |

---

## Technical Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Language | Python required | User requirement |
| Application | Web app; desktop/laptop support required | User requirement |
| Data storage | Persistent database required; an in-memory database is not mandatory | Account, content, and progress data must persist across restarts |
| User authentication | Admin-managed username/password accounts | Pilot accounts are created and assigned roles by the admin |
| Hosting, frontend technology, integrations, budget | Not specified | No additional constraints provided |
| Performance/availability targets | No numeric targets specified | To be determined if needed during architecture/QA |

---

## Quality Gates

| Gate | Target | Required |
|------|--------|----------|
| Chapter content completeness | All 9 chapters meet SC-2 | Yes |
| Role-based workflows | All required role permissions and workflows pass end-to-end checks | Yes |
| Test scoring | Teacher-configured question weights total 100; score is in the 1–100 range and is shown only after the single submission | Yes |
| Parent/student privacy | Students see only their records; parents see only admin-linked children; unauthorized access is denied | Yes |
| Content moderation | Blocked content is hidden from students and parents; teacher receives an in-app notice; resubmissions remain hidden until admin clears the block | Yes |
| Test/code coverage, performance, uptime | No numeric target specified | No additional target supplied |

---

## Design References

| File/URL | Type | Description | Used In |
|----------|------|-------------|---------|
| [manuale.edu.ro](https://manuale.edu.ro/) | Official digital textbook reference | Use Romanian curriculum-aligned second-grade books as references. Where multiple books cover a subject, select the one best suited to high-achieving students while remaining grade-appropriate and curriculum-aligned. Create original lesson, exercise, and test content; use textbooks as references only and do not reproduce their material. Specific textbook titles are to be selected during content curation. | All three subject content sets |

---

## Functional Requirements

### Feature: Grade and subject catalogue

**Priority**: Must Have

**User Story**: As a student, I want to see the grade and subject catalogue so I can find available learning content.

**Acceptance Criteria**:
- Show grades from kindergarten through grade 8 and their subject categories.
- Only grade 2’s Communicare in Limba Romana (CLR), Matematica si Explorarea mediului (MEM), and Engleza (EN) are active in the MVP.
- Show other grades and subjects as unavailable/non-interactive; they must not open or allow actions.

### Feature: Course lessons and practice

**Priority**: Must Have

**User Story**: As a student, I want to read lessons and practice each chapter so I can study the material and check my understanding.

**Acceptance Criteria**:
- Each of the three active subjects has exactly 3 chapters in the MVP.
- Each chapter contains a main lesson and 5–10 additional higher-difficulty exercises.
- Exercises are not scored. After the student selects “Finish exercise,” show correct answers and explanations.
- Learning content is available in Romanian and English.

### Feature: Chapter tests

**Priority**: Must Have

**User Story**: As a student, I want to take a chapter test and see my result after submitting it.

**Acceptance Criteria**:
- Each chapter has one 10-question test using automatically scored multiple-choice, true/false, and short numeric question formats.
- A student gets one attempt. No score is shown per question; show the final score after the student submits the test.
- Before sending a test to students, the teacher configures custom points per question; configured weights must total 100.
- The final score is in the 1–100 range; an all-incorrect result is reported as 1, not 0.
- Short numeric answers compare by exact numeric value while ignoring formatting differences (for example, `2` and `2.0` are equivalent).
- Save test results for student, teacher, parent (when linked), and admin access according to the permissions matrix.

### Feature: Teacher-managed content and admin moderation

**Priority**: Must Have

**Acceptance Criteria**:
- Teachers can create/edit lesson content, add exercises, and create/update tests for all three pilot subjects.
- Teacher-created or edited content becomes available immediately unless an admin flags it for review.
- Admins can review flagged content and block incorrect content. Blocked content is immediately hidden from student and parent views.
- When content is blocked, notify its teacher in-app with the reason for the block.
- Teachers can revise and resubmit blocked content. Resubmitted content remains hidden until an admin clears the block.

### Feature: Accounts, roles, and progress visibility

**Priority**: Must Have

**Acceptance Criteria**:
- Admin creates all student, teacher, and parent accounts and assigns their roles using username/password accounts.
- Admin links each parent account to the relevant child account.
- Students can access their own lessons, exercises, tests, and scores; they cannot access another student’s data.
- Parents have read-only access to progress and scores for linked children only.
- Teachers can view pilot student scores; admins can view all pilot records and manage accounts/parent links.
- Store user name and date of birth. Show a generic avatar/icon after login; no profile-photo uploads are required.
- Retain account and score data until an admin deletes the account.

---

## Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Persistence | Account, course, and student progress/test results survive application restarts | Required |
| Usability | Role-appropriate UI; generic avatar; grade/subject options outside MVP are visible but unavailable | Required |
| Language | UI and learning content can be used in Romanian and English | Required |
| Device support | Web app on desktop/laptop | Required |
| Security/privacy | Enforce role-specific access to student records and parent-child links | Required |
| Performance/availability | No numeric target specified | TBD only if needed |

---

## Explicit Scope

### IN Scope ✅
- Second grade and CLR, MEM, EN subjects only.
- Three chapters per active subject, each with a main lesson, 5–10 challenging exercises, and a 10-question test.
- Romanian and English UI and learning content.
- Admin-managed accounts, role-specific access, parent-child links, progress and score visibility.
- Teacher content editing and test configuration; admin flag/block/review flow with in-app teacher notification.
- Visible but inactive grade/subject catalogue from kindergarten through grade 8.

> **Owner decision (2026-10-21):** "kindergarten" = **Grădiniță** (code `K`, preschool, 5 experiential domains); **Clasa pregătitoare** (code `P`) is shown as its own level before grade 1, so the catalogue has 10 levels. See Story 2.1.

### OUT of Scope ❌
- Active learning content or actions for grades other than grade 2.
- Active grade 2 subjects beyond CLR, MEM, and EN.
- Profile-photo uploads.
- Exercise scoring or manual grading of tests/free-text responses.
- More than one attempt per chapter test.
- Reproducing textbook content; textbook materials are reference-only.
- Mobile phone/tablet support in the pilot.

### Future Considerations (Not This Epic)
- Activate additional grades and subjects after the pilot.
- Expand device support beyond desktop/laptop.

---

## Assumptions

| Assumption | Impact if Wrong |
|------------|-----------------|
| Pilot is limited to 10 students and 2 teachers, with one admin-managed platform and linked parent accounts. | Account, role, or rollout requirements may need revision. |
| Teachers author original bilingual material informed by official curriculum/textbook references; no textbook reproduction rights are assumed. | Content sources and legal permissions would need review before using any third-party text. |
| The one-month timeline starts 2026-10-19 and targets pilot launch on 2026-11-19. | Milestones and scope may need replanning. |
| Account and score data remain until an admin deletes the account. | Retention/deletion behavior must change if a different policy is required. |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Nine complete chapters plus bilingual content exceed the one-month pilot window. | Medium | High | Keep scope limited to grade 2’s three subjects and track chapter completion against SC-2. |
| Incorrect or unsuitable learning content reaches children. | Medium | High | Admin can flag/block content; blocked and resubmitted items stay hidden pending admin clearance. |
| Student account or score data is exposed to an unauthorized user. | Low | High | Enforce and test role-specific access and parent-child record boundaries. |

---

## Timeline

| Milestone | Date | Deliverables |
|-----------|------|--------------|
| Requirements Complete | 2026-10-19 | Approved requirements |
| Architecture Complete | TBD | Architecture design |
| Pilot content and implementation complete | TBD | Persistent-data web MVP; 9 chapters; required role workflows |
| Pilot launch target | 2026-11-19 | 10 students and 2 teachers onboarded |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Stakeholder | User/project owner | 2026-10-19 | Approved |
| Technical Lead | TBD | — | Pending |
