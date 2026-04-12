---
phase: 01-foundation
reviewed: 2026-04-12T21:15:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - .gitignore
  - AGENTS.md
  - SKILL.md
  - scripts/init_db.py
  - scripts/migrate_db.py
  - scripts/test_init_db_security.py
  - scripts/validate_urls.py
  - subskills/adapt.md
  - tests/__init__.py
  - tests/conftest.py
  - tests/test_eval_pipeline.py
  - tests/test_init_db.py
  - tests/test_migrate_db.py
  - tests/test_validate_urls.py
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-12T21:15:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed all 14 changed files: 3 Python scripts (`init_db.py`, `migrate_db.py`, `validate_urls.py`), 1 security test file, 1 subskill markdown (`adapt.md`), 5 test files, 1 test conftest, 1 gitignore, and 2 documentation files (`AGENTS.md`, `SKILL.md`).

Two critical schema drift issues found between `init_db.py` and the test expectations / migration state. The production `init_db.py` is stuck at v1 schema while tests and migrations assume v2. This means fresh installs will have a different schema than migrated installs. Additional warnings around SQL injection risk in markdown subskills, CHECK constraint inconsistency between tests and production, and missing error handling in migration down-path.

## Critical Issues

### CR-01: init_db.py is out of sync with v2 migration -- fresh installs get incomplete schema

**File:** `scripts/init_db.py` (entire file, compared against `scripts/migrate_db.py:24-35`)
**Issue:** The `init_db.py` script does not include the v2 migration columns and config keys. Specifically, it is missing:

**modules table:** `score REAL DEFAULT 0` and `next_review_date TEXT`
**daily_tasks table:** `response_window_end TEXT`
**config defaults:** `last_task_date`, `daily_count`, `weekly_count`, `response_window_end`

This means a fresh install (running `init_db.py`) produces a v1 schema, while an existing install that has been migrated via `migrate_db.py` is at v2. The AGENTS.md section "How to Add Features" explicitly states: "Edit `init_db.py`: Add the new column to the `CREATE TABLE` statement for fresh installs" -- but this was not done when v2 was created.

The test file `tests/test_init_db.py` lines 15-28 already expect all v2 columns and config keys (8 keys including `last_task_date`, `daily_count`, `weekly_count`, `response_window_end`). Running that test against the current `init_db.py` would fail.

**Fix:**
```python
# In init_db.py, modules CREATE TABLE -- add score and next_review_date:
c.execute('''
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        module_order INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        score_avg REAL DEFAULT 0,
        score REAL DEFAULT 0,
        next_review_date TEXT,
        times_repeated INTEGER DEFAULT 0,
        started TEXT,
        completed TEXT,
        FOREIGN KEY (path_id) REFERENCES paths(id) ON DELETE CASCADE
    )
''')

# In init_db.py, daily_tasks CREATE TABLE -- add response_window_end:
c.execute('''
    CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        content TEXT NOT NULL,
        response TEXT CHECK(length(response) <= 10000 OR response IS NULL),
        score INTEGER,
        response_window_end TEXT,
        feedback TEXT,
        skipped INTEGER DEFAULT 0,
        awaiting_response INTEGER DEFAULT 1,
        FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    )
''')

# In init_db.py, defaults list -- add v2 config keys:
defaults = [
    ('active_path_id', ''),
    ('pending_task_id', ''),
    ('last_response_date', ''),
    ('streak_count', '0'),
    ('last_task_date', ''),
    ('daily_count', '0'),
    ('weekly_count', '0'),
    ('response_window_end', ''),
]
```

### CR-02: init_db.py does not create or set schema_version table

**File:** `scripts/init_db.py` (entire file)
**Issue:** The `init_db.py` script never creates the `schema_version` table nor inserts a version record. Meanwhile, `migrate_db.py` line 57 reads from `schema_version` to determine current version. If a user runs `init_db.py` (fresh install) and then runs `migrate_db.py`, the migration script calls `get_current_version()` which catches the `OperationalError` and returns 0, then proceeds to run all migrations from v0 to v2. This accidentally works, but:

1. It runs migrations unnecessarily on a fresh install (wasteful, creates a backup of a brand-new DB).
2. It means `init_db.py`'s schema is always treated as "pre-version" by the migration engine, which is fragile and semantically wrong.
3. AGENTS.md section 4 documents `schema_version` as a table in the schema but `init_db.py` does not create it.

**Fix:**
```python
# After all CREATE TABLE statements in init_db(), add:
c.execute('''
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER
    )
''')
c.execute('''
    INSERT OR IGNORE INTO schema_version (version) VALUES (2)
''')
```

This ensures fresh installs start at v2 and `migrate_db.py` correctly detects "already at expected version."

## Warnings

### WR-01: SQL injection risk in SKILL.md and adapt.md -- user input not properly parameterized

**File:** `SKILL.md:161-172`, `subskills/adapt.md:10-21`
**Issue:** Both files document LIKE queries with user input and describe manual escaping (replace `\`, `%`, `_`). While the intent is correct, this is a markdown prompt for an LLM agent -- there is no guarantee the LLM will correctly implement the escaping steps. A more robust approach would be to instruct the LLM to use parameterized queries with `?` placeholders and the `ESCAPE` clause, which is already partially shown (line 171 uses `? ESCAPE '\'`) but the preceding manual escaping instructions at lines 162-166 contradict the parameterized approach.

If the LLM follows the instructions literally and does manual string formatting into SQL (as suggested by "Wrap in `%...%` for substring matching"), it could produce a SQL injection vector. The agent should be told to **always** use parameter binding, never string interpolation.

**Fix:** In both SKILL.md and adapt.md, replace the manual escaping instructions with a clear directive:
```
Note: Always use parameterized queries. Bind user input as a parameter to prevent injection.
Never interpolate user input directly into SQL strings.
```

### WR-02: CHECK constraint on response column missing from test schemas

**File:** `scripts/test_init_db_security.py:78`, `tests/test_init_db.py:88-101`, `tests/test_eval_pipeline.py:38-45`
**Issue:** The production `init_db.py` (line 78) has a CHECK constraint on `daily_tasks.response`: `CHECK(length(response) <= 10000 OR response IS NULL)`. However, the test helper functions that replicate the schema omit this constraint:

- `test_init_db.py` `_run_init_sql()` line 93: `response TEXT,` (no CHECK)
- `test_eval_pipeline.py` `_create_full_schema()` line 41: `response TEXT,` (no CHECK)
- `test_init_db_security.py` `_init_test_db()` line 78: correctly includes CHECK

The security test properly tests the constraint, but the main init_db test and eval pipeline test do not replicate it. This means those tests operate against a slightly different schema than production, which could mask bugs (e.g., inserting a 50000-char response would pass in tests but fail in production).

**Fix:** Add the CHECK constraint to all test schema replications:
```python
# In tests/test_init_db.py _run_init_sql() and tests/test_eval_pipeline.py _create_full_schema():
response TEXT CHECK(length(response) <= 10000 OR response IS NULL),
```

### WR-03: migrate_db.py down-migration does not handle FK IntegrityError for non-FK cases

**File:** `scripts/migrate_db.py:183-191`
**Issue:** The `migrate_down()` function catches `sqlite3.IntegrityError` and only checks for "foreign key" in the message. If any other IntegrityError occurs (e.g., NOT NULL constraint violation during table recreation), it falls through to the else branch which calls `sys.exit(1)`. This is correct behavior but the error message is printed twice (line 180 and 182 print different things), and the `conn.close()` before `sys.exit(1)` does not rollback the partial migration, leaving the DB in an inconsistent state.

**Fix:** Add `conn.rollback()` before `conn.close()` in the error handler, and consolidate the error messages:
```python
except sqlite3.IntegrityError as e:
    if "foreign key" in str(e).lower():
        print(f"    FK note: {e}")
    else:
        print(f"    ERROR: {e}")
        print(f"    SQL: {sql}")
        conn.rollback()
        conn.close()
        sys.exit(1)
```

### WR-04: validate_urls.py -- generic tier 1 patterns can misclassify tier 2 URLs

**File:** `scripts/validate_urls.py:19-22, 66-76`
**Issue:** The two-pass classification (specific domain patterns first, then generic path patterns) is designed to prevent shadowing, but generic patterns like `r'/lessons?/[\w-]+$'` (tier 1) and `r'/docs(?:/[\w-]+)+'` (tier 2) have overlapping potential. A URL like `https://somedomain.com/docs/lessons/python` would match tier 2's `/docs` pattern in the first pass (domain-anchored), which is correct. But `https://somedomain.com/lessons/python/docs` would match tier 1's `/lessons` pattern in the second pass (path-based), classifying a docs page as an interactive lesson.

The two-pass system mitigates most cases but does not eliminate all ambiguity. This is a known design tradeoff documented in the code comments.

**Fix:** Consider adding a negative lookahead or ordering paths by specificity (longer patterns first). Alternatively, document this as a known limitation in AGENTS.md section 8 alongside the existing model-specific caveats.

## Info

### IN-01: test_init_db_security.py is in scripts/ instead of tests/

**File:** `scripts/test_init_db_security.py`
**Issue:** This test file lives in `scripts/` alongside the production code, while all other test files are in `tests/`. This is inconsistent with the project structure and means the test may not be discovered by a test runner pointing at `tests/`.

**Fix:** Move `scripts/test_init_db_security.py` to `tests/test_init_db_security.py`. The file already uses `os.path.dirname(__file__)` for path resolution so it would need the same `sys.path` adjustment used by `conftest.py`.

### IN-02: conftest.py uses mutable sys.path.insert but no cleanup

**File:** `tests/conftest.py:6`
**Issue:** `sys.path.insert(0, ...)` modifies the global Python path for the test process. While this is standard practice for test fixtures, it means the `scripts` directory is permanently on `sys.path` for the entire test session, which could cause import conflicts if other modules share names with standard library or third-party packages.

**Fix:** This is a minor issue and acceptable for a single-user project. No action needed unless import conflicts arise.

### IN-03: .gitignore does not exclude test databases or backup files

**File:** `.gitignore`
**Issue:** The `.gitignore` covers `learning.db` and `*.db-wal`/`*.db-shm`, but does not exclude `*.bak.*` (migration backups) or `*.db` in subdirectories (e.g., if someone runs tests from the project root, `test.db` files could appear). Migration backups are created at `learning.db.bak.v{N}` which is already covered by the existing patterns, but `tests/*.db` files from local testing are not excluded.

**Fix:** Add `*.bak.*` and `test*.db` to `.gitignore` if local test artifacts become a concern.

---

_Reviewed: 2026-04-12T21:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
