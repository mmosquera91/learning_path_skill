# External Integrations

**Analysis Date:** 2026-04-12

## APIs & External Services

**Message Delivery:**
- Telegram — Primary communication channel for all user interaction
  - Client: Hermes Agent's built-in `telegram` deliver channel
  - Auth: Configured in Hermes framework (`~/.hermes/config.yaml`, `~/.hermes/.env`)
  - Usage: Daily task delivery, evaluation feedback, weekly reports, milestone celebrations, status queries
  - Delivery trigger: Hermes cron jobs and real-time agent responses
  - Quiet hours enforced: 00:00-08:00 (no messages sent)

**Web Search (Resource Discovery):**
- Web search API — Used during `/tutor init` to find real learning resources
  - Client: Hermes `delegate_task` tool with `web_search` capability
  - Usage: 5 parallel search queries per init to find syllabus resources across different source tiers
  - Flow: Search results are captured with exact URLs and titles, then passed to LLM for syllabus generation
  - Referenced in: `subskills/init.md` Step 2

**LLM (Language Model):**
- Configured model via Hermes Agent — Powers all generative logic
  - Usage: Syllabus generation (structured JSON), daily task content generation, student response evaluation (JSON with rubric scores), weekly adaptation analysis
  - Evaluation output schema defined in: `templates/evaluation.md`
  - Syllabus output schema defined in: `subskills/init.md` Step 3
  - Task output schema defined in: `subskills/daily.md` Step 6

## Data Storage

**Databases:**
- SQLite (local file)
  - Location: `~/.hermes/skills/tutor/learning.db`
  - Client: Python `sqlite3` standard library
  - Mode: WAL (Write-Ahead Logging) for concurrent access from cron + agent sessions
  - Foreign keys: Enabled
  - Busy timeout: 5000ms
  - Initialization: `scripts/init_db.py` (idempotent)
  - Migration: `scripts/migrate_db.py` (version-tracked, currently at version 1)
  - Tables: `config`, `paths`, `modules`, `daily_tasks`, `resources`, `schema_version`
  - Gitignored: Yes (runtime state, not committed)

**File Storage:**
- Local filesystem only
  - Obsidian vault export: `$OBSIDIAN_VAULT_PATH/Learning/{topic}-journey.md` or fallback `~/Learning/{topic}-journey.md`
  - Temporary files: `/tmp/syllabus.json`, `/tmp/init_path.py` (used during init flow, not persisted)
  - Referenced in: `SKILL.md` (export command), `subskills/init.md` Step 7

**Caching:**
- None. Every cron run starts from the database with zero prior context.

## Authentication & Identity

**Auth Provider:**
- Hermes Agent framework — User identity and session management handled by Hermes
  - Implementation: Single-user system tied to the Hermes session. The skill does not implement its own authentication.
  - User identification: Implicit via the Telegram chat session associated with the Hermes instance.

## Monitoring & Observability

**Error Tracking:**
- None. Errors are reported to the user via Telegram messages.

**Logs:**
- Hermes framework handles its own logging at `~/.hermes/logs/`
- No application-specific logging in the Python scripts (only `print()` for CLI output)
- Cron job output stored at `~/.hermes/cron/output/`

## CI/CD & Deployment

**Hosting:**
- Local execution only. Runs on the same machine as the Hermes Agent gateway. No server deployment.

**CI Pipeline:**
- None. The project uses git version control but has no CI/CD configuration (no `.github/workflows/`, no Makefile, no deployment scripts).

**Installation:**
- Placed as a directory under `~/.hermes/skills/tutor/`
- Auto-discovered by Hermes as a skill based on `SKILL.md` presence
- Database initialized on first use via `scripts/init_db.py`

## Environment Configuration

**Required env vars:**
- None required by the skill itself. The Hermes framework may require its own env vars for Telegram bot tokens and LLM API keys.

**Optional env vars:**
- `OBSIDIAN_VAULT_PATH` — Path to Obsidian vault for learning journey export (default: `$HOME/Documents/Obsidian Vault`)

**Secrets location:**
- `~/.hermes/.env` — Hermes framework secrets (not managed by this skill)
- `~/.hermes/auth.json` — Hermes authentication (not managed by this skill)

**Hermes Configuration:**
- `~/.hermes/config.yaml` — Main Hermes config (cron schedules, channels, model settings)
- `~/.hermes/cron/jobs.json` — Cron job definitions (created programmatically by the skill during `/tutor confirm`)

## Webhooks & Callbacks

**Incoming:**
- Telegram messages via Hermes gateway — The skill receives messages through Hermes, which acts as the Telegram bot interface. No direct webhook configuration.
- Cron triggers — Two Hermes cron jobs invoke the skill with pre-built prompts:
  1. `tutor-daily` — Schedule `0 9 * * *`, uses `subskills/daily.md` content as prompt
  2. `tutor-weekly` — Schedule `0 22 * * 0`, uses `subskills/adapt.md` content as prompt

**Outgoing:**
- Telegram messages via Hermes `telegram` deliver channel — All user-facing output is sent as Telegram messages
- HTTP HEAD requests via curl — URL validation during init flow (`scripts/validate_urls.py` calls `curl -sI` against resource URLs)

## Inter-Module Communication

**Subskill Loading Pattern:**
- The skill uses a router pattern: `SKILL.md` dispatches commands to subskills
- Subskills are loaded on demand by the Hermes Agent when a matching command is detected
- Communication is synchronous: the agent reads the subskill Markdown file, follows its steps, and returns the result

**Cron-to-Skill Communication:**
- Cron jobs include the FULL subskill content in their prompt (no file loading)
- This is because cron sessions start with zero context — no loaded skills, no conversation history
- The `cronjob(action="create")` tool stores the prompt at registration time
- Editing a subskill file does NOT update running cron jobs — they must be recreated

**Database-as-Message-Bus:**
- The SQLite `config` table acts as the state machine's message bus between sessions
- Key state keys: `active_path_id`, `pending_task_id`, `last_response_date`, `last_task_date`, `streak_count`, `daily_count`, `weekly_count`, `response_window_end`
- Each session (interactive or cron) reads config, performs actions, writes config back
- No locking mechanism beyond SQLite's built-in WAL mode and busy timeout (5000ms)

---

*Integration audit: 2026-04-12*
