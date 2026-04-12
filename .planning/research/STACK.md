# Stack Research: Hermes Tutor Skill Hardening

**Domain:** Markdown-driven AI skill with SQLite backend (brownfield hardening)
**Researched:** 2026-04-12
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | All script logic, DB operations, URL validation | Already the project language. 3.11+ required for `sqlite3` WAL reliability and `ExceptionGroup`. Stdlib-only constraint from PROJECT.md means no external runtime deps. |
| SQLite | 3.45+ (system lib 3.50.4) | Persistent state backend | Already in use. The `sqlite3` stdlib module on this system links to 3.50.4. WAL mode + foreign keys already configured in `migrate_db.py`. No reason to change. |
| Markdown | --- | Skill logic, subskills, templates | Hermes Agent runtime constraint -- all application logic must remain in Markdown files interpreted by the agent. This is not a choice, it is a constraint. |
| pytest | 8.3+ | Test framework for scripts and DB operations | The standard for Python testing in 2025-2026. Zero test coverage is the single biggest blocker to safe refactoring. pytest fixtures provide clean DB isolation via `:memory:` SQLite. CONTRIBUTING.md already references `python3 -m pytest`. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `git-filter-repo` | 2.47+ | Purge `learning.db` from git history | One-time operation to remove the 3 commits containing user data blobs (commits `ffa02d78`, `f2ff73d7`, `dd3918fb`). Install via `pipx` or a dedicated venv -- NOT as a project dependency since it is a single-use tool. |
| `pytest-tmp-files` | --- | Test directory fixtures | Optional. If tests need temp file creation (e.g., testing `init_db.py` file creation), pytest's built-in `tmp_path` fixture is sufficient. No extra library needed. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `python3 -m venv` | Isolated test dependency environment | Required because this system uses `externally-managed-environment` (PEP 668). pytest must be installed in a venv, not system-wide. Runtime scripts (`init_db.py`, `validate_urls.py`) must remain stdlib-only and work outside the venv. |
| `git-filter-repo` | One-time git history rewrite | Install: `pip install git-filter-repo` inside a venv, then run against a fresh clone. This replaces the deprecated `git filter-branch`. See Pitfalls section for required procedure. |
| `shellcheck` | Validate inline Bash/SQL in Markdown | The subskill Markdown files contain embedded Python and SQL that the LLM executes. Shellcheck does not apply here, but manual SQL review against the schema does. No automated tool can validate LLM-interpreted SQL. |
| `wc -l` / line-count CI check | Enforce SKILL.md < 200 lines | Simple `wc -l SKILL.md` in a test or CI step. Prevents the router from growing past its context budget again. |

## Installation

```bash
# Create test venv (runtime scripts stay stdlib-only)
cd ~/.hermes/skills/tutor
python3 -m venv .venv
source .venv/bin/activate

# Test dependencies only
pip install pytest

# One-time: git history cleanup tool
pip install git-filter-repo
```

Runtime scripts (`init_db.py`, `migrate_db.py`, `validate_urls.py`) require NO installation. They use only Python stdlib.

## Stack Decisions by Concern

### Testing the Python Scripts

**What to test:**
- `validate_urls.py` -- `classify_url()` has 12+ regex patterns with YouTube special-casing. Zero tests. One regex change breaks URL classification silently.
- `init_db.py` -- Schema creation, idempotency, default config values.
- `migrate_db.py` -- Version detection, forward migration, duplicate column handling.

**Approach:** pytest with `:memory:` SQLite fixture. Each test gets a fresh in-memory database. No file I/O, no cleanup needed.

```python
# tests/conftest.py
import sqlite3
import pytest

@pytest.fixture
def db_conn():
    """Fresh in-memory SQLite connection per test."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    yield conn
    conn.close()
```

```python
# tests/test_validate_urls.py
from scripts.validate_urls import classify_url

def test_youtube_single_video():
    tier, kind = classify_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert tier == 3
    assert kind == "YouTube single video"

def test_youtube_playlist_rejected():
    tier, kind = classify_url("https://www.youtube.com/playlist?list=PLabc123")
    assert tier is None
    assert "PLAYLIST" in kind

def test_coursera_tier2():
    tier, kind = classify_url("https://www.coursera.org/learn/machine-learning")
    assert tier == 2
```

**Confidence:** HIGH -- this is the standard pytest pattern for SQLite testing, well-documented since 2023.

### Parameterized SQL for LLM Context

**The problem:** Two SQL queries in Markdown files use f-string interpolation with LIKE clauses:
- `SKILL.md:163` -- `WHERE topic LIKE '%{topic}%'`
- `subskills/adapt.md:13` -- `AND title LIKE '%{module}%'`

These are NOT executed directly by Python -- they are interpreted by the LLM from Markdown. This makes traditional parameterized queries impossible. The LLM must construct and execute the SQL.

**Solution -- two layers:**

1. **In the Markdown prompts:** Write the SQL with explicit escape instructions for the LLM:
   ```sql
   -- Escape user input before interpolation:
   -- Replace \ with \\, % with \%, _ with \_
   -- Then use: WHERE topic LIKE '%{escaped_topic}%' ESCAPE '\'
   ```
   This gives the LLM a concrete procedure to follow.

2. **In Python scripts (init_db.py, etc.):** Use proper `?` parameterized queries:
   ```python
   def escape_like(value: str) -> str:
       """Escape LIKE wildcards for SQLite."""
       return (
           value
           .replace("\\", "\\\\")
           .replace("%", "\\%")
           .replace("_", "\\_")
       )

   conn.execute(
       "SELECT * FROM paths WHERE topic LIKE ? ESCAPE '\\'",
       (f"%{escape_like(user_input)}%",)
   )
   ```

**Why not remove LIKE entirely:** LIKE with wildcards is useful for search. The fix is escaping, not removal.

**Confidence:** HIGH -- `ESCAPE` clause is standard SQLite since 3.39.0. The LLM-layer solution is MEDIUM confidence because it depends on LLM compliance.

### Git History Cleanup

**The problem:** `learning.db` was committed in 3 commits (`ffa02d78`, `f2ff73d7`, `dd3918fb`). The `.gitignore` was added later. The blob remains recoverable.

**Tool:** `git-filter-repo` (replaces deprecated `git filter-branch`).

**Procedure:**
```bash
# 1. Clone fresh (filter-repo requires a fresh clone or --force)
cd /tmp
git clone ~/.hermes/skills/tutor tutor-clean
cd tutor-clean

# 2. Install filter-repo in a venv
python3 -m venv .venv
source .venv/bin/activate
pip install git-filter-repo

# 3. Remove the file from ALL history
git filter-repo --path learning.db --invert-paths --force

# 4. Verify no traces remain
git rev-list --objects --all | grep learning.db
# Should return nothing

# 5. Copy cleaned history back
# WARNING: This rewrites ALL commit hashes
# Single-user repo, no collaborators -- safe to proceed
```

**Confidence:** HIGH -- `git-filter-repo` is the standard tool since 2020, maintained by Elijah Newren. The procedure is well-documented. LOW confidence on exact version (2.47+ is training data estimate; verify `pip install git-filter-repo` output).

**Important caveat:** This repo is single-user on a single machine with one branch (`gsd-experiment` with `master` as main). No collaborators. Force-push is not needed (no remote to push to). If a remote exists, `git push --force --all` is required.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `pytest` | `unittest` (stdlib) | Never. pytest fixtures are the sole reason to use it. `unittest` cannot express DB-per-test isolation cleanly. `unittest.mock` is available within pytest anyway. |
| `pytest` | `hypothesis` (property-based testing) | For `classify_url()` fuzzing -- useful but not MVP. Add later if regex coverage proves insufficient. pytest + hypothesis coexist fine. |
| `git-filter-repo` | `git filter-branch` | Never. `git filter-branch` is deprecated, slow, and leaves reflog debris. Removed from Git docs. |
| `git-filter-repo` | `BFG Repo Cleaner` | BFG is Java-based and not installed. `git-filter-repo` is Python (already available) and more capable for path-based filtering. |
| In-memory SQLite for tests | File-based `test.db` | For debugging a single failing test, temporarily switch to `sqlite:///test_debug.db` to inspect state. Default should always be `:memory:` for speed and isolation. |
| `ESCAPE '\\'` in SQL | Remove LIKE, use `=` exact match | LIKE is needed for search functionality. Removing it reduces capability. Escape is the correct fix. |
| `ESCAPE '\\'` in SQL | SQLite FTS5 full-text search | Overkill for searching topic titles across ~15 modules. FTS5 adds schema complexity. Consider for v2 if search becomes a primary feature. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SQLAlchemy / ORM | Adds a heavy dependency to a stdlib-only project. The schema is 5 simple tables with no relations complex enough to justify an ORM. Raw `sqlite3` is clearer and keeps the zero-dependency constraint intact. | Python `sqlite3` stdlib module |
| Any external runtime dependency | PROJECT.md constraint: "Python 3.11+ stdlib only (no external dependencies)". Runtime scripts must work without pip install. | Stdlib only for runtime; pytest in venv for tests only |
| `git filter-branch` | Deprecated since Git 2.38 (2022). Slow. Leaves objects in reflog. No longer in official Git docs. | `git filter-repo` |
| `promptfoo` / `deepeval` / LLM eval frameworks | These are designed for testing LLM *outputs* against quality metrics. This project needs to test *state transitions* and *SQL correctness*, not prompt quality. The LLM is the runtime, not the system under test. | pytest with in-memory SQLite -- test the DB operations and state machine logic, not the LLM |
| `pyproject.toml` with build system | This is not a packaged Python library. It is a Hermes skill with a few utility scripts. A build system adds complexity with zero benefit. | Plain scripts in `scripts/` with a `tests/` directory and a `.venv/` for test deps |
| `tox` / `nox` | Multi-environment testing for a single-Python-version project running on one machine. Over-engineering. | Single venv with `pytest` |

## Stack Patterns by Variant

**If testing DB state transitions (init -> eval -> daily cycle):**
- Use pytest `tmp_path` fixture to create a temporary file-based SQLite DB
- Run the actual `init_db.py` and `migrate_db.py` scripts against it
- Execute SQL queries to verify state after each operation
- Because: In-memory DB cannot test file-permission checks or DB-not-found edge cases. File-based temp DB tests the full `init_db.py` path including `mkdir` and `Path` logic.

**If testing URL classification in isolation:**
- Import `classify_url` directly, no DB needed
- Use `@pytest.mark.parametrize` with a table of (URL, expected_tier, expected_type) tuples
- Because: Pure function with no side effects. Table-driven tests give maximum coverage with minimum boilerplate.

**If testing the migration system:**
- Create DB at version 0, run `migrate_db.py` with `--db` flag pointing to temp file
- Verify `schema_version` table has correct version
- Because: Migrations are the riskiest DB operation. A bad migration corrupts user data. Test forward migration AND idempotency (running twice should be safe).

## Version Compatibility

| Component | Version | Compatible With | Notes |
|-----------|---------|-----------------|-------|
| Python | 3.11.15 (system) | SQLite 3.50.4, pytest 8.3+ | 3.11 is minimum per PROJECT.md |
| SQLite (via Python) | 3.50.4 | Python 3.11+ stdlib | WAL mode, foreign keys, `ESCAPE` clause all supported |
| pytest | 8.3+ | Python 3.11+, sqlite3 stdlib | Install in venv only |
| git-filter-repo | 2.47+ | Python 3.8+, Git 2.43+ | Install in venv, run once, can remove |
| git | 2.43.0 (system) | git-filter-repo 2.47+ | No issues expected |

## Security Hardening Tools

These are not libraries to install but patterns to implement:

| Pattern | Implementation | Where |
|---------|---------------|-------|
| Parameterized SQL with LIKE escape | `escape_like()` function in scripts | All Python scripts that query the DB |
| LLM SQL safety instructions | Escape instructions in Markdown prompts | `SKILL.md`, `subskills/adapt.md` |
| DB file permissions | `os.chmod(db_path, 0o600)` after creation | `init_db.py` |
| Input length validation | `CHECK(length(response) <= 10000)` in schema | `migrate_db.py` migration v2 |
| Git history purge | `git filter-repo --path learning.db --invert-paths` | One-time operation |

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| pytest + SQLite testing | HIGH | Standard pattern, well-documented, no ambiguity |
| Parameterized LIKE escaping | HIGH | SQLite `ESCAPE` clause is standard; pattern is well-established |
| git-filter-repo for history purge | HIGH | Standard tool, maintained by Git core contributor |
| LLM-prompt SQL safety | MEDIUM | The escape instructions depend on LLM following them; no enforcement mechanism exists. Reduces risk but cannot eliminate it. |
| git-filter-repo version | LOW | Training data estimate (2.47+). Verify with `pip install git-filter-repo` output. Not critical -- any recent version works. |

## Sources

- Python `sqlite3` module documentation -- parameterized queries and `ESCAPE` clause (HIGH confidence)
- `git-filter-repo` GitHub: https://github.com/newren/git-filter-repo (HIGH confidence)
- pytest documentation: fixture patterns for database testing (HIGH confidence)
- PROJECT.md -- constraints on stdlib-only, single-user, Hermes runtime (HIGH confidence -- internal project doc)
- CONCERNS.md -- SQL injection vectors, git history leak, zero test coverage (HIGH confidence -- internal project doc)
- WebSearch -- pytest SQLite best practices (MEDIUM confidence -- search results unavailable, based on training data)
- WebSearch -- git-filter-repo version (LOW confidence -- search rate-limited, version is training data estimate)

---
*Stack research for: Hermes Tutor Skill Hardening*
*Researched: 2026-04-12*
