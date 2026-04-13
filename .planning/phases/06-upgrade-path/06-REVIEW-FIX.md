---
phase: 06-upgrade-path
fixed_at: 2026-04-13T00:00:00Z
review_path: .planning/phases/06-upgrade-path/06-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-04-13
**Source review:** .planning/phases/06-upgrade-path/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2 (critical_warning scope; 0 critical, 2 warning)
- Fixed: 2
- Skipped: 0

## Fixed Issues

### WR-01: Inconsistent exit behavior when DB schema is newer than expected

**Files modified:** `scripts/migrate_db.py`
**Commit:** 157276a4
**Applied fix:** Changed the `migrate()` function's `current > EXPECTED_VERSION` branch to call `sys.exit(1)` instead of silently returning. This makes the behavior consistent with `check_and_migrate()`, which already exited with code 1 in the same scenario.

### WR-02: Potential None dereference when querying active_path_id

**Files modified:** `subskills/init.md`
**Commit:** 09f6932c
**Applied fix:** Added a `if p:` null guard around the `print(f'ACTIVE_PATH: ...')` line in the inline Python script. If `fetchone()` returns None (path id stored in config references a deleted path), the script now prints `NO_ACTIVE_PATH` instead of raising an `IndexError`.

---

_Fixed: 2026-04-13_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
