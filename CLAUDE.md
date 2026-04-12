<!-- GSD:project-start source:PROJECT.md -->
## Project

**Tutor Skill Hardening**

The Hermes Agent "Tutor" skill — a prompt-driven learning path system that creates personalized syllabi, delivers daily tasks via Telegram, evaluates submissions with a rubric, and adapts over time. Built as a Hermes skill with Markdown subskills, Python utility scripts, and a SQLite state backend.

**Core Value:** The Tutor skill reliably delivers a daily learning task, evaluates the user's submission, and progresses through the learning path — every day, without silent failures or broken state.

### Constraints

- **Runtime**: Hermes Agent — all logic must remain in Markdown files interpreted by the agent, not compiled code
- **Cron constraint**: Cron sessions have zero context — all logic must be self-contained when inlined
- **State**: SQLite is the single source of truth — no in-memory state between sessions
- **Language**: Python 3.11+ stdlib only (no external dependencies)
- **Delivery**: Telegram via Hermes deliver channel — no custom API integration
- **Single user**: One user, one machine — no multi-user or cross-device concerns
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.11 — Database initialization (`scripts/init_db.py`, `scripts/migrate_db.py`), URL validation (`scripts/validate_urls.py`), and inline DB operations within subskill prompts
- Markdown — All skill logic, subskills, templates, and documentation. The entire application logic lives in Markdown files interpreted by the Hermes Agent runtime.
- SQL (SQLite dialect) — Inline SQL queries embedded in subskill Markdown files for all CRUD operations
- Mustache-like template syntax — Used in `templates/*.md` files (`{{variable}}`, `{{#section}}`)
## Runtime
- Hermes Agent (v0.7+) — AI agent framework that interprets Markdown skill files and executes tools (cron, terminal, delegate_task, etc.)
- Python 3.11 — For script execution
- Bash — For running Python scripts, curl commands, and file operations
- None. This project has no `package.json`, `requirements.txt`, `pyproject.toml`, or equivalent. All Python code uses only the standard library (`sqlite3`, `json`, `subprocess`, `argparse`, `re`, `os`, `sys`, `pathlib`, `datetime`, `urllib.parse`).
## Frameworks
- Hermes Agent Skill System — The entire application is a "skill" within the Hermes Agent framework. The skill is defined by `SKILL.md` (router/persona) with subskills loaded on demand.
- SQLite 3.50.4 (via Python `sqlite3` standard library module) — WAL mode enabled in migrations, foreign keys enforced
- pytest — Referenced in `CONTRIBUTING.md` (`python3 -m pytest scripts/test_validate_urls.py -v`), but no test files currently exist in the repository
- None. This is a zero-dependency skill. No build step, no compilation, no bundling.
## Key Dependencies
- `sqlite3` — Database operations (built-in)
- `json` — JSON parsing for LLM evaluation output and syllabus data (built-in)
- `subprocess` — Running curl for URL validation (built-in)
- `argparse` — CLI argument parsing for validate_urls.py (built-in)
- `re` — URL pattern matching for tier classification (built-in)
- `urllib.parse` — URL parsing (built-in)
- `pathlib` / `os` — File path handling (built-in)
- `datetime` — Timestamp generation (built-in)
- `curl` (system package, 8.5.0) — Used by `scripts/validate_urls.py` for HTTP HEAD requests to verify resource URLs
- `hermes` (system-level) — The Hermes Agent runtime that loads and executes skill files
- Telegram API — Message delivery via Hermes `telegram` deliver channel
- Web search — Resource discovery via Hermes `delegate_task` with `web_search` tool
- LLM — Syllabus generation, task generation, and evaluation via Hermes agent's configured model
## Configuration
- No `.env` file required by the skill itself. The Hermes framework may have its own configuration at `~/.hermes/config.yaml` and `~/.hermes/.env`.
- Database path is hardcoded: `~/.hermes/skills/tutor/learning.db`
- Obsidian vault path is configurable via `OBSIDIAN_VAULT_PATH` environment variable, falling back to `$HOME/Documents/Obsidian Vault`
- No build configuration. Files are plain Markdown and Python scripts.
- Cron jobs are registered via Hermes `cronjob(action="create")` tool with schedule expressions (`0 9 * * *` for daily, `0 22 * * 0` for weekly)
- Skill auto-registers as `/tutor` based on directory name
- Delivery channel: `telegram`
## Platform Requirements
- Python 3.11+ (only standard library needed)
- curl (for URL validation)
- Hermes Agent v0.7+ runtime for execution
- A running Hermes gateway with Telegram channel configured
- Hermes Agent runtime (same machine, no deployment)
- SQLite database at `~/.hermes/skills/tutor/learning.db`
- Cron job scheduler within Hermes (2 cron jobs: daily task delivery, weekly review)
- Telegram bot integration via Hermes
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Project Type
## Naming Patterns
- Skill router: `SKILL.md` (uppercase, root level)
- Subskills: `kebab-case.md` in `subskills/` -- e.g., `init.md`, `daily.md`, `eval.md`, `adapt.md`
- Templates: `kebab-case.md` in `templates/` -- e.g., `daily-task.md`, `weekly-report.md`, `evaluation.md`
- Python scripts: `snake_case.py` in `scripts/` -- e.g., `init_db.py`, `migrate_db.py`, `validate_urls.py`
- Documentation: `UPPERCASE.md` for project docs (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`)
- `subskills/` -- command-specific prompt files loaded on demand by the router
- `templates/` -- formatting-only Markdown templates for Telegram output
- `scripts/` -- Python utility scripts for database and URL validation
- `snake_case` -- e.g., `daily_tasks`, `schema_version`, `active_path_id`
- Config keys: `snake_case` -- e.g., `active_path_id`, `pending_task_id`, `last_response_date`
- Mustache-style: `{{variable_name}}` with sections `{{#section}}...{{/section}}` and inverted `{{^section}}...{{/section}}`
- Python format strings: `{variable_name}` in daily-task.md and weekly-report.md
## Code Style
- No linter or formatter configured (no `.prettierrc`, `.eslintrc`, `.editorconfig`, `biome.json`)
- Markdown files use ATX headers (`#`, `##`, `###`)
- Python scripts use standard PEP 8 style (observed from the existing scripts)
- Shebang: `#!/usr/bin/env python3`
- UTF-8 encoding (no explicit encoding declaration needed for Python 3)
- Imports grouped: stdlib first, no third-party imports in this project
- Docstrings: triple-double-quote module docstrings at top of file
- Functions: `snake_case` names
- Type hints used for function signatures in `migrate_db.py` (e.g., `conn: sqlite3.Connection`, `db_path: str`)
- Constants: `UPPER_SNAKE_CASE` at module level (e.g., `DB_PATH`, `EXPECTED_VERSION`, `MIGRATIONS`, `TIER_PATTERNS`)
- CLI argument parsing via `argparse` (see `validate_urls.py`)
## Markdown / Prompt Conventions
- Formatting only -- no logic, no SQL, no decision branches
- Mustache-style variables for dynamic content
- Emoji prefixes for visual hierarchy in Telegram messages (e.g., `📚`, `✅`, `❌`, `📊`, `🎉`)
- Separator lines: `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`
- YAML frontmatter with `name`, `description`, `version`, `author`, `argument-hint`
- `## PERSONA` -- defines the tutor's character and language rules
- `## RULES` -- numbered behavioral rules for the LLM
- `## PITFALLS` -- known issues from experience
- `## SOURCE TIER SYSTEM` -- URL reliability classification
- `## ROUTER` -- command dispatch table mapping commands to subskills
- `## DATABASE` -- DB location and initialization
- `## COMMAND IMPLEMENTATIONS` -- inline SQL and bash for simple commands
- `## CRON JOB NOTES` -- cron-specific behavior notes
## Import Organization
## Error Handling
- `try/except` for specific exceptions (e.g., `sqlite3.OperationalError`, `subprocess.TimeoutExpired`)
- Idempotent operations: `CREATE TABLE IF NOT EXISTS`, `INSERT OR IGNORE`
- Migration script handles "duplicate column name" gracefully (prints SKIP instead of failing)
- Stdin JSON parse error prints message and exits with `sys.exit(1)`
- DB not found prints message and exits with `sys.exit(1)`
- Each subskill has an `## Error Handling` section documenting failure modes
- Pattern: retry once, then report to user
- DB failures: report error, do NOT leave partial state
- LLM JSON parse failures: retry once with explicit instruction, then ask user to resubmit
- Silent exit on expected conditions (no active path, path paused, task already sent)
- No output = no Telegram message sent
- Auto-pause on extended inactivity (5+ days)
## Documentation Style
- User-facing documentation
- Includes: what it does, example session (real, not polished), architecture diagram, command table, setup instructions, evaluation rubric, inactivity handling, SQLite schema overview, design decisions table, limitations, roadmap
- Written in English (as of v1.1 rename)
- Builder/developer guide -- explicitly states "for developers extending or debugging"
- Includes: project overview, architecture decisions table, file structure, state model, cron behavior, evaluation flow, how-to guides for adding features, known limitations, testing checklist
- References README.md for user-facing usage
- Focused on the URL validation system (the most common contribution area)
- Includes: tier system rules, testing commands, common issues and fixes, PR submission steps
- Python: module-level docstrings, function docstrings, inline comments for non-obvious logic
- Markdown: minimal comments; structure is self-documenting through headers and tables
- SQL: inline in code blocks within subskills, commented with purpose
## Git Workflow
- `feature/<short-description>` -- e.g., `feature/trusted-sources-syllabus-v2`
- `fix/<short-description>` -- e.g., `fix/cron-silent-no-path`, `fix/remove-duplicate-tier-section-v2`
- Hyphens as separators, lowercase
- Follow conventional commits: `<type>: <description>`
- Types observed: `feat`, `fix`, `docs`, `chore`
- Lowercase after colon
- Examples:
- Version bumps use format: `v1.1: rename skill learning-path -> tutor`
- Some early commits do not follow the convention (e.g., `fixed authors`, `Initial commit`)
- Merged via GitHub PRs
- PR titles follow same conventional commit style
- Squash merge observed (feature branch commits merged into single merge commit)
## Language
- Documentation: English (README, AGENTS.md, CONTRIBUTING.md)
- User-facing output: Spanish by default (matching user language per persona rules)
- Code: English for all identifiers, comments, docstrings
- Mixed: some template content is in Spanish (e.g., syllabus.md template), some in English (e.g., daily-task.md, evaluation.md)
## File Size Guidelines
- `SKILL.md`: Keep under 200 lines (explicit guideline in AGENTS.md)
- Subskills: 65-257 lines (current range)
- Templates: 12-55 lines (formatting only)
- Python scripts: 102-216 lines (focused, single-purpose)
- If SKILL.md grows beyond 200 lines, extract a new subskill
## Configuration Patterns
- No config files for tooling (no `.prettierrc`, no `tsconfig.json`, no `pyproject.toml`)
- `.gitignore` ignores: `learning.db`, `*.db-wal`, `*.db-shm`, OS files (`.DS_Store`, `Thumbs.db`), editor files (`*.swp`, `.vscode/`, `.idea/`)
- Runtime configuration: SQLite `config` table (key-value store)
- Environment variables: `OBSIDIAN_VAULT_PATH` (optional, in `~/.hermes/.env`)
- DB path: hardcoded as `~/.hermes/skills/tutor/learning.db` (no env var override for DB location)
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- The entire application is a **Hermes Agent skill** — not a traditional code application. Logic lives in Markdown files (prompts), not in compiled code.
- **DB is truth.** Every operation queries SQLite before acting. No in-memory state is trusted.
- **Cron sessions are stateless.** Every cron invocation starts with zero context — all SQL, decision branches, and logic must be fully inlined in the prompt.
- **Subskill router** pattern keeps the main prompt (~180 lines) lean for local models (Ollama). Heavy logic loads on demand.
## Layers
- Purpose: Receives user commands and routes to the appropriate subskill or inline handler
- Location: `SKILL.md`
- Contains: Persona definition, rules, command dispatch table, inline SQL for simple commands (status, skip, pause, resume, switch, export)
- Depends on: `subskills/*.md` for complex flows, `scripts/init_db.py` for DB initialization
- Used by: Hermes Agent runtime (loaded when the skill is invoked)
- Purpose: Contains the step-by-step logic for each major workflow
- Location: `subskills/`
- Contains: Four subskills, each with trigger conditions, SQL queries, LLM prompts, and decision trees
- Depends on: `templates/*.md` for output formatting, `scripts/*.py` for DB operations
- Used by: Router layer (loaded on demand), cron jobs (inlined verbatim into cron prompts)
- Purpose: Defines presentation formats for user-facing messages
- Location: `templates/`
- Contains: Format templates for syllabi, daily tasks, evaluations, weekly reports, and milestones
- Depends on: Nothing (pure formatting)
- Used by: Subskills (init.md, daily.md, eval.md, adapt.md)
- Purpose: Python utilities for database initialization, schema migration, and URL validation
- Location: `scripts/`
- Contains: `init_db.py` (idempotent DB setup), `migrate_db.py` (schema versioning), `validate_urls.py` (tier-based URL checking)
- Depends on: Python 3.11+, SQLite3 stdlib, curl (for HTTP checks)
- Used by: Subskills (init.md calls init_db.py and validate_urls.py)
- Purpose: Single source of truth for all application state
- Location: `learning.db` (gitignored, created at runtime)
- Contains: 6 tables — `config`, `paths`, `modules`, `daily_tasks`, `resources`, `schema_version`
- Depends on: Nothing
- Used by: All layers — router, subskills, and scripts
## Data Flow
- All state is in SQLite at `~/.hermes/skills/tutor/learning.db` (WAL mode for concurrent access)
- The `config` table acts as a key-value store for runtime state (`active_path_id`, `pending_task_id`, `last_response_date`, etc.)
- No in-memory state is maintained between sessions — every interaction starts from the DB
- Module lifecycle: `pending` -> `in_progress` -> `completed` (with `decompose` branching for low scores)
- Path lifecycle: `draft` -> `active` -> `paused` -> `active` (or `completed`)
## Key Abstractions
- Purpose: A self-contained unit of domain logic loaded only when its trigger fires
- Examples: `subskills/init.md`, `subskills/eval.md`, `subskills/daily.md`, `subskills/adapt.md`
- Pattern: Each subskill has a trigger condition, numbered steps with inline SQL, LLM prompts, and error handling. The subskill is either loaded by the router (interactive session) or inlined verbatim into a cron prompt (stateless cron session).
- Purpose: Ensures learning resources come from trustworthy, stable sources
- Examples: `scripts/validate_urls.py` (TIER_PATTERNS dict), `SKILL.md` (tier rules table)
- Pattern: Four-tier classification (TIER 1: interactive platforms, TIER 2: official courses, TIER 3: YouTube single videos, TIER 4: reference). Minimum 50% TIER 1 per module. YouTube playlists are rejected. URLs are validated by regex pattern matching and optional HTTP HEAD checks.
- Purpose: Provides consistent, evidence-based scoring of task submissions
- Examples: `templates/evaluation.md`, `subskills/eval.md`
- Pattern: Two 1-10 scores (Conceptual Comprehension, Application Ability) averaged to produce a final score. Score drives decision: advance, repeat, or decompose. LLM outputs a strict JSON schema that is parsed and stored.
- Purpose: Schedules review of completed modules at increasing intervals
- Examples: `subskills/daily.md` (Step 5 review check), `templates/evaluation.md` (next_review_days)
- Pattern: Based on evaluation score, `next_review_date` is set (7 days for >= 8.0, 3 days for 5.0-7.9, 1 day for < 5.0). Daily cron checks for modules due for review. Implemented but not yet validated end-to-end.
## Entry Points
- Location: `SKILL.md` (router), loaded by Hermes Agent when user sends a message starting with `/tutor`
- Triggers: Any message containing `/tutor <command>` or free text that matches trigger patterns (e.g., "quiero aprender <topic>")
- Responsibilities: Command parsing, subskill loading, inline command execution (status, skip, pause, resume, switch, export), error reporting
- Location: `subskills/daily.md` (inlined verbatim into cron prompt)
- Triggers: Cron schedule `0 9 * * *` (9 AM daily)
- Responsibilities: DB health check, active path verification, duplicate prevention, inactivity handling, task generation, Telegram delivery
- Critical: Must be fully self-contained — zero prior context, all SQL and decisions inlined
- Location: `subskills/adapt.md` (inlined verbatim into cron prompt)
- Triggers: Cron schedule `0 22 * * 0` (Sundays 10 PM)
- Responsibilities: Performance metrics aggregation, adaptation rule evaluation, weekly report generation, Obsidian export
- Critical: Must be fully self-contained — zero prior context
- Location: `scripts/init_db.py`
- Triggers: Called at the start of every cron job and `/tutor init` flow
- Responsibilities: Creates all tables if they don't exist, inserts default config values, idempotent (safe to run repeatedly)
- Location: `scripts/migrate_db.py`
- Triggers: Manual invocation when schema changes are needed
- Responsibilities: Compares `schema_version` in DB with `EXPECTED_VERSION`, runs ALTER TABLE statements for version deltas
## Error Handling
- **DB-first verification:** Every operation queries SQLite before acting. If the DB query fails or returns unexpected results, the agent reports it (per SKILL.md Rule 3).
- **Idempotent initialization:** `scripts/init_db.py` uses `CREATE TABLE IF NOT EXISTS` and `INSERT OR IGNORE` — safe to run on every cron invocation.
- **JSON parse retry:** If LLM outputs invalid JSON during evaluation, retry once with explicit instruction. If it fails again, ask the user to resubmit.
- **URL validation loop:** If generated syllabus fails URL validation (>30% invalid), regenerate with more conservative sources rather than proceeding with broken URLs.
- **Silent cron exits:** When no active path exists or path is paused, the daily cron exits silently with no output — no error message, no Telegram notification.
- **Partial state prevention:** If DB write fails during path creation, report to user rather than leaving partial data. Do NOT commit partial transactions.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
