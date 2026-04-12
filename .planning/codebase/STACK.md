# Technology Stack

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.11 — Database initialization (`scripts/init_db.py`, `scripts/migrate_db.py`), URL validation (`scripts/validate_urls.py`), and inline DB operations within subskill prompts
- Markdown — All skill logic, subskills, templates, and documentation. The entire application logic lives in Markdown files interpreted by the Hermes Agent runtime.

**Secondary:**
- SQL (SQLite dialect) — Inline SQL queries embedded in subskill Markdown files for all CRUD operations
- Mustache-like template syntax — Used in `templates/*.md` files (`{{variable}}`, `{{#section}}`)

## Runtime

**Environment:**
- Hermes Agent (v0.7+) — AI agent framework that interprets Markdown skill files and executes tools (cron, terminal, delegate_task, etc.)
- Python 3.11 — For script execution
- Bash — For running Python scripts, curl commands, and file operations

**Package Manager:**
- None. This project has no `package.json`, `requirements.txt`, `pyproject.toml`, or equivalent. All Python code uses only the standard library (`sqlite3`, `json`, `subprocess`, `argparse`, `re`, `os`, `sys`, `pathlib`, `datetime`, `urllib.parse`).

**Lockfile:** Not applicable.

## Frameworks

**Core:**
- Hermes Agent Skill System — The entire application is a "skill" within the Hermes Agent framework. The skill is defined by `SKILL.md` (router/persona) with subskills loaded on demand.

**Database:**
- SQLite 3.50.4 (via Python `sqlite3` standard library module) — WAL mode enabled in migrations, foreign keys enforced

**Testing:**
- pytest — Referenced in `CONTRIBUTING.md` (`python3 -m pytest scripts/test_validate_urls.py -v`), but no test files currently exist in the repository

**Build/Dev:**
- None. This is a zero-dependency skill. No build step, no compilation, no bundling.

## Key Dependencies

**Critical (Python standard library only):**
- `sqlite3` — Database operations (built-in)
- `json` — JSON parsing for LLM evaluation output and syllabus data (built-in)
- `subprocess` — Running curl for URL validation (built-in)
- `argparse` — CLI argument parsing for validate_urls.py (built-in)
- `re` — URL pattern matching for tier classification (built-in)
- `urllib.parse` — URL parsing (built-in)
- `pathlib` / `os` — File path handling (built-in)
- `datetime` — Timestamp generation (built-in)

**Infrastructure:**
- `curl` (system package, 8.5.0) — Used by `scripts/validate_urls.py` for HTTP HEAD requests to verify resource URLs
- `hermes` (system-level) — The Hermes Agent runtime that loads and executes skill files

**External services consumed at runtime (not installed packages):**
- Telegram API — Message delivery via Hermes `telegram` deliver channel
- Web search — Resource discovery via Hermes `delegate_task` with `web_search` tool
- LLM — Syllabus generation, task generation, and evaluation via Hermes agent's configured model

## Configuration

**Environment:**
- No `.env` file required by the skill itself. The Hermes framework may have its own configuration at `~/.hermes/config.yaml` and `~/.hermes/.env`.
- Database path is hardcoded: `~/.hermes/skills/tutor/learning.db`
- Obsidian vault path is configurable via `OBSIDIAN_VAULT_PATH` environment variable, falling back to `$HOME/Documents/Obsidian Vault`

**Build:**
- No build configuration. Files are plain Markdown and Python scripts.

**Hermes Configuration:**
- Cron jobs are registered via Hermes `cronjob(action="create")` tool with schedule expressions (`0 9 * * *` for daily, `0 22 * * 0` for weekly)
- Skill auto-registers as `/tutor` based on directory name
- Delivery channel: `telegram`

## Platform Requirements

**Development:**
- Python 3.11+ (only standard library needed)
- curl (for URL validation)
- Hermes Agent v0.7+ runtime for execution
- A running Hermes gateway with Telegram channel configured

**Production:**
- Hermes Agent runtime (same machine, no deployment)
- SQLite database at `~/.hermes/skills/tutor/learning.db`
- Cron job scheduler within Hermes (2 cron jobs: daily task delivery, weekly review)
- Telegram bot integration via Hermes

---

*Stack analysis: 2026-04-12*
