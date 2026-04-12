# Architecture

**Analysis Date:** 2026-04-12

## Pattern Overview

**Overall:** Prompt-driven state machine with subskill router pattern, backed by SQLite and delivered via cron-triggered Telegram messages.

**Key Characteristics:**
- The entire application is a **Hermes Agent skill** — not a traditional code application. Logic lives in Markdown files (prompts), not in compiled code.
- **DB is truth.** Every operation queries SQLite before acting. No in-memory state is trusted.
- **Cron sessions are stateless.** Every cron invocation starts with zero context — all SQL, decision branches, and logic must be fully inlined in the prompt.
- **Subskill router** pattern keeps the main prompt (~180 lines) lean for local models (Ollama). Heavy logic loads on demand.

## Layers

**Router Layer (Command Dispatch):**
- Purpose: Receives user commands and routes to the appropriate subskill or inline handler
- Location: `SKILL.md`
- Contains: Persona definition, rules, command dispatch table, inline SQL for simple commands (status, skip, pause, resume, switch, export)
- Depends on: `subskills/*.md` for complex flows, `scripts/init_db.py` for DB initialization
- Used by: Hermes Agent runtime (loaded when the skill is invoked)

**Subskill Layer (Domain Logic):**
- Purpose: Contains the step-by-step logic for each major workflow
- Location: `subskills/`
- Contains: Four subskills, each with trigger conditions, SQL queries, LLM prompts, and decision trees
- Depends on: `templates/*.md` for output formatting, `scripts/*.py` for DB operations
- Used by: Router layer (loaded on demand), cron jobs (inlined verbatim into cron prompts)

**Template Layer (Output Formatting):**
- Purpose: Defines presentation formats for user-facing messages
- Location: `templates/`
- Contains: Format templates for syllabi, daily tasks, evaluations, weekly reports, and milestones
- Depends on: Nothing (pure formatting)
- Used by: Subskills (init.md, daily.md, eval.md, adapt.md)

**Infrastructure Layer (Scripts):**
- Purpose: Python utilities for database initialization, schema migration, and URL validation
- Location: `scripts/`
- Contains: `init_db.py` (idempotent DB setup), `migrate_db.py` (schema versioning), `validate_urls.py` (tier-based URL checking)
- Depends on: Python 3.11+, SQLite3 stdlib, curl (for HTTP checks)
- Used by: Subskills (init.md calls init_db.py and validate_urls.py)

**State Layer (SQLite Database):**
- Purpose: Single source of truth for all application state
- Location: `learning.db` (gitignored, created at runtime)
- Contains: 6 tables — `config`, `paths`, `modules`, `daily_tasks`, `resources`, `schema_version`
- Depends on: Nothing
- Used by: All layers — router, subskills, and scripts

## Data Flow

**Learning Path Initialization Flow (`/tutor init <topic>`):**

1. User sends `/tutor init <topic>` to Hermes Agent via Telegram
2. Hermes loads `SKILL.md`, router matches command to `subskills/init.md`
3. `init.md` Step 0: Ensure DB exists via `scripts/init_db.py`
4. `init.md` Step 1: Check for existing active path in SQLite
5. `init.md` Step 2: Research phase — delegate web searches for real resources using `delegate_task` with `web_search`
6. `init.md` Step 3: LLM generates structured JSON syllabus incorporating research results
7. `init.md` Step 4: Validate URLs via `scripts/validate_urls.py` (tier classification + HTTP check)
8. `init.md` Step 5: Present syllabus to user using `templates/syllabus.md` format
9. User sends `/tutor confirm` or `/tutor edit <feedback>`
10. `init.md` Step 7: Save syllabus to SQLite (paths, modules, resources tables)
11. `init.md` Step 8: Create cron jobs (`tutor-daily` at 9 AM, `tutor-weekly` Sundays 10 PM) with full subskill content inlined as cron prompts
12. Send confirmation message to user

**Daily Task Delivery Flow (Cron):**

1. Cron job triggers at 9:00 AM daily with the full text of `subskills/daily.md` as the prompt
2. `daily.md` Step 1: Ensure DB exists via `scripts/init_db.py`
3. `daily.md` Step 2: Check for `active_path_id` in config — if missing, exit silently
4. `daily.md` Step 3: Check for existing `awaiting_response` task — if exists, skip
5. `daily.md` Step 4: Find next module with status `pending` or `in_progress`
6. `daily.md` Step 5: Retrieve resources for that module
7. `daily.md` Step 6: LLM generates a specific daily task based on module content and resources
8. `daily.md` Step 7: Save task to `daily_tasks` table, set `pending_task_id` in config
9. `daily.md` Step 8: Format and deliver task via Telegram using `templates/daily-task.md` format

**Task Evaluation Flow (`/tutor submit <response>`):**

1. User sends `/tutor submit <response>` or confirms free-text as submission
2. Hermes loads `SKILL.md`, router matches to `subskills/eval.md`
3. `eval.md` Step 1: Fetch pending task from `daily_tasks` where `awaiting_response=1`
4. `eval.md` Step 2: LLM evaluates submission using rubric from `templates/evaluation.md`, outputs structured JSON
5. `eval.md` Step 3: Save evaluation (response, score, feedback) to `daily_tasks`, clear `awaiting_response`
6. `eval.md` Step 4: Calculate module average score from all task scores
7. `eval.md` Step 5: Apply decision based on score:
   - `>= 7.0` ADVANCE: mark module completed, set `next_review_date`
   - `4.0-6.9` REPEAT: module stays `in_progress`, increment `times_repeated`
   - `< 4.0` DECOMPOSE: insert 2-3 sub-modules after current, shift `module_order`
8. `eval.md` Step 6: Send feedback to user via Telegram

**State Management:**
- All state is in SQLite at `~/.hermes/skills/tutor/learning.db` (WAL mode for concurrent access)
- The `config` table acts as a key-value store for runtime state (`active_path_id`, `pending_task_id`, `last_response_date`, etc.)
- No in-memory state is maintained between sessions — every interaction starts from the DB
- Module lifecycle: `pending` -> `in_progress` -> `completed` (with `decompose` branching for low scores)
- Path lifecycle: `draft` -> `active` -> `paused` -> `active` (or `completed`)

## Key Abstractions

**Subskill (On-Demand Logic Module):**
- Purpose: A self-contained unit of domain logic loaded only when its trigger fires
- Examples: `subskills/init.md`, `subskills/eval.md`, `subskills/daily.md`, `subskills/adapt.md`
- Pattern: Each subskill has a trigger condition, numbered steps with inline SQL, LLM prompts, and error handling. The subskill is either loaded by the router (interactive session) or inlined verbatim into a cron prompt (stateless cron session).

**Tier System (URL Reliability Classification):**
- Purpose: Ensures learning resources come from trustworthy, stable sources
- Examples: `scripts/validate_urls.py` (TIER_PATTERNS dict), `SKILL.md` (tier rules table)
- Pattern: Four-tier classification (TIER 1: interactive platforms, TIER 2: official courses, TIER 3: YouTube single videos, TIER 4: reference). Minimum 50% TIER 1 per module. YouTube playlists are rejected. URLs are validated by regex pattern matching and optional HTTP HEAD checks.

**Evaluation Rubric (Two-Axis Scoring):**
- Purpose: Provides consistent, evidence-based scoring of task submissions
- Examples: `templates/evaluation.md`, `subskills/eval.md`
- Pattern: Two 1-10 scores (Conceptual Comprehension, Application Ability) averaged to produce a final score. Score drives decision: advance, repeat, or decompose. LLM outputs a strict JSON schema that is parsed and stored.

**Spaced Repetition Scheduler:**
- Purpose: Schedules review of completed modules at increasing intervals
- Examples: `subskills/daily.md` (Step 5 review check), `templates/evaluation.md` (next_review_days)
- Pattern: Based on evaluation score, `next_review_date` is set (7 days for >= 8.0, 3 days for 5.0-7.9, 1 day for < 5.0). Daily cron checks for modules due for review. Implemented but not yet validated end-to-end.

## Entry Points

**Interactive Entry (User Commands via Telegram):**
- Location: `SKILL.md` (router), loaded by Hermes Agent when user sends a message starting with `/tutor`
- Triggers: Any message containing `/tutor <command>` or free text that matches trigger patterns (e.g., "quiero aprender <topic>")
- Responsibilities: Command parsing, subskill loading, inline command execution (status, skip, pause, resume, switch, export), error reporting

**Cron Entry (Daily Task Delivery):**
- Location: `subskills/daily.md` (inlined verbatim into cron prompt)
- Triggers: Cron schedule `0 9 * * *` (9 AM daily)
- Responsibilities: DB health check, active path verification, duplicate prevention, inactivity handling, task generation, Telegram delivery
- Critical: Must be fully self-contained — zero prior context, all SQL and decisions inlined

**Cron Entry (Weekly Review):**
- Location: `subskills/adapt.md` (inlined verbatim into cron prompt)
- Triggers: Cron schedule `0 22 * * 0` (Sundays 10 PM)
- Responsibilities: Performance metrics aggregation, adaptation rule evaluation, weekly report generation, Obsidian export
- Critical: Must be fully self-contained — zero prior context

**Script Entry (DB Initialization):**
- Location: `scripts/init_db.py`
- Triggers: Called at the start of every cron job and `/tutor init` flow
- Responsibilities: Creates all tables if they don't exist, inserts default config values, idempotent (safe to run repeatedly)

**Script Entry (Schema Migration):**
- Location: `scripts/migrate_db.py`
- Triggers: Manual invocation when schema changes are needed
- Responsibilities: Compares `schema_version` in DB with `EXPECTED_VERSION`, runs ALTER TABLE statements for version deltas

## Error Handling

**Strategy:** Graceful degradation with explicit error reporting. The LLM agent handles most errors by checking DB state before acting and reporting issues to the user.

**Patterns:**
- **DB-first verification:** Every operation queries SQLite before acting. If the DB query fails or returns unexpected results, the agent reports it (per SKILL.md Rule 3).
- **Idempotent initialization:** `scripts/init_db.py` uses `CREATE TABLE IF NOT EXISTS` and `INSERT OR IGNORE` — safe to run on every cron invocation.
- **JSON parse retry:** If LLM outputs invalid JSON during evaluation, retry once with explicit instruction. If it fails again, ask the user to resubmit.
- **URL validation loop:** If generated syllabus fails URL validation (>30% invalid), regenerate with more conservative sources rather than proceeding with broken URLs.
- **Silent cron exits:** When no active path exists or path is paused, the daily cron exits silently with no output — no error message, no Telegram notification.
- **Partial state prevention:** If DB write fails during path creation, report to user rather than leaving partial data. Do NOT commit partial transactions.

## Cross-Cutting Concerns

**Persona:** Defined in `SKILL.md` — "Hermilio Tutor" persona with specific behavioral rules (patient, rigorous, encouraging, direct, no filler). Language matches the user's (default Spanish).

**Validation:** URL validation via `scripts/validate_urls.py` with regex-based tier classification and optional HTTP HEAD checks. Tier balance enforced (minimum 50% TIER 1 per module). YouTube playlists explicitly rejected.

**Authentication:** Handled by the Hermes Agent platform. The skill itself has no authentication — it trusts the Hermes runtime to identify the user. The Telegram gateway provides the delivery channel.

**Localization:** User's language is matched dynamically. Templates default to Spanish but adapt to the user. The evaluation rubric requires feedback in the user's language.

**Delivery:** Telegram is the primary delivery channel. Cron jobs specify `deliver: telegram`. Quiet hours enforced (00:00-08:00 no messages). Obsidian export available as secondary output.

---

*Architecture analysis: 2026-04-12*
