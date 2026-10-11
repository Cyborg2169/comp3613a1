# COMP 3613 Assignment 1

Draft this file with the Guide. **Update it after every phase milestone** before you pause. The use-case diagram is a UML PNG at `docs/diagrams/use-case.png`, linked from this file as `diagrams/use-case.png` (path relative to `docs/report.md`). The model diagram is Mermaid. **Embed wireframe images** as `wireframes/<file>` (files live in `docs/wireframes/`).

Do not put your student ID in this file if you will commit it. The PDF cover adds your name and ID at export time.

## Assigned project

Student Awards

## Three workflows

### 1.
Earn Volunteer Hours (Student)

### 2.
Nominate Student for Award (Teacher)

### 3.
Manage Award Categories (Admin)

## Use case diagram

![Use case diagram](diagrams/use-case.png)

Phase 2 notes: “Earn Volunteer Hours” is represented as **Log Volunteer Hours**; students log entries and teachers verify them before they count toward awards. **Nominate Student for Award** includes **Select Award Category**. Use cases belong only to their named actors; no further missing use case was identified.

## Model diagram

First draft. Update this section in Phase 5 when polish revises the model, and note what changed.

```mermaid
erDiagram
    Student {
        int id
        string name
        string email
    }

    Teacher {
        int id
        string name
        string email
    }

    Admin {
        int id
        string name
        string email
    }

    VolunteerHours {
        int id
        int student_id
        int hours
        date date
        string description
        string status
    }

    AwardCategory {
        int id
        string name
        string description
        int required_hours
    }

    Nomination {
        int id
        int student_id
        int teacher_id
        int category_id
        date date
        string reason
    }

    Student ||--o{ VolunteerHours : logs
    Student ||--o{ Nomination : submits
    Teacher ||--o{ Nomination : reviews
    AwardCategory ||--o{ Nomination : qualifies_for
    Admin ||--o{ AwardCategory : manages
```

Assumption: each volunteer-hour record belongs to one student; each nomination belongs to one student, one teacher, and one award category; admin manages categories but does not directly log hours or nominate students.

## Wireframes

Embed each student-crafted wireframe here (Phase 4). Paths are relative to this file:

```markdown
### Explore / Search Publications

![Explore / Search Publications](wireframes/explore.png)
```

`python manage.py report` also embeds any PNG/JPG still missing from `docs/wireframes/`.

## Theming

Branding preferences and how they were applied (landing / login / register).

## Implementation notes

One named workflow at a time. Include verify notes and polish / model revisions (Phase 5). Do not treat the first build as final.

## Deployed app

Phase 6. Public Render URL (not localhost). Markers open this to mark the three workflows.

https://

## Logins

Every account a marker needs, including extra users you added. Starter accounts:

- bob / bobpass — regular user
- admin / adminpass — admin

## YouTube URL

## Session transcripts

Filled when the Guide builds the report: the agent writes each Guide chat to `docs/transcripts/<slug>.md` (Copilot Agent, Cursor, or OpenCode). `python manage.py report` packages them. Do not paste chats here during the build.

## Competency (student-judge)

Filled when the report is built. Guide runs student-judge, writes `docs/judge.md`, and export appends the scorecard here.

## Skill integrity

Filled by `python manage.py report`. Do not edit the course skills.
