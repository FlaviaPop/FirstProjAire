# Architecture Diagrams - Romanian Curriculum Learning Platform (Working Title)

**Source**: `docs/architecture/design/00-system-architecture-greenfield.md`
**Generated**: 2026-10-19

> This file contains Mermaid diagrams extracted from the architecture document for easy preview.
> For full architecture details, refer to the source `.md` file.

---

## System Context Diagram

```mermaid
flowchart LR
  student["👧 Student<br/>(grade 2)"]
  teacher["🧑‍🏫 Teacher"]
  parent["👪 Parent/Guardian"]
  admin["🛡️ Admin"]

  subgraph platform["Romanian Curriculum Learning Platform"]
    app["Django web application<br/>(HTML + HTMX over HTTPS)"]
    db[("SQLite database<br/>persistent volume")]
  end

  ref["manuale.edu.ro<br/>(reference only, used offline by teachers)"]

  student -->|"read lessons, finish exercises,<br/>submit tests, view own scores"| app
  teacher -->|"author content, configure tests,<br/>view scores, resubmit blocked content"| app
  parent -->|"view linked children's<br/>progress & scores (read-only)"| app
  admin -->|"manage accounts & links,<br/>moderate content, view all records"| app
  app --> db
  teacher -. "consults when writing<br/>original content" .-> ref
```

---

## Component Architecture (Layered View)

```mermaid
flowchart TB
  subgraph infra["Infrastructure layer (Django)"]
    direction TB
    subgraph web["web"]
      views["Views + URL routes<br/>(i18n_patterns /ro/ /en/)"]
      forms["Forms / formsets"]
      tmpl["Templates + HTMX partials"]
      authz["@require_permission decorator<br/>+ scoping helpers"]
      djadmin["Django admin<br/>(Admin role: accounts, links)"]
    end
    subgraph persist["persistence"]
      orm["Django ORM models + migrations"]
      repos["Repository implementations"]
      queries["Query services (read models)"]
      uow["DjangoUnitOfWork<br/>(transaction.atomic)"]
    end
    md["Markdown renderer + nh3 sanitizer"]
    container["Composition root<br/>(wires use cases)"]
  end

  subgraph app["Application layer"]
    uc["Use cases<br/>SubmitTest · FinishExercise · RecordLessonView<br/>SaveLesson · SaveExercise · SaveTest · PublishTest<br/>FlagContent · ApproveContent · BlockContent<br/>ResubmitContent · ClearBlock · LinkParent"]
    dto["Commands / DTOs"]
  end

  subgraph domain["Domain layer (pure Python, no Django imports)"]
    ent["Entities & value objects<br/>Role · Permission · AnswerKey · Score · Language"]
    rules["Domain services<br/>AnswerChecker · TestScorer · TestPublicationPolicy<br/>ModerationStateMachine · RecordAccessPolicy"]
    ports["Ports (Protocols)<br/>Repositories · UnitOfWork · Clock · Notifier"]
  end

  views --> forms
  views --> authz
  views --> container
  views --> queries
  views --> tmpl
  tmpl --> md
  container --> uc
  uc --> rules
  uc --> ports
  uc --> dto
  rules --> ent
  repos -. implements .-> ports
  uow -. implements .-> ports
  repos --> orm
  queries --> orm
```

---

## Data Model / ER Diagram

```mermaid
erDiagram
  USER ||--o{ PARENT_CHILD_LINK : "is parent in"
  USER ||--o{ PARENT_CHILD_LINK : "is child in"
  GRADE ||--o{ SUBJECT : has
  SUBJECT ||--o{ CHAPTER : has
  CHAPTER ||--o| LESSON : has
  CHAPTER ||--o{ EXERCISE : has
  CHAPTER ||--o| CHAPTER_TEST : has
  CHAPTER_TEST ||--o{ TEST_QUESTION : contains
  USER ||--o{ TEST_ATTEMPT : submits
  CHAPTER_TEST ||--o{ TEST_ATTEMPT : "is attempted in"
  TEST_ATTEMPT ||--|{ ATTEMPT_ANSWER : records
  TEST_QUESTION ||--o{ ATTEMPT_ANSWER : "answered by"
  USER ||--o{ LESSON_VIEW : opens
  LESSON ||--o{ LESSON_VIEW : "viewed in"
  USER ||--o{ EXERCISE_COMPLETION : finishes
  EXERCISE ||--o{ EXERCISE_COMPLETION : "finished in"
  USER ||--o{ NOTIFICATION : receives
  USER ||--o{ MODERATION_EVENT : performs
  USER ||--o{ AUDIT_LOG : "acts in"

  USER {
    int id PK
    string username UK
    string password_hash "Argon2id"
    string role "STUDENT|TEACHER|PARENT|ADMIN"
    string full_name
    date date_of_birth
    string preferred_language "ro|en"
    bool is_active
    datetime date_joined
    datetime last_login
  }
  PARENT_CHILD_LINK {
    int id PK
    int parent_id FK "role=PARENT"
    int student_id FK "role=STUDENT"
    int created_by_id FK "role=ADMIN"
    datetime created_at
  }
  GRADE {
    int id PK
    string code UK "K,1..8"
    int sort_order
    string name_ro
    string name_en
  }
  SUBJECT {
    int id PK
    int grade_id FK
    string code "CLR|MEM|EN|..."
    string name_ro
    string name_en
    bool is_active "true only for grade 2 CLR, MEM, EN"
  }
  CHAPTER {
    int id PK
    int subject_id FK
    int number "1..3, unique per subject"
    string title_ro
    string title_en
    int created_by_id FK
    int updated_by_id FK
  }
  LESSON {
    int id PK
    int chapter_id FK "unique"
    text body_ro "Markdown"
    text body_en "Markdown"
    string moderation_status
    text moderation_reason
    int created_by_id FK
    int updated_by_id FK
    datetime updated_at
  }
  EXERCISE {
    int id PK
    int chapter_id FK
    int position "1..10, unique per chapter"
    string kind "MCQ|TRUE_FALSE|NUMERIC"
    text prompt_ro
    text prompt_en
    json options "MCQ choices, bilingual"
    json answer_key
    text explanation_ro
    text explanation_en
    string moderation_status
    text moderation_reason
    int created_by_id FK
    int updated_by_id FK
  }
  CHAPTER_TEST {
    int id PK
    int chapter_id FK "unique"
    string status "DRAFT|PUBLISHED"
    datetime published_at
    string moderation_status
    text moderation_reason
    int created_by_id FK
    int updated_by_id FK
  }
  TEST_QUESTION {
    int id PK
    int test_id FK
    int position "1..10, unique per test"
    string kind "MCQ|TRUE_FALSE|NUMERIC"
    text prompt_ro
    text prompt_en
    json options
    json answer_key
    int points ">=1; sum per test = 100"
  }
  TEST_ATTEMPT {
    int id PK
    int student_id FK
    int test_id FK
    int earned_points "0..100"
    int score "1..100"
    datetime submitted_at
  }
  ATTEMPT_ANSWER {
    int id PK
    int attempt_id FK
    int question_id FK
    text response_raw
    bool is_correct
    int points_awarded
  }
  LESSON_VIEW {
    int id PK
    int student_id FK
    int lesson_id FK
    datetime first_viewed_at
  }
  EXERCISE_COMPLETION {
    int id PK
    int student_id FK
    int exercise_id FK
    datetime completed_at
  }
  NOTIFICATION {
    int id PK
    int recipient_id FK
    string kind "CONTENT_BLOCKED"
    string content_type "lesson|exercise|test"
    int content_id
    text reason
    datetime created_at
    datetime read_at
  }
  MODERATION_EVENT {
    int id PK
    string content_type
    int content_id
    string action "FLAG|APPROVE|BLOCK|RESUBMIT|CLEAR"
    string from_status
    string to_status
    text reason
    int actor_id FK
    datetime created_at
  }
  AUDIT_LOG {
    int id PK
    int actor_id FK "nullable, SET_NULL"
    string actor_username
    string action
    string target_type
    string target_id
    json metadata
    string ip_address
    datetime created_at
  }
```

---

## Moderation State Machine

```mermaid
stateDiagram-v2
  [*] --> ACTIVE : teacher creates (visible immediately)
  ACTIVE --> FLAGGED : admin flags for review
  FLAGGED --> ACTIVE : admin approves
  FLAGGED --> BLOCKED : admin blocks (reason required) / notify teacher
  ACTIVE --> BLOCKED : admin blocks (reason required) / notify teacher
  BLOCKED --> RESUBMITTED : teacher revises + resubmits
  RESUBMITTED --> ACTIVE : admin clears block
  RESUBMITTED --> BLOCKED : admin blocks again (reason required) / notify teacher
```

---

## Deployment View (Logical)

```mermaid
flowchart LR
  browser["Browser<br/>(desktop/laptop)"] -- HTTPS --> tls["TLS termination<br/>(hosting platform)"]
  tls --> gunicorn["Container: Gunicorn<br/>1 instance, 3 sync workers<br/>Django + WhiteNoise"]
  gunicorn --> sqlite[("SQLite file (WAL)<br/>/data/db.sqlite3<br/>persistent encrypted volume")]
  sqlite -. "nightly online backup<br/>(sqlite3 .backup) + retention" .-> backup[("Backup storage")]
```
