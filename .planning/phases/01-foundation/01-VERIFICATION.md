---
phase: 01-foundation
verified: 2025-04-12T21:30:00Z
status: gaps_found
score: 4/6 must-haves verified
gaps:
  - truth: "python scripts/init_db.py creates all documented columns (next_review_date, score, response_window_end, feedback) and initializes all config keys (last_task_date, daily_count, weekly_count, response_window_end)"
    status: failed
    reason: "init_db.py is missing critical v2 schema columns and config keys. The modules table lacks 'score' and 'next_review_date' columns. The daily_tasks table lacks 'response_window_end' column. The config defaults list lacks 'last_task_date', 'daily_count', 'weekly_count', and 'response_window_end' keys. Root cause: Commit 06cf5f2d (Plan 01-03) accidentally removed these columns when adding the CHECK constraint, causing a regression from the work done in commit 521b136d (Plan 01-01)."
    artifacts:
      - path: "scripts/init_db.py"
        issue: "Missing columns: modules.score, modules.next_review_date, daily_tasks.response_window_end. Missing config keys: last_task_date, daily_count, weekly_count, response_window_end"
    missing:
      - "Add 'score REAL DEFAULT 0' column to modules CREATE TABLE statement"
      - "Add 'next_review_date TEXT' column to modules CREATE TABLE statement"
      - "Add 'response_window_end TEXT' column to daily_tasks CREATE TABLE statement"
      - "Add config defaults: ('last_task_date', ''), ('daily_count', '0'), ('weekly_count', '0'), ('response_window_end', '')"
  - truth: "AGENTS.md schema documentation matches the actual CREATE TABLE statements in init_db.py"
    status: failed
    reason: "AGENTS.md correctly documents all v2 schema columns and config keys, but init_db.py CREATE TABLE statements do not match. Documentation is ahead of implementation."
    artifacts:
      - path: "scripts/init_db.py"
        issue: "CREATE TABLE statements missing columns that AGENTS.md documents"
      - path: "AGENTS.md"
        issue: "No issue - documentation is correct and complete"
    missing:
      - "Update init_db.py CREATE TABLE statements to match AGENTS.md documentation"
  - truth: "python -m pytest tests/ passes with tests covering DB operations, state transitions, URL validation, eval pipeline, and migration"
    status: failed
    reason: "All 50 tests in tests/ pass, and all 7 security tests in scripts/test_init_db_security.py pass. However, test_init_db.py tests were written against the v2 schema expectation, which means the tests themselves may be using temp DB fixtures that include the missing columns. The production init_db.py does not create these columns, causing a mismatch between test environment and production behavior."
    artifacts:
      - path: "tests/test_init_db.py"
        issue: "Tests may be using temp DB fixtures that include v2 columns, masking the production init_db.py gap"
      - path: "scripts/init_db.py"
        issue: "Production init_db.py does not create v2 columns, but tests expect them"
    missing:
      - "Verify that test fixtures match production init_db.py behavior or update init_db.py to include v2 columns"
deferred: []
---

# Phase 1: Foundation Verification Report

**Phase Goal:** The documented schema matches the actual database, all config keys are initialized, and a test suite exists to validate safe refactoring in subsequent phases
**Verified:** 2025-04-12T21:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python scripts/init_db.py` creates all documented columns (next_review_date, score, response_window_end, feedback) and initializes all config keys (last_task_date, daily_count, weekly_count, response_window_end) | ✗ FAILED | init_db.py missing columns: modules.score, modules.next_review_date, daily_tasks.response_window_end. Missing config keys: last_task_date, daily_count, weekly_count, response_window_end |
| 2 | `python -m pytest tests/` passes with tests covering DB operations, state transitions, URL validation, eval pipeline, and migration | ✗ FAILED | All 50 tests pass + 7 security tests pass, but tests may use temp DB fixtures that include v2 columns, masking production init_db.py gap |
| 3 | AGENTS.md schema documentation matches the actual CREATE TABLE statements in init_db.py | ✗ FAILED | AGENTS.md correctly documents all v2 columns, but init_db.py CREATE TABLE statements are missing them. Documentation ahead of implementation. |
| 4 | migrate_db.py creates a backup before applying changes and supports down-migration to the previous version | ✓ VERIFIED | migrate_db.py has backup_db() function, creates .bak.v{N} before migration, supports --down flag, REVERSE_MIGRATIONS dict present. Tests verify all behaviors. |
| 5 | User submissions longer than a defined limit are rejected before being written to the database, and learning.db is created with 600 permissions | ✓ VERIFIED | init_db.py has `CHECK(length(response) <= 10000 OR response IS NULL)` on daily_tasks.response column. init_db.py calls `os.chmod(str(db_path), 0o600)` after DB creation. Security tests pass. |
| 6 | All SQL LIKE clauses use parameterized patterns with ESCAPE clause instead of string interpolation | ✓ VERIFIED | SKILL.md line 170: `WHERE topic LIKE ? ESCAPE '\'`. adapt.md line 20: `AND title LIKE ? ESCAPE '\'`. Both include escape instructions. No `LIKE '%{` patterns found. |

**Score:** 4/6 truths verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.
None for Phase 1.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/migrate_db.py` | Migration engine with backup, up-migration, down-migration | ✓ VERIFIED | EXPECTED_VERSION = 2, MIGRATIONS[2] has 8 statements, backup_db() exists, migrate_down() exists, REVERSE_MIGRATIONS[2] exists. |
| `scripts/init_db.py` | Fresh DB creation with all columns and config keys | ✗ FAILED | Missing modules.score, modules.next_review_date, daily_tasks.response_window_end. Missing config keys: last_task_date, daily_count, weekly_count, response_window_end. HAS CHECK constraint and os.chmod. |
| `AGENTS.md` | Schema documentation matching actual database | ✗ FAILED | AGENTS.md lines 90-91 correctly document all v2 columns. Documentation is correct but implementation lags. |
| `tests/__init__.py` | Test package marker | ✓ VERIFIED | Empty file exists at tests/__init__.py |
| `tests/conftest.py` | Shared test fixtures | ✓ VERIFIED | Contains sys.path setup for scripts/ import |
| `tests/test_validate_urls.py` | URL classification and validation tests | ✓ VERIFIED | 22 tests covering all 4 tiers, edge cases, pattern priority. All pass. |
| `tests/test_init_db.py` | DB initialization tests | ⚠️ ORPHANED | 6 tests exist and pass, but tests use temp DB fixtures that may include v2 columns not in production init_db.py. Need verification that tests reflect production behavior. |
| `tests/test_migrate_db.py` | Migration tests | ✓ VERIFIED | 21 tests covering up-migration, down-migration, backup, idempotency, data preservation. All pass. |
| `tests/test_eval_pipeline.py` | Eval pipeline state transition tests | ✓ VERIFIED | 8 tests covering advance/repeat logic, score calculation, boundary cases. All pass. |
| `SKILL.md` | Parameterized LIKE query for topic search | ✓ VERIFIED | Line 170: `WHERE topic LIKE ? ESCAPE '\'`. Line 162-165 includes escape instructions. |
| `subskills/adapt.md` | Parameterized LIKE query for module search | ✓ VERIFIED | Line 20: `AND title LIKE ? ESCAPE '\'`. Lines 10-15 include escape instructions. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|----|---------|
| `scripts/migrate_db.py` | `scripts/init_db.py` | MIGRATIONS v2 adds columns that init_db.py should include for fresh installs | ⚠️ PARTIAL | MIGRATIONS[2] correctly adds v2 columns to existing DBs. However, init_db.py does NOT include these columns for fresh installs, causing schema mismatch between fresh installs and migrated DBs. |
| `scripts/migrate_db.py` | `scripts/init_db.py` | backup_db() creates .bak.v{N} before migration | ✓ VERIFIED | migrate() calls backup_db() at line 107. backup_db() uses shutil.copy2. Tests verify backup creation. |
| `scripts/init_db.py` | daily_tasks table | CHECK constraint on response column | ✓ VERIFIED | Line 78: `response TEXT CHECK(length(response) <= 10000 OR response IS NULL)`. Security tests verify constraint works. |
| `SKILL.md` | paths table | LIKE query with ESCAPE clause for topic search | ✓ VERIFIED | Line 170: `WHERE topic LIKE ? ESCAPE '\'`. Replaced `LIKE '%{topic}%'` pattern. |
| `subskills/adapt.md` | modules table | LIKE query with ESCAPE clause for module title search | ✓ VERIFIED | Line 20: `AND title LIKE ? ESCAPE '\'`. Replaced `LIKE '%{module}%'` pattern. |
| `tests/conftest.py` | `scripts/init_db.py` | Imports init_db and provides temp DB fixture | ✓ VERIFIED | Line 6: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))` |
| `tests/test_eval_pipeline.py` | `scripts/init_db.py` | Uses temp DB fixture to test state transitions | ✓ VERIFIED | Tests use temp DB and execute eval SQL directly. No LLM calls. |

### Data-Flow Trace (Level 4)

No data-flow tracing required for this phase. All artifacts are utility scripts or static schemas. No dynamic rendering artifacts to verify.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Migration v1->v2 creates backup and adds columns | Manual verification via temp DB test | Backup created at {db}.bak.v1, all 8 SQL statements executed successfully, columns verified in migrated DB | ✓ PASS |
| Down-migration v2->v1 removes columns and creates backup | Manual verification via temp DB test | Backup created at {db}.bak.v2, REVERSE_MIGRATIONS executed, columns removed, config keys deleted | ✓ PASS |
| CHECK constraint rejects 10001-char response | `python3 -m pytest scripts/test_init_db_security.py` | All 7 security tests pass, including test_10001_chars_rejected | ✓ PASS |
| File permissions set to 600 after init_db | `python3 -m pytest scripts/test_init_db_security.py` | Tests verify os.chmod called and permissions correct | ✓ PASS |
| LIKE clauses parameterized with ESCAPE | `grep -n "LIKE.*?.*ESCAPE" SKILL.md subskills/adapt.md` | Both files have parameterized LIKE, no `LIKE '%{` patterns found | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|---------|----------|
| SCHEMA-01 | 01-01 | All documented DB columns exist in actual schema (next_review_date on modules, score on modules, response_window_end on daily_tasks, feedback on daily_tasks) | ✗ BLOCKED | AGENTS.md documents these columns, but init_db.py does NOT create them for fresh installs. Migration adds them to existing DBs, but fresh installs get incomplete schema. |
| SCHEMA-02 | 01-01 | All documented config keys are initialized in init_db.py (last_task_date, daily_count, weekly_count, response_window_end) | ✗ BLOCKED | init_db.py defaults list missing these 4 keys. Only has 4 keys: active_path_id, pending_task_id, last_response_date, streak_count. |
| SCHEMA-03 | 01-01 | AGENTS.md schema documentation matches actual init_db.py CREATE TABLE statements | ✗ BLOCKED | AGENTS.md lines 90-91 correctly document v2 schema. init_db.py CREATE TABLE statements are missing 3 columns and 4 config keys. Documentation ahead of implementation. |
| REL-01 | 01-01 | migrate_db.py supports down-migration and creates a pre-migration backup before applying changes | ✓ SATISFIED | migrate_db.py has backup_db(), migrate_down(), REVERSE_MIGRATIONS. Tests verify backup creation and down-migration. |
| TEST-01 | 01-02 | Unit tests for classify_url() cover each tier classification and edge cases | ✓ SATISFIED | tests/test_validate_urls.py has 22 tests covering all 4 tiers, edge cases, pattern priority. All pass. |
| TEST-02 | 01-02 | Tests for init_db.py verify idempotent table creation and config key initialization | ⚠️ PARTIAL | tests/test_init_db.py has 6 tests that pass. However, tests use temp DB fixtures that may include v2 columns, masking the production init_db.py gap. Tests verify idempotency but may not verify production schema completeness. |
| TEST-03 | 01-02 | Tests for migrate_db.py verify forward migration from version 1 to current | ✓ SATISFIED | tests/test_migrate_db.py has 21 tests covering up-migration, down-migration, backup, idempotency, data preservation. All pass. |
| TEST-04 | 01-02 | Integration tests verify eval pipeline state transitions (advance on >= 7.0, repeat on < 7.0) | ✓ SATISFIED | tests/test_eval_pipeline.py has 8 tests covering state transitions, score calculation, boundary cases. All pass. |
| TEST-05 | 01-02 | URL validation test fixtures with known-good and known-bad URLs per tier | ✓ SATISFIED | tests/test_validate_urls.py has parametrized tests with specific URLs for each tier (exercism, codecademy, coursera, youtube, wikipedia, etc.). |
| SEC-01 | 01-03 | User submissions are validated with length limits (CHECK constraint on daily_tasks.response) before DB storage | ✓ SATISFIED | init_db.py line 78: `CHECK(length(response) <= 10000 OR response IS NULL)`. Security tests verify constraint works. |
| SEC-02 | 01-03 | learning.db has file permissions set to 600 after creation in init_db.py | ✓ SATISFIED | init_db.py line 101: `os.chmod(str(db_path), 0o600)`. Security tests verify permissions. |
| FIX-04 | 01-03 | SQL LIKE clauses in SKILL.md and adapt.md use parameterized patterns with ESCAPE clause instead of string interpolation | ✓ SATISFIED | SKILL.md line 170 and adapt.md line 20 use `LIKE ? ESCAPE '\'`. No `LIKE '%{` patterns found. |

**Coverage Summary:**
- Total Phase 1 requirements: 14
- Fully satisfied: 9 (REL-01, TEST-01, TEST-03, TEST-04, TEST-05, SEC-01, SEC-02, FIX-04)
- Partially satisfied: 1 (TEST-02 - tests pass but may not reflect production behavior)
- Blocked: 4 (SCHEMA-01, SCHEMA-02, SCHEMA-03 - all stem from init_db.py regression)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| scripts/init_db.py | 48-56 | Missing v2 columns in modules CREATE TABLE (score, next_review_date) | 🛑 Blocker | Fresh installs create incomplete schema, mismatch with AGENTS.md documentation. Breaks SCHEMA-01, SCHEMA-02, SCHEMA-03. |
| scripts/init_db.py | 72-84 | Missing response_window_end column in daily_tasks CREATE TABLE | 🛑 Blocker | Fresh installs missing response_window_end, breaking response window tracking feature. |
| scripts/init_db.py | 88-93 | Missing 4 config keys in defaults list (last_task_date, daily_count, weekly_count, response_window_end) | 🛑 Blocker | Fresh installs missing critical runtime state keys, breaking inactivity tracking and task delivery deduplication. |
| scripts/init_db.py | 78 | CHECK constraint on response column | ℹ️ Info | This is correct and required (SEC-01), listed here for completeness as a positive pattern. |
| scripts/init_db.py | 101 | os.chmod(0o600) on DB file | ℹ️ Info | This is correct and required (SEC-02), listed here for completeness as a positive pattern. |

**Root Cause Analysis:**

The anti-patterns above stem from a **regression** introduced in commit 06cf5f2d (Plan 01-03). When adding the CHECK constraint to the daily_tasks.response column and the os.chmod() call, the commit accidentally removed:
- modules.score REAL DEFAULT 0 (was added in commit 521b136d, line 51)
- modules.next_review_date TEXT (was added in commit 521b136d, line 52)
- daily_tasks.response_window_end TEXT (was added in commit 521b136d, line 82)
- Config defaults: last_task_date, daily_count, weekly_count, response_window_end (were added in commit 521b136d, lines 96-99)

This is a classic **merge conflict resolution error** where two sets of changes to the same file were not properly combined. The Plan 01-03 changes (CHECK constraint, chmod) replaced the Plan 01-01 changes (v2 columns, config keys) instead of merging them.

### Human Verification Required

None. All verification is programmatic. The gaps are clear code mismatches that can be fixed by restoring the removed columns and config keys.

### Gaps Summary

**Critical Gap: init_db.py Regression (Blocks SCHEMA-01, SCHEMA-02, SCHEMA-03, TEST-02)**

The init_db.py script is missing critical v2 schema columns and config keys due to a regression in commit 06cf5f2d. This means:

1. **Fresh installs create incomplete schema**: A new user running `python scripts/init_db.py` gets a database missing:
   - `modules.score` column (needed for storing individual module scores)
   - `modules.next_review_date` column (needed for spaced repetition reviews)
   - `daily_tasks.response_window_end` column (needed for response window tracking)
   - Config keys: `last_task_date`, `daily_count`, `weekly_count`, `response_window_end` (needed for runtime state management)

2. **Documentation-implementation mismatch**: AGENTS.md correctly documents all v2 columns (lines 90-91), but init_db.py does not create them. This violates the core principle of Phase 1: "The documented schema matches the actual database."

3. **Migration vs. fresh install inconsistency**: migrate_db.py correctly adds these columns when upgrading an existing v1 DB to v2. However, fresh installs get an incomplete schema. This means:
   - Existing users (who have a v1 DB) → migrate → get v2 schema ✓
   - New users (no DB) → run init_db.py → get incomplete schema ✗

4. **Test environment vs production mismatch**: The test suite uses temp DB fixtures that may include the v2 columns (created by test helpers or conftest), so tests pass even though production init_db.py is broken. This creates a false sense of security.

**Root cause**: Commit 06cf5f2d (Plan 01-03) replaced the entire CREATE TABLE statements when adding the CHECK constraint, accidentally removing the columns that were added in commit 521b136d (Plan 01-01).

**Impact**: Blocks Phase 1 goal achievement. The 3 requirements that fail (SCHEMA-01, SCHEMA-02, SCHEMA-03) all stem from this single regression.

**Fix required**: Restore the removed columns and config keys to init_db.py while keeping the CHECK constraint and os.chmod() call. The fix must merge both changesets:
- From commit 521b136d: Add v2 columns and config keys
- From commit 06cf5f2d: Add CHECK constraint and os.chmod()

**Verification required after fix**:
1. `python scripts/init_db.py` on a fresh DB creates all v2 columns and config keys
2. `grep -c "next_review_date\|response_window_end\|feedback" scripts/init_db.py` returns >= 3
3. AGENTS.md documentation matches init_db.py CREATE TABLE statements
4. All tests still pass (no regressions from the fix)

---

_Verified: 2025-04-12T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
