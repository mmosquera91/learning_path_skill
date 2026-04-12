---
phase: 01-foundation
plan: 01
subsystem: database
tags: [sqlite, migration, schema, python]

# Dependency graph
requires: []
provides:
  - v1->v2 migration engine with backup and down-migration in scripts/migrate_db.py
  - Fresh install schema aligned with documentation in scripts/init_db.py
  - AGENTS.md schema documentation matching actual database schema
  - Test suite for migration operations in tests/test_migrate_db.py
affects: [01-02, 01-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD with pytest for database migration code"
    - "Backup-before-migrate pattern using shutil.copy2"
    - "Down-migration via CREATE TABLE AS SELECT / DROP / RENAME pattern"

key-files:
  created:
    - tests/test_migrate_db.py
  modified:
    - scripts/migrate_db.py
    - scripts/init_db.py
    - AGENTS.md

key-decisions:
  - "Disable foreign keys during down-migration to prevent CASCADE deletes when tables are dropped and recreated"
  - "Reorder reverse migration to handle daily_tasks before modules (correct dependency order for reconstruction)"
  - "Fix AGENTS.md 'Adding a New Column' guide which incorrectly said not to modify init_db.py"

patterns-established:
  - "TDD for migration scripts: write tests first, implement to pass, commit separately"
  - "Migration backup pattern: create .bak.v{N} before any migration or down-migration"

requirements-completed: [SCHEMA-01, SCHEMA-02, SCHEMA-03, REL-01]

# Metrics
duration: 4min
completed: 2026-04-12
---

# Phase 01 Plan 01: Schema Alignment Summary

**SQLite v1->v2 migration with backup/down-migration support, init_db.py fresh-install alignment, and AGENTS.md documentation synchronization**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-12T18:52:19Z
- **Completed:** 2026-04-12T18:56:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- v1->v2 migration engine with 8 SQL statements (4 ALTER TABLE + 4 INSERT OR IGNORE config keys)
- Backup-before-migrate pattern creating .bak.v{N} files before any schema change
- Down-migration support via --down flag that reverses v2 changes and creates backup
- init_db.py updated with all missing columns (modules.score, modules.next_review_date, daily_tasks.response_window_end) and config defaults (last_task_date, daily_count, weekly_count, response_window_end)
- 21 pytest tests covering constants, up-migration, down-migration, idempotency, data preservation, and backup creation
- AGENTS.md "Adding a New Column" guide fixed to correctly reference both migrate_db.py and init_db.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Add v1->v2 migration with backup and down-migration** - `0803695` (test), `7bc2bf2` (feat)
2. **Task 2: Update init_db.py and AGENTS.md schema documentation** - `3c980d6` (feat)

_Note: Task 1 used TDD with separate RED and GREEN commits._

## Files Created/Modified
- `tests/test_migrate_db.py` - 21 pytest tests for migration constants, up-migration, down-migration, idempotency, data preservation, and backup creation
- `scripts/migrate_db.py` - Migration engine upgraded to v2 with backup_db(), migrate_down(), REVERSE_MIGRATIONS dict, and --down CLI flag
- `scripts/init_db.py` - Added score REAL DEFAULT 0, next_review_date TEXT to modules; response_window_end TEXT to daily_tasks; 4 new config defaults
- `AGENTS.md` - Fixed "Adding a New Column" guide; updated migrate_db.py file structure description

## Decisions Made
- **Disable FK during down-migration**: Foreign keys must be OFF during down-migration because the CREATE TABLE AS SELECT / DROP / RENAME pattern drops tables that have CASCADE relationships, which would silently delete data from dependent tables (e.g., dropping modules cascades to daily_tasks).
- **Reorder reverse migration**: daily_tasks must be backed up and rebuilt before modules because daily_tasks depends on modules via FK. Even with FK off, ordering correctly prevents data loss if FK enforcement is accidentally re-enabled mid-migration.
- **Fix AGENTS.md guide**: The existing documentation had a contradiction -- step 1 said "Do NOT modify init_db.py" while step 3 said "Update init_db.py SCHEMA". Resolved by rewriting the guide to clearly state both files must be updated.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test helper missing schema_version table creation**
- **Found during:** Task 1 (TDD RED phase, first test run)
- **Issue:** `_create_v1_db()` test fixture did not create the `schema_version` table before inserting a version row, causing `sqlite3.OperationalError: no such table: schema_version`
- **Fix:** Added `c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")` to the test fixture
- **Files modified:** `tests/test_migrate_db.py`
- **Committed in:** `7bc2bf2` (part of Task 1 GREEN commit)

**2. [Rule 1 - Bug] Down-migration CASCADE delete destroying daily_tasks data**
- **Found during:** Task 1 (TDD GREEN phase, test_down_migration_preserves_existing_data)
- **Issue:** Reverse migration dropped `modules` first, which cascaded and deleted all `daily_tasks` rows via ON DELETE CASCADE. Then daily_tasks_backup was created from an already-empty table, resulting in 0 rows after rename.
- **Fix:** Two-part fix: (1) Set `PRAGMA foreign_keys=OFF` in `migrate_down()` to prevent CASCADE during table reconstruction, (2) Reordered REVERSE_MIGRATIONS to handle daily_tasks before modules (correct dependency order)
- **Files modified:** `scripts/migrate_db.py`
- **Committed in:** `7bc2bf2` (part of Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. The CASCADE issue would have caused silent data loss in production down-migrations. No scope creep.

## Issues Encountered
- pytest was not installed in the environment; installed with `pip3 install --break-system-packages pytest`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Schema alignment complete -- init_db.py, migrate_db.py, and AGENTS.md are synchronized
- Test infrastructure (pytest) is now available for subsequent plans
- Migration backup pattern established for safe schema changes going forward
- Plan 01-02 (URL validation hardening) and 01-03 (subskill cleanup) can proceed without schema concerns

## Self-Check: PASSED

All files exist, all commits verified, no stubs detected, no unexpected threat surface.

---
*Phase: 01-foundation*
*Completed: 2026-04-12*
