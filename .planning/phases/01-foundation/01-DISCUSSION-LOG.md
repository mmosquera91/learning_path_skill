# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 1-Foundation
**Areas discussed:** Migration granularity, Test approach for eval pipeline

---

## Migration granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Single migration (v1→v2) | Add all missing columns, config keys, constraints in one migration. Simpler, atomic, one backup. | ✓ |
| Multiple sequential migrations | Separate migrations per logical group. More granular rollback but adds complexity. | |

**User's choice:** Single migration (v1→v2)

### Backup location

| Option | Description | Selected |
|--------|-------------|----------|
| Same directory with version suffix | `learning.db.bak.v{current_version}` in same directory. Simple, easy to find. | ✓ |
| Separate backups/ directory | Copy to `~/.hermes/skills/tutor/backups/` with timestamp. Cleaner but adds directory. | |

**User's choice:** Same directory with version suffix

### Down-migration trigger

| Option | Description | Selected |
|--------|-------------|----------|
| --down flag | Add flag to migrate_db.py for explicit manual rollback. | ✓ |
| Auto-rollback on failure | Automatically revert if migration fails mid-way. Safer but more complex. | |

**User's choice:** --down flag

---

## Test approach for eval pipeline

### LLM-driven state transition testing

| Option | Description | Selected |
|--------|-------------|----------|
| Mock JSON, test DB transitions | Feed fixed eval JSON into DB operations, verify state changes. No LLM calls. | ✓ |
| Real LLM calls | Call actual LLM to generate scores, then verify state. Expensive, non-deterministic. | |
| Extract logic to Python | Move transition logic to a testable Python function. More refactor but deterministic. | |

**User's choice:** Mock JSON, test DB transitions

### Test scope for eval pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| Test DB transitions only | Verify state changes with mocked input. Don't test prompt→SQL generation. | ✓ |
| Also test prompt→SQL generation | Verify Markdown prompts produce valid SQL. More thorough but harder to maintain. | |

**User's choice:** Test DB transitions only

---

## Claude's Discretion

- Response length limit (SEC-01) — deferred to Claude's judgment
- DB file permissions enforcement scope — deferred to Claude's judgment
- README.md schema update scope — deferred to Claude's judgment

## Deferred Ideas

None

---

*Discussion date: 2026-04-12*
