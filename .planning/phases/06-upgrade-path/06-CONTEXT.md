# Phase 6: Upgrade Path - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire migration into init flow (so existing v1.0 users get automatic schema migration on upgrade) and document the upgrade path for existing users.

Requirements: MIGRATE-01, UPGRADE-01, UPGRADE-02
Depends on: Phase 5 (completed)

</domain>

<decisions>
## Implementation Decisions

### Migration Call Location
- **D-01:** `migrate_db.py --check` runs in `init.md` Step 0 BEFORE `init_db.py`. This ensures existing DBs are migrated before init touches them. Order: migrate → init.

### --check Flag Behavior
- **D-02:** `migrate_db.py --check` verifies current schema version, then runs migration automatically if the DB is behind EXPECTED_VERSION. Clean UX: existing users run `/tutor init` and migration happens silently with no user action needed.
- **D-03:** The `--check` flag must be ADDED to `migrate_db.py` — it doesn't exist yet. Behavior: if schema is current, print status and exit; if behind, run migrations automatically.

### Upgrade Documentation Scope
- **D-04:** Brief "Upgrading from v1.0" section in README.md (3-5 sentences). Content: migration is automatic on first `/tutor init`, learning data is preserved, no user action required.
- **D-05:** No separate UPGRADE.md file. Keep it simple in README.

### Test Strategy
- **D-06:** pytest test that creates a v1 schema DB (schema_version=1), inserts test data, runs migration, verifies data integrity. Follows Phase 1 test patterns.
- **D-07:** Test file: `scripts/test_migrate_db.py` (pytest format)

### Claude's Discretion
- Exact error messages when migration fails (keep them human-readable)
- Whether to print migration progress to stdout or be silent on success
- Specific backup file naming/numbering if multiple migrations happen

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 5 (prerequisite - completed)
- `.planning/phases/05-readme-redesign/05-01-SUMMARY.md` — Phase 5 completed README audit/rewrite
- `README.md` — Current state after Phase 5 rewrite

### Migration System
- `scripts/migrate_db.py` — Migration script needing --check flag added
- `scripts/init_db.py` — DB initialization (called after migrate in init.md)

### Requirements
- `.planning/REQUIREMENTS.md` §MIGRATE-01 — "Wire migrate_db.py into subskills/init.md"
- `.planning/REQUIREMENTS.md` §UPGRADE-01 — "Document upgrade path"
- `.planning/REQUIREMENTS.md` §UPGRADE-02 — "Test upgrade path end-to-end"

### Success Criteria (ROADMAP.md)
- `.planning/ROADMAP.md` §Phase 6 — All 4 success criteria listed

### Existing Test Patterns (Phase 1)
- Follow pytest patterns from Phase 1 (see `.planning/phases/01-foundation/` if available)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/migrate_db.py` — Already has forward + reverse migrations, backup logic, version tracking
- `scripts/init_db.py` — Already idempotent, creates fresh v2 schema
- `scripts/validate_urls.py` — Example of stdlib-only Python script with argparse

### Established Patterns
- init.md Step 0: single bash call to Python script
- Python scripts: shebang, module docstring, stdlib-only imports
- Tests: pytest format (Phase 1 established)

### Integration Points
- init.md Step 0: add migrate_db.py call before init_db.py
- migrate_db.py: add --check flag to CLI argparse
- README.md: add upgrade section near top or in Setup area

</code_context>

<specifics>
## Specific Ideas

- Migration call in init.md Step 0: `python3 ~/.hermes/skills/tutor/scripts/migrate_db.py --check`
- On fresh DB (no file): migrate_db.py currently exits with "DB not found". Need to handle this — init_db.py will create it.
- On already-current DB: migrate_db.py --check should print "Already at schema vN" and exit 0

</specifics>

<deferred>
## Deferred Ideas

None — all scope items discussed and resolved.

</deferred>

---

*Phase: 06-upgrade-path*
*Context gathered: 2026-04-13*
