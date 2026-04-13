---
phase: 06-upgrade-path
reviewed: 2026-04-13T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - README.md
  - scripts/migrate_db.py
  - subskills/init.md
  - tests/test_migrate_db.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-04-13
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed 4 files: README.md (documentation, no issues), scripts/migrate_db.py (migration engine), subskills/init.md (initialization subskill), and tests/test_migrate_db.py (migration tests). No critical issues found. Two warnings and two info-level findings.

The migration engine in migrate_db.py is generally well-structured with idempotent operations, proper error handling, and backup support. However, two inconsistent behaviors were identified. The init.md subskill has a potential crash when accessing query results without null checking.

## Warnings

### WR-01: Inconsistent exit behavior when DB schema is newer than expected

**File:** `scripts/migrate_db.py:98-102`
**Issue:** The `migrate()` function silently returns when `current > EXPECTED_VERSION` (line 98-102), but `check_and_migrate()` calls `sys.exit(1)` in the same scenario (line 161-165). This inconsistency could cause confusion when troubleshooting version mismatches — a caller using `migrate()` directly would see a silent return, while `--check` would exit with code 1.
**Fix:** Consider making both behave consistently. If exiting with code 1 is the desired behavior for unexpected future versions, apply it to `migrate()` as well:
```python
if current > EXPECTED_VERSION:
    print(f"DB schema v{current} is newer than expected v{EXPECTED_VERSION}.")
    print("This might mean you're running an older version of the skill.")
    conn.close()
    sys.exit(1)  # Add this for consistency
```

### WR-02: Potential None dereference when querying active_path_id

**File:** `subskills/init.md:26`
**Issue:** The inline Python script accesses `row[0]` without checking if `fetchone()` returned None. If the `active_path_id` config key does not exist in the database, `fetchone()` returns None and `row[0]` raises `IndexError`.
**Fix:** Add a None check before accessing `row[0]`:
```python
row = c.fetchone()
if row and row[0]:
    c.execute('SELECT topic, status FROM paths WHERE id=?', (row[0],))
    p = c.fetchone()
    if p:
        print(f'ACTIVE_PATH: {p[0]} (status: {p[1]})')
    else:
        print('NO_ACTIVE_PATH')
else:
    print('NO_ACTIVE_PATH')
```

## Info

### IN-01: Missing PRAGMA foreign_keys=ON in inline Python

**File:** `subskills/init.md:17`
**Issue:** The inline Python script connects to SQLite without setting `PRAGMA foreign_keys=ON`. While this does not cause data corruption in the current usage (the script only reads data), it is inconsistent with the project's error handling pattern. The `init_db.py`, `migrate_db.py`, and `save_path.py` all set this pragma.
**Fix:** Add after connection:
```python
conn = sqlite3.connect(db)
conn.execute("PRAGMA foreign_keys=ON")
```

### IN-02: Test v1 schema does not match real v1 schema

**File:** `tests/test_migrate_db.py:22-79`
**Issue:** The test creates a hand-crafted v1 schema that differs from the actual v1 schema defined in `scripts/init_db.py`. Specifically:
- `modules` table in test is missing `score` and `next_review_date` columns (which exist in the real init_db.py schema)
- `daily_tasks` table in test is missing `response_window_end` column (which exists in the real init_db.py schema)

This means the test does not accurately model a real v1->v2 migration. However, this does not cause false failures because the migration handles "duplicate column name" gracefully, and the test only checks for the presence of new columns, not the absence of duplicate-column errors.
**Fix:** Align the test's `create_v1_db()` function with the actual schema in `init_db.py` to improve test fidelity:
```python
c.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        ...
        score REAL DEFAULT 0,
        next_review_date TEXT,
        ...
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS daily_tasks (
        ...
        response_window_end TEXT,
        ...
    )
""")
```

---

_Reviewed: 2026-04-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
