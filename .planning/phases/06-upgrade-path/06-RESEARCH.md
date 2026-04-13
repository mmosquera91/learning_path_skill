# Phase 6: Upgrade Path - Research

**Researched:** 2026-04-13
**Domain:** Database migration wiring, upgrade UX, pytest testing
**Confidence:** HIGH

## Summary

Phase 6 wires the existing `migrate_db.py` into `init.md` Step 0 (before `init_db.py`) and adds a `--check` flag that auto-migrates existing v1.0 users silently. The migration engine already exists and is tested in `tests/test_migrate_db.py` (21 pytest tests covering up-migration, down-migration, idempotency, data preservation). The new work is: (1) add `--check` CLI flag to `migrate_db.py`, (2) update `init.md` Step 0 call order, (3) add `--check`-specific tests, (4) document upgrade path in README.md.

**Primary recommendation:** Add `--check` to `migrate_db.py` argparse with behavior: no DB = silent exit, current schema = print + exit 0, behind = auto-migrate. Wire it in `init.md` Step 0 before `init_db.py`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `migrate_db.py --check` runs in `init.md` Step 0 BEFORE `init_db.py`. Order: migrate then init.
- **D-02:** `--check` auto-migrates if DB is behind EXPECTED_VERSION. Clean UX: existing users run `/tutor init` and migration happens silently with no user action needed.
- **D-03:** `--check` flag must be ADDED to `migrate_db.py` — it doesn't exist yet.
- **D-04:** Brief "Upgrading from v1.0" section in README.md (3-5 sentences).
- **D-05:** No separate UPGRADE.md file.
- **D-06:** pytest test that creates a v1 schema DB (schema_version=1), inserts test data, runs migration, verifies data integrity.
- **D-07:** Test file: `scripts/test_migrate_db.py` (pytest format).

### Claude's Discretion
- Exact error messages when migration fails (keep them human-readable)
- Whether to print migration progress to stdout or be silent on success
- Specific backup file naming/numbering if multiple migrations happen

### Deferred Ideas (OUT OF SCOPE)
None — all scope items discussed and resolved.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MIGRATE-01 | Wire migrate_db.py into subskills/init.md — Step 0 must call `python3 scripts/migrate_db.py --check` and run migrations before init | init.md Step 0 currently calls only init_db.py; needs migrate call before it |
| UPGRADE-01 | Document upgrade path — what existing v1.0 users must do, what data is preserved, what might break | README.md needs 3-5 sentence upgrade section near Setup |
| UPGRADE-02 | Test upgrade path end-to-end — simulate existing user with schema v1 data, run migration, verify everything works | `tests/test_migrate_db.py` already has `create_v1_db()` fixture and data preservation tests; need `--check` flag tests added |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.11+ stdlib | built-in | All scripts use only stdlib (`sqlite3`, `argparse`, `shutil`, `os`, `sys`, `pathlib`) | Zero-dependency constraint from CLAUDE.md |
| pytest | existing in tests/ | Test framework for `tests/test_migrate_db.py` | Established in Phase 1 with 21 passing tests |
| argparse | built-in | CLI flag parsing in `migrate_db.py` | Already used by `validate_urls.py` |

### Test File Location Note
**CONFLICT DETECTED:** D-07 specifies `scripts/test_migrate_db.py` but Phase 1 established tests at `tests/test_migrate_db.py` (project root `tests/` directory). Phase 1 summary explicitly states: *"tests/test_migrate_db.py - 21 pytest tests"*. The existing 21-test suite lives in `tests/`. I will recommend following Phase 1's established pattern (tests at project root `tests/`) since those tests already exist and work.

## Architecture Patterns

### Project Structure
```
~/.hermes/skills/tutor/
├── SKILL.md
├── subskills/
│   ├── init.md              # Step 0: add migrate_db.py --check call
│   ├── daily.md
│   ├── eval.md
│   └── adapt.md
├── scripts/
│   ├── migrate_db.py        # Add --check flag
│   ├── init_db.py           # Already idempotent
│   └── validate_urls.py
├── tests/                   # Phase 1 established location
│   ├── test_migrate_db.py   # Add --check flag tests here
│   └── ...
├── templates/
└── learning.db
```

### Pattern 1: init.md Step 0 Call Order
**What:** `python3 scripts/migrate_db.py --check` runs BEFORE `python3 scripts/init_db.py`
**When to use:** Every `/tutor init` invocation
**Rationale:** Ensures existing v1 DBs are migrated before init touches them. Fresh DB (no file) exits migrate silently, then init creates it.

**Current init.md Step 0:**
```bash
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```

**New init.md Step 0:**
```bash
# Step 0: Migrate existing DB if needed (before init_db.py creates tables)
python3 ~/.hermes/skills/tutor/scripts/migrate_db.py --check
# Step 0b: Ensure DB exists (idempotent)
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```

### Pattern 2: --check Flag Behavior
**What:** Single CLI flag with three mutually exclusive outcomes
**When to use:** Called automatically on every `/tutor init`
**Example:**
```python
# In migrate_db.py argparse section:
if "--check" in sys.argv:
    idx = sys.argv.index("--check")
    if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
        path = sys.argv[idx + 1]
    # Run check logic instead of full migrate
```

**Three outcomes:**
| DB State | Behavior | Exit Code |
|----------|----------|-----------|
| No DB file | Print nothing, exit 0 silently | 0 |
| Schema current (v2) | Print "Already at schema v2", exit 0 | 0 |
| Schema behind (v1) | Run migrations, print progress, exit 0 | 0 |
| Schema newer (error) | Print error, exit 1 | 1 |

### Pattern 3: pytest Data Preservation Test
**What:** Create v1 DB, insert sample data, run migration, verify data intact
**When to use:** UPGRADE-02 requirement validation
**Example (from existing `tests/test_migrate_db.py`):**
```python
def test_existing_data_preserved_after_migration(self, tmp_path):
    db_path = str(tmp_path / "test.db")
    create_v1_db(db_path)
    migrate_db.migrate(db_path)
    conn = sqlite3.connect(db_path)
    # Check data is intact
    path = conn.execute("SELECT topic FROM paths WHERE id=1").fetchone()
    assert path[0] == "Python", "Path data corrupted"
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migration | Custom SQL scripts | `migrate_db.py` with MIGRATIONS dict | Already tested, handles idempotency, backup, version tracking |
| CLI flag parsing | Manual `sys.argv` string matching | `argparse.ArgumentParser` | Used by `validate_urls.py`, consistent with project |
| v1 test fixture | Inline schema definitions | `create_v1_db()` in `tests/test_migrate_db.py` | Already exists, matches actual v1 schema |

## Common Pitfalls

### Pitfall 1: migrate_db.py exits with error on fresh DB
**What goes wrong:** If `migrate_db.py` is called when no DB exists, it currently prints "DB not found at {path}. Run init_db.py first." and exits with code 1.
**Why it happens:** Current code at line 82-84 exits with `sys.exit(1)` when DB not found.
**How to avoid:** In `--check` mode, handle "DB not found" as a silent success — init_db.py will create the DB. In regular mode, keep the error message.
**Warning signs:** Existing users who run `/tutor init` get migration error before init creates DB.

### Pitfall 2: init.md call order mistake
**What goes wrong:** If `init_db.py` is called before `migrate_db.py --check`, existing v1 DBs get init's CREATE TABLE IF NOT EXISTS on a v1 schema that lacks v2 columns.
**Why it happens:** init_db.py uses CREATE TABLE IF NOT EXISTS, which doesn't add missing columns to existing tables.
**How to avoid:** Enforce migrate before init in Step 0. The order is the requirement.
**Warning signs:** Existing users' DBs missing `modules.score`, `modules.next_review_date`, `daily_tasks.response_window_end`, `daily_tasks.feedback`.

### Pitfall 3: Tests in wrong directory
**What goes wrong:** D-07 says `scripts/test_migrate_db.py` but Phase 1 established `tests/test_migrate_db.py` with 21 working tests.
**Why it happens:** Decision conflict between D-07 and Phase 1 established pattern.
**How to avoid:** Follow Phase 1's `tests/test_migrate_db.py` location since those tests already exist and the test file was created there during Phase 1.

### Pitfall 4: Backup file overwrite on repeated migration
**What goes wrong:** If migration runs twice on same DB, second backup overwrites first.
**Why it happens:** `backup_db()` uses fixed path `{db_path}.bak.v{version}`.
**How to avoid:** Accept this limitation (not in scope for v1.1). Claude's discretion covers backup naming.

## Code Examples

### migrate_db.py --check Flag Addition
Source: `scripts/migrate_db.py` lines 206-216 (existing argparse pattern from `validate_urls.py`)

```python
# Add to argparse section:
parser.add_argument('--check', action='store_true',
    help='Check schema version and migrate if needed. Exits 0 if current or migrated successfully.')

# New function:
def check_and_migrate(db_path: str = DB_PATH):
    """Check schema version, migrate if needed. Silent on fresh DB."""
    if not os.path.exists(db_path):
        # Fresh DB - init_db.py will create it. Silent success.
        return
    # ... rest of check logic
```

### init.md Step 0 Update
Source: `subskills/init.md` Step 0 (current)

```bash
### 0. Ensure database exists and migrate if needed
# Migrate existing v1 DBs to v2 schema (before init_db.py touches them)
python3 ~/.hermes/skills/tutor/scripts/migrate_db.py --check
# Ensure DB exists (idempotent - safe to run every time)
python3 ~/.hermes/skills/tutor/scripts/init_db.py
```

### README.md Upgrade Section Addition
Source: `README.md` Setup section (after line ~143 "The database initializes automatically on first use.")

```markdown
### Upgrading from v1.0

If you're upgrading from v1.0, the migration runs automatically when you first run `/tutor init`. All your existing learning paths, modules, and progress are preserved — no data loss. The migration adds new columns (score tracking, spaced repetition dates) and initializes new config keys. No action required on your part.
```

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this
> section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 1 tests at `tests/test_migrate_db.py` are the canonical location and should be extended rather than creating `scripts/test_migrate_db.py` | Standard Stack | Could cause confusion if D-07 (`scripts/test_migrate_db.py`) was intentional |
| A2 | pytest is installed and available (Phase 1 summary notes it was installed via `pip3 install --break-system-packages pytest`) | Environment | If pytest is not in PATH, tests won't run |
| A3 | The `--check` flag behavior (silent on fresh DB) is acceptable UX | Pitfall 1 | If user expects confirmation, they won't get it |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **Test file location conflict (D-07 vs Phase 1)**
   - What we know: D-07 says `scripts/test_migrate_db.py` but Phase 1 created tests at `tests/test_migrate_db.py`
   - What's unclear: Whether D-07 was an oversight or intentional override
   - Recommendation: Extend existing `tests/test_migrate_db.py` (Phase 1 pattern) and note the discrepancy

2. **Silent success on fresh DB**
   - What we know: `--check` should exit 0 silently when no DB exists
   - What's unclear: Whether users running `/tutor init` for the first time want any confirmation that migration check ran
   - Recommendation: Silent is correct per D-02 UX requirement

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — all tools are Python stdlib or already present in the project)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (uses pytest conventions) |
| Quick run command | `python3 -m pytest tests/test_migrate_db.py -x -v` |
| Full suite command | `python3 -m pytest tests/ -x -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MIGRATE-01 | migrate_db.py --check called in init.md Step 0 before init_db.py | manual verification | N/A (prompt inspection) | N/A |
| UPGRADE-01 | README.md has upgrade section | manual verification | N/A (doc inspection) | N/A |
| UPGRADE-02 | v1 schema DB migrates with data integrity | pytest | `python3 -m pytest tests/test_migrate_db.py::TestMigrationV2::test_existing_data_preserved_after_migration -x` | YES |
| D-03 (--check flag) | --check flag added to migrate_db.py | pytest | `python3 -m pytest tests/test_migrate_db.py -k check -x` | NO (new tests needed) |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_migrate_db.py -x -v`
- **Per wave merge:** `python3 -m pytest tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_migrate_db.py` — add `TestCheckFlag` class with tests for --check behavior
- [ ] `subskills/init.md` — verify Step 0 calls migrate before init
- [ ] Framework install: pytest already installed (per Phase 1)

## Security Domain

> Skip this section — Phase 6 is a wiring and documentation phase with no security-relevant changes. The migration itself was already implemented in Phase 1 with proper backup handling.

## Sources

### Primary (HIGH confidence)
- `scripts/migrate_db.py` — current migration engine with MIGRATIONS dict, EXPECTED_VERSION=2, backup logic
- `scripts/init_db.py` — current v2 schema with all columns (score, next_review_date, response_window_end, feedback)
- `subskills/init.md` — current Step 0 implementation
- `tests/test_migrate_db.py` — Phase 1 established pytest suite with create_v1_db() fixture

### Secondary (MEDIUM confidence)
- `.planning/phases/01-foundation/01-01-SUMMARY.md` — Phase 1 migration work documented, test file location confirmed
- `.planning/REQUIREMENTS.md` — MIGRATE-01, UPGRADE-01, UPGRADE-02 requirements
- `.planning/ROADMAP.md` — Phase 6 success criteria

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib, pytest already established
- Architecture: HIGH — call order is explicit in D-01, code patterns from existing files
- Pitfalls: MEDIUM — identified from code inspection, not yet validated with running tests

**Research date:** 2026-04-13
**Valid until:** 2026-05-13 (schema migration is stable, unlikely to change)
