# AGENTS.md — Builder's Guide to the Learning Path Skill

> This document is for **developers extending or debugging** the skill. For user-facing usage, see [README.md](README.md).

---

## 1. Project Overview

Learning Path Generator is a Hermes Agent skill that acts as a personal AI tutor. It generates structured learning paths for any topic, delivers daily tasks via Telegram (cron-driven), evaluates submissions with a two-axis rubric, and adapts the plan based on performance.

The entire state machine lives in a single SQLite file. Cron jobs run with zero prior context — every prompt is self-contained with all SQL and decision logic inline. The skill is split into a router (SKILL.md) and four subskills loaded on demand to keep context lean for local models.

**Stack:** Hermes Agent + SQLite (WAL mode) + Telegram delivery + cron tool

---

## 2. Architecture Decisions

These are the non-obvious choices that shaped the skill. Understanding them prevents re-litigating solved problems.

| Decision | Choice | Why |
|----------|--------|-----|
| Persona embedded in SKILL.md | No separate Hermes profile | Cron jobs run on the default profile — Hermes has no `--profile` flag for cron. A separate profile would be cleaner but the cron layer doesn't support it. |
| Subskill router pattern | 4 subskills loaded on demand | A monolithic SKILL.md would be 500+ lines. Local models (Ollama) struggle with long prompts. The router keeps context ~180 lines; subskills load only when needed. |
| SQLite over JSON files | WAL mode, foreign keys | Concurrent access from cron + agent sessions. JSON would need manual locking and can't query. SQLite handles atomic writes natively. |
| Explicit `/submit` command | 20h window as fallback only | Without `/submit`, a casual question like "what is a lifetime in Rust?" gets evaluated as a task submission. The 20h window asks for confirmation before evaluating. |
| LLM outputs structured JSON for evals | JSON schema in prompt | Free-form text leads to inconsistent scoring. JSON forces the model to commit to numbers and specific feedback. Easier to parse, store, and compare across sessions. |
| Cron prompts include ALL SQL inline | ~500 lines per prompt | Cron sessions start with zero context — no conversation history, no loaded skills. Every query and decision branch must be in the prompt. |
| `init_db.py` is idempotent | Run on every cron invocation | Cron has no guarantee the DB exists. Running init every time is safe (it checks `schema_version` and exits early if already initialized). |

---

## 3. File Structure with Responsibilities

```
~/.hermes/skills/learning-path/
├── SKILL.md                  # Router — persona, rules, command dispatch, pitfalls
├── AGENTS.md                 # This file — builder's guide
├── README.md                 # User-facing documentation
├── LICENSE                   # MIT
├── .gitignore                # Ignores learning.db, __pycache__
│
├── subskills/
│   ├── init.md               # /tutor init flow: syllabus gen → URL validation → confirm → save
│   ├── daily.md              # Cron daily task: path check → inactivity → review check → task gen → deliver
│   ├── eval.md               # /submit flow: pending task → evaluate → score → decision → update state
│   └── adapt.md              # Weekly review + /tutor review: metrics → adaptation rules → report
│
├── templates/
│   ├── syllabus.md           # Syllabus presentation format (sent to user for review)
│   ├── daily-task.md         # Daily task Telegram format
│   ├── evaluation.md         # Full rubric + JSON output schema for evaluations
│   ├── weekly-report.md      # Weekly report template
│   └── milestone.md          # Module completion celebration message
│
├── scripts/
│   ├── init_db.py            # Idempotent DB initialization. Creates all tables + default config.
│   └── migrate_db.py         # Schema migration engine. Runs ALTER TABLE based on version delta.
│
└── learning.db               # Runtime state — created by init_db.py, ignored by git
```

### What Each File Does NOT Do

| File | Does NOT |
|------|----------|
| `SKILL.md` | Does NOT contain task generation logic, evaluation logic, or SQL for daily operations — it delegates to subskills |
| `init.md` | Does NOT handle evaluation or daily task delivery — only syllabus creation and path activation |
| `daily.md` | Does NOT evaluate submissions — it only generates and delivers tasks |
| `eval.md` | Does NOT generate tasks — it only evaluates submitted responses |
| `adapt.md` | Does NOT evaluate or generate tasks — it only reviews weekly metrics and adjusts the path |
| `init_db.py` | Does NOT migrate — use `migrate_db.py` for schema changes |
| `migrate_db.py` | Does NOT create a fresh DB — use `init_db.py` first |
| Templates | Do NOT contain logic — they are formatting only |

---

## 4. State Model

Everything lives in SQLite at `~/.hermes/skills/learning-path/learning.db`.

### Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `config` | Global runtime state (KV store) | `key`, `value` |
| `paths` | One row per learning path | `id`, `topic`, `status`, `is_active`, `confirmed`, `created`, `completed` |
| `modules` | Modules within a path | `id`, `path_id` (FK), `title`, `description`, `module_order`, `status`, `score`, `score_avg`, `next_review_date`, `times_repeated`, `started`, `completed` |
| `daily_tasks` | Individual task assignments | `id`, `module_id` (FK), `date`, `content`, `response`, `feedback`, `score`, `awaiting_response`, `response_window_end`, `skipped` |
| `resources` | URLs per module | `id`, `module_id` (FK), `url`, `title`, `type`, `verified` |
| `schema_version` | Migration tracking | `version` |

### Critical Config Keys

These are the keys that drive the state machine. Query them before making decisions.

| Key | Type | Purpose |
|-----|------|---------|
| `active_path_id` | int as string | Which path is currently active. Empty = no active path. |
| `pending_task_id` | int as string | ID of the task awaiting a response. Empty = no pending task. |
| `response_window_end` | datetime string | When the submission window closes (task creation + 20h). |
| `last_task_date` | date string | When the last daily task was sent. Prevents duplicate sends. |
| `last_response_date` | date string | When the user last submitted. Drives inactivity logic. |
| `daily_count` | int as string | Total daily tasks sent (incremented each send). |
| `weekly_count` | int as string | Total weekly reviews sent. |

### Module Status Lifecycle

```
pending → in_progress → completed
                    ↘ (score < 4.0) → pending (decomposed into sub-modules first)
                    ↘ (score 4.0-6.9) → stays in_progress (repeat with new task)
```

Completed modules with `next_review_date` set are picked up by the daily cron for spaced repetition review.

### Path Status Lifecycle

```
active → paused → active (resume)
                 → completed (all modules done)
```

---

## 5. Cron Behavior

Cron jobs are the backbone of the daily workflow. They run in a fresh session with **zero prior context** — no loaded skills, no conversation history.

### Why Crons Start Blank

Hermes cron jobs invoke a new agent session. The only input is the `prompt` field from the cronjob tool. This means:
- The prompt must be fully self-contained
- All SQL queries must be written out in the prompt
- All decision branches must be explicit
- The agent must call `skill_view("learning-path")` or have the logic inlined

In practice, the cron prompts include the full subskill content (daily.md or adapt.md) directly in the prompt text.

### Daily Task Cron

- **Schedule:** 9:00 AM daily (`0 9 * * *`)
- **Deliver:** `telegram`
- **Prompt:** Contains all steps from `subskills/daily.md` verbatim
- **Conditions that stop it:**
  - No `active_path_id` → sends "no active path" message, ends
  - Path status is `paused` → ends silently (no message)
  - `last_task_date` = today → ends silently (already sent)
  - 5+ days inactive → auto-pauses, sends notification, ends
  - All modules completed → sends completion message, ends

### Weekly Review Cron

- **Schedule:** Sundays at 22:00 (`0 22 * * 0`)
- **Deliver:** `telegram`
- **Prompt:** Contains all steps from `subskills/adapt.md` verbatim
- **Conditions that stop it:**
  - No `active_path_id` → ends silently
  - Path status is `paused` → ends silently

### Creating Cron Jobs

Cron jobs are created automatically during the `/confirm` step of `init.md`. The agent calls `cronjob(action="create")` with the full prompt. You should NOT try to create them via `hermes cron create` in the CLI — the prompts are ~500 lines each and the CLI isn't practical for that.

If cron jobs need to be recreated, ask the agent in a chat session:
> "Create the cron jobs for the learning-path skill: daily at 9 AM and weekly review Sundays at 10 PM, deliver to telegram."

---

## 6. Evaluation Flow

This is the most complex state transition. Here's the complete path from user message to database update.

### Step-by-Step

```
User message arrives
  │
  ├─ Starts with "/submit"? → eval.md Step 1
  │
  └─ Free text?
       │
       ├─ pending_task_id is set AND within 20h window?
       │    → Ask: "Is this your submission? Reply yes or /submit <response>"
       │    → User confirms → eval.md Step 1
       │
       └─ No pending task OR outside window
            → Treat as normal conversation
```

### Evaluation Pipeline

1. **Fetch pending task** — `SELECT ... FROM daily_tasks WHERE awaiting_response=1 AND skipped=0`
2. **Check window** — if past `response_window_end` and not explicit `/submit`, reject
3. **LLM evaluation** — prompt with task content + student response + rubric from `templates/evaluation.md`
4. **Parse JSON** — extract `conceptual_comprehension`, `application_ability`, `score`, `decision`, `feedback`, `strengths`, `improvements`, `next_review_days`
5. **Apply decision:**
   - `score >= 7.0` → ADVANCE: mark module `completed`, set `next_review_date`, celebrate if milestone
   - `score 4.0-6.9` → REPEAT: module stays `in_progress`, new task next session
   - `score < 4.0` → DECOMPOSE: insert 2-3 sub-modules after current, shift `module_order`, reset current to `pending`
6. **Save evaluation** — update `daily_tasks` with response, feedback, score; clear `awaiting_response`
7. **Update config** — set `last_response_date`, clear `pending_task_id`
8. **Check adaptation triggers** (v1.1): 2 consecutive low scores → extra resource; 3 consecutive >= 9 → offer acceleration

### JSON Schema (LLM must output this exactly)

```json
{
  "conceptual_comprehension": <1-10>,
  "application_ability": <1-10>,
  "score": "<average, 1 decimal>",
  "decision": "<advance|repeat|decompose>",
  "feedback": "<specific, 2-4 sentences>",
  "strengths": ["<specific>"],
  "improvements": ["<specific>"],
  "next_review_days": <1|3|7>
}
```

If JSON parsing fails, retry once. If it fails again, ask the user to resubmit and log the error.

---

## 7. How to Add Features

### New Subskill vs Extending an Existing One

**Add a new subskill when:**
- The feature has its own trigger (new command or new cron schedule)
- It adds significant logic (>30 lines) that doesn't belong in an existing subskill
- It has its own state transitions

**Extend an existing subskill when:**
- It's a modification to an existing flow (e.g., adding a new adaptation rule goes in `adapt.md`)
- It's a new field in the evaluation output (goes in `eval.md` + `templates/evaluation.md`)
- It's a new check in the daily flow (goes in `daily.md`)

### Adding a New Column to the Database

1. **Do NOT modify `init_db.py`** — that's for fresh installs only
2. **Edit `migrate_db.py`:**
   - Increment `EXPECTED_VERSION`
   - Add a migration entry:
     ```python
     MIGRATIONS = {
         # ... existing ...
         2: [
             "ALTER TABLE modules ADD COLUMN difficulty TEXT DEFAULT 'medium'",
         ],
     }
     ```
3. **Update `init_db.py` SCHEMA** to include the new column for fresh installs
4. **Update `SCHEMA_VERSION` in `init_db.py` to match `EXPECTED_VERSION`**
5. **Run migration:** `python3 ~/.hermes/skills/learning-path/scripts/migrate_db.py`
6. **Update all subskills** that reference the affected table

### Adding a New Command

1. Add the command to the ROUTER table in `SKILL.md`
2. Either:
   - Create a new subskill file in `subskills/` and reference it
   - Add inline logic in SKILL.md (for simple commands like `/tutor skip`)
3. Add the command to the README.md command table
4. Test the full flow manually

### Updating a Cron Prompt

Cron prompts are the full text of a subskill file. When you modify `daily.md` or `adapt.md`:

1. Edit the subskill file
2. The existing cron jobs still have the OLD prompt — they are NOT auto-updated
3. Delete old cron jobs and recreate them:
   ```
   Ask the agent: "Recreate the learning-path cron jobs with the updated prompts."
   ```
4. Verify with `cronjob(action="list")` that the new prompts are active

### Adding a Template

1. Create `templates/<name>.md`
2. Reference it in the subskill that uses it
3. Templates are formatting only — no logic, no SQL

---

## 8. Known Limitations & Gotchas

### Critical

- **`hermes skill list` does not exist.** The correct command is `hermes skills list` (plural). This trips up every new session.
- **`hermes cron create` from CLI is impractical for this skill.** The cron prompts are ~500 lines each. Always use the `cronjob` tool programmatically or ask the agent to create them.
- **Spaced repetition is implemented but NOT validated end-to-end.** The logic exists in `daily.md` (step 5: review check) and `eval.md` (step 5: setting `next_review_date`), but no full cycle (init → submit → eval → advance → review task) has been tested. This is the top priority for v1.1.
- **`mixture_of_agents` is unreliable for structured JSON.** Use `delegate_task` instead for syllabus generation. MoA tends to produce free-form text that breaks JSON parsing.
- **Don't inline complex Python with JSON in f-strings.** When saving to SQLite from `execute_code`, the backslash/quote escaping breaks. Write the script to a temp file (e.g., `/tmp/init_path.py`) then run it with `terminal`.

### Operational

- **Cron prompts are NOT auto-synced.** Editing a subskill file does NOT update running cron jobs. You must manually recreate them.
- **The `/confirm` step should auto-create cron jobs.** Currently depends on the agent having access to the `cronjob` tool during init. If the tool isn't available, cron jobs won't be created.
- **URL verification is async.** The init flow validates URLs with HEAD requests (`curl -sI`), but some URLs may be temporarily down. Unverified URLs are flagged but don't block path creation.
- **`learning.db` is gitignored.** The DB is runtime state. To reset everything, delete the file and run `init_db.py`.
- **No multi-device sync.** Single SQLite file means single machine. Progress sync across devices is a v2.0 goal.

### Model-Specific

- **Evaluation quality depends on model instruction-following.** Tested with glm-5.1. Local models via Ollama may need shorter prompts or simplified rubrics.
- **LLM may hallucinate URLs in syllabi.** The HEAD request validation mitigates this, but it's not foolproof (temporarily down servers, redirect chains).
- **The JSON schema for evaluations must be exact.** If the model adds extra fields or changes the structure, parsing fails. The retry-once logic handles most cases.

---

## 9. Testing Checklist

When making changes, manually verify these flows:

### Init Flow
- [ ] `/tutor init <topic>` generates a syllabus with valid JSON
- [ ] URLs are verified with HEAD requests
- [ ] `/confirm` saves to SQLite and sets `active_path_id`
- [ ] `/edit <feedback>` regenerates incorporating feedback
- [ ] Duplicate init with existing active path prompts user to pause first

### Daily Task Flow
- [ ] Cron job at 9 AM generates and delivers a task
- [ ] No duplicate tasks on same day (`last_task_date` guard)
- [ ] Inactive path → silent exit
- [ ] No active path → "no active path" message
- [ ] Inactivity escalation: 2 days nudge → 3 days offer pause → 5 days auto-pause
- [ ] All modules completed → path completion message

### Evaluation Flow
- [ ] `/submit <response>` triggers evaluation
- [ ] Free text within 20h window → confirmation prompt
- [ ] Free text outside window → treated as conversation
- [ ] Score >= 7.0 → ADVANCE: module status = completed
- [ ] Score 4.0-6.9 → REPEAT: module stays in_progress
- [ ] Score < 4.0 → DECOMPOSE: sub-modules inserted, orders shifted
- [ ] Evaluation JSON parses correctly
- [ ] Failed JSON parse → retry once
- [ ] `pending_task_id` cleared after evaluation
- [ ] `last_response_date` updated

### Weekly Review Flow
- [ ] Cron job on Sunday 22:00 sends weekly report
- [ ] Metrics calculated correctly (tasks sent, completed, skipped, avg score)
- [ ] Adaptation rules fire correctly (>50% skipped, avg < 5.0, avg > 8.0)
- [ ] Obsidian export works when `OBSIDIAN_VAULT_PATH` is set
- [ ] Silent exit when no active path

### State Management
- [ ] `init_db.py` is idempotent — running twice doesn't break anything
- [ ] `migrate_db.py` handles version upgrades correctly
- [ ] `migrate_db.py` is idempotent — running at current version exits early
- [ ] `/tutor pause` clears `active_path_id`
- [ ] `/tutor resume` restores most recently paused path
- [ ] `/tutor skip` clears `pending_task_id`

### Spaced Repetition (when validated)
- [ ] Completed module gets `next_review_date` set
- [ ] Daily cron picks up modules due for review
- [ ] Review task focuses on weak areas from past evaluations
- [ ] Review increments `times_repeated` and updates `score_avg`

---

## 10. Roadmap

### v1.1 — In Progress

| Feature | Status | What's Needed |
|---------|--------|---------------|
| Spaced repetition validated end-to-end | Logic exists, untested | Full manual cycle: init → advance a module → wait for review date → verify daily cron picks it up |
| Multi-path with `/tutor switch` | SQL written, untested | Create 2 paths, deactivate one, switch between them |
| Adaptation triggers | Code in eval.md step 9 | Test: 2 consecutive low scores → resource added; 3 consecutive >= 9 → acceleration offered |
| Milestone celebrations | Template exists | Verify `templates/milestone.md` renders correctly in Telegram |

### v2.0 — Planned

| Feature | Notes |
|---------|-------|
| Configurable delivery time | Currently hardcoded 9 AM. Could be stored in `config` table with user timezone. |
| Multi-language support | Beyond Spanish/English. Needs template system per language. |
| Local model optimized prompts | Shorter subskills, simplified rubrics for 7B-13B models. |
| Progress sync across devices | Needs a sync layer (could use git, could use a remote DB). |
| Rich task types | Currently text-only. Could add: code execution and test, diagram drawing, fill-in-the-blank. |
| Prerequisites graph | DAG of module dependencies instead of linear order. |

### Contributing Guidelines

1. Edit subskills, not SKILL.md (unless adding a command to the router)
2. Always update both `init_db.py` (for fresh installs) and `migrate_db.py` (for existing DBs)
3. Test the checklist above before committing
4. Cron prompts must be self-contained — assume zero context
5. Keep SKILL.md under 200 lines; if it grows, extract a new subskill
