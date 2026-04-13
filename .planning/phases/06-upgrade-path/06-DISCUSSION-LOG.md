# Phase 6: Upgrade Path - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 06-upgrade-path
**Areas discussed:** Migration order, --check flag behavior, Upgrade doc scope, Test strategy

---

## Gray Area 1: Migration Call Location

| Option | Description | Selected |
|--------|-------------|----------|
| Before init_db.py (Recommended) | migrate_db.py --check runs first, then init_db.py. Ensures existing DBs migrated before init touches them | ✓ |
| After init_db.py | init_db.py runs first (creates fresh DB), then migrate_db.py --check runs. Simpler ordering | |
| Conditionally | Check if DB exists + needs migration first, only then run migrate | |

**User's choice:** Before init_db.py (Recommended)
**Notes:** Migration runs before init. This ensures existing v1.0 DBs are brought to current schema before init_db.py creates/updates tables.

---

## Gray Area 2: --check Flag Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Check + apply if needed (Recommended) | --check verifies version, runs migration automatically if DB is behind. Cleanest UX | ✓ |
| Check only | --check reports version/status but doesn't migrate. Separate invocation without --check does migration | |
| Check + prompt | --check reports status and asks user to confirm before migrating. Requires interaction | |

**User's choice:** Check + apply if needed (Recommended)
**Notes:** Existing users upgrading just run /tutor init and migration happens silently. No user action needed. The --check flag needs to be added to migrate_db.py (doesn't exist yet).

---

## Gray Area 3: Upgrade Documentation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal (Recommended) | Brief section in README: migration automatic, data preserved, no user action needed. 3-5 sentences | ✓ |
| Detailed | Full section covering schema changes, preserved data, known issues, rollback steps | |
| Separate UPGRADE.md | Dedicated upgrade guide file. Keeps README clean but adds file to maintain | |

**User's choice:** Minimal (Recommended)
**Notes:** Keep README clean. 3-5 sentence upgrade section is sufficient. No separate UPGRADE.md file needed.

---

## Gray Area 4: Test Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| pytest script (Recommended) | pytest test creating v1 schema DB, inserting test data, running migration, verifying data. Follows Phase 1 test patterns | ✓ |
| Manual test script | Bash script doing same verification. Simpler but less formal than pytest | |
| Document only | Verify migration correctness via code review, no automated test | |

**User's choice:** pytest script (Recommended)
**Notes:** Follow Phase 1 test patterns. Test file: scripts/test_migrate_db.py. Should create v1 schema, insert test data, run migration, verify data integrity.

---

## Claude's Discretion

- Exact error messages when migration fails (keep human-readable)
- Whether to print migration progress to stdout or be silent on success
- Specific backup file naming if multiple migrations happen

## Deferred Ideas

None — all scope items discussed and resolved.
