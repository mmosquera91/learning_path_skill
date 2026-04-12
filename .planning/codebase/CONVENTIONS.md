# Coding Conventions

**Analysis Date:** 2026-04-12

## Project Type

This is a **Hermes Agent skill** -- the codebase consists of Markdown prompt files (skill logic), Python utility scripts, and Markdown templates. There are no compiled languages, no build systems, and no traditional application code. The "code" is primarily LLM prompts that define behavior.

## Naming Patterns

**Files:**
- Skill router: `SKILL.md` (uppercase, root level)
- Subskills: `kebab-case.md` in `subskills/` -- e.g., `init.md`, `daily.md`, `eval.md`, `adapt.md`
- Templates: `kebab-case.md` in `templates/` -- e.g., `daily-task.md`, `weekly-report.md`, `evaluation.md`
- Python scripts: `snake_case.py` in `scripts/` -- e.g., `init_db.py`, `migrate_db.py`, `validate_urls.py`
- Documentation: `UPPERCASE.md` for project docs (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `LICENSE`)

**Directories:**
- `subskills/` -- command-specific prompt files loaded on demand by the router
- `templates/` -- formatting-only Markdown templates for Telegram output
- `scripts/` -- Python utility scripts for database and URL validation

**Database Tables:**
- `snake_case` -- e.g., `daily_tasks`, `schema_version`, `active_path_id`
- Config keys: `snake_case` -- e.g., `active_path_id`, `pending_task_id`, `last_response_date`

**Variables in Templates:**
- Mustache-style: `{{variable_name}}` with sections `{{#section}}...{{/section}}` and inverted `{{^section}}...{{/section}}`
- Python format strings: `{variable_name}` in daily-task.md and weekly-report.md

## Code Style

**Formatting:**
- No linter or formatter configured (no `.prettierrc`, `.eslintrc`, `.editorconfig`, `biome.json`)
- Markdown files use ATX headers (`#`, `##`, `###`)
- Python scripts use standard PEP 8 style (observed from the existing scripts)

**Python Style:**
- Shebang: `#!/usr/bin/env python3`
- UTF-8 encoding (no explicit encoding declaration needed for Python 3)
- Imports grouped: stdlib first, no third-party imports in this project
- Docstrings: triple-double-quote module docstrings at top of file
- Functions: `snake_case` names
- Type hints used for function signatures in `migrate_db.py` (e.g., `conn: sqlite3.Connection`, `db_path: str`)
- Constants: `UPPER_SNAKE_CASE` at module level (e.g., `DB_PATH`, `EXPECTED_VERSION`, `MIGRATIONS`, `TIER_PATTERNS`)
- CLI argument parsing via `argparse` (see `validate_urls.py`)

## Markdown / Prompt Conventions

**Subskill Structure** (files in `subskills/`):
1. Title line: `# Subskill: {Name} -- {One-line description}`
2. `## Trigger` section -- what command or event invokes this subskill
3. `## Steps` section -- numbered steps (`### 1.`, `### 2.`, etc.)
4. Each step contains inline code blocks (SQL, bash, Python) that the LLM executes
5. Optional `## Error Handling` section at the end

**Template Structure** (files in `templates/`):
- Formatting only -- no logic, no SQL, no decision branches
- Mustache-style variables for dynamic content
- Emoji prefixes for visual hierarchy in Telegram messages (e.g., `📚`, `✅`, `❌`, `📊`, `🎉`)
- Separator lines: `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`

**SKILL.md Structure:**
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

**Python:**
1. Standard library imports (`sqlite3`, `os`, `sys`, `re`, `json`, `subprocess`, `argparse`)
2. Standard library `from X import Y` (`pathlib.Path`, `urllib.parse.urlparse`, `datetime`)
3. No third-party imports -- all scripts use only stdlib

## Error Handling

**Python Scripts:**
- `try/except` for specific exceptions (e.g., `sqlite3.OperationalError`, `subprocess.TimeoutExpired`)
- Idempotent operations: `CREATE TABLE IF NOT EXISTS`, `INSERT OR IGNORE`
- Migration script handles "duplicate column name" gracefully (prints SKIP instead of failing)
- Stdin JSON parse error prints message and exits with `sys.exit(1)`
- DB not found prints message and exits with `sys.exit(1)`

**Prompt/Subskill Error Handling:**
- Each subskill has an `## Error Handling` section documenting failure modes
- Pattern: retry once, then report to user
- DB failures: report error, do NOT leave partial state
- LLM JSON parse failures: retry once with explicit instruction, then ask user to resubmit

**Cron Job Error Handling:**
- Silent exit on expected conditions (no active path, path paused, task already sent)
- No output = no Telegram message sent
- Auto-pause on extended inactivity (5+ days)

## Documentation Style

**README.md:**
- User-facing documentation
- Includes: what it does, example session (real, not polished), architecture diagram, command table, setup instructions, evaluation rubric, inactivity handling, SQLite schema overview, design decisions table, limitations, roadmap
- Written in English (as of v1.1 rename)

**AGENTS.md:**
- Builder/developer guide -- explicitly states "for developers extending or debugging"
- Includes: project overview, architecture decisions table, file structure, state model, cron behavior, evaluation flow, how-to guides for adding features, known limitations, testing checklist
- References README.md for user-facing usage

**CONTRIBUTING.md:**
- Focused on the URL validation system (the most common contribution area)
- Includes: tier system rules, testing commands, common issues and fixes, PR submission steps

**Code Comments:**
- Python: module-level docstrings, function docstrings, inline comments for non-obvious logic
- Markdown: minimal comments; structure is self-documenting through headers and tables
- SQL: inline in code blocks within subskills, commented with purpose

## Git Workflow

**Branch Naming:**
- `feature/<short-description>` -- e.g., `feature/trusted-sources-syllabus-v2`
- `fix/<short-description>` -- e.g., `fix/cron-silent-no-path`, `fix/remove-duplicate-tier-section-v2`
- Hyphens as separators, lowercase

**Commit Messages:**
- Follow conventional commits: `<type>: <description>`
- Types observed: `feat`, `fix`, `docs`, `chore`
- Lowercase after colon
- Examples:
  - `feat: initial release -- Learning Path Generator v1.0.0`
  - `fix: prevent cron duplication + score dispute guard`
  - `docs: honest README -- fix cron setup, add example session, mark untested features`
  - `feat: Add URL validation system with tier-based source ranking`
  - `chore: remove learning.db from repo (user data, never belongs in version control)`
- Version bumps use format: `v1.1: rename skill learning-path -> tutor`
- Some early commits do not follow the convention (e.g., `fixed authors`, `Initial commit`)

**Pull Requests:**
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

---

*Convention analysis: 2026-04-12*
