# Roadmap: Tutor Skill Hardening

## Overview

Harden the existing Hermes Tutor skill by fixing the schema-documentation mismatch, building a test safety net, deduplicating tier rules, reducing subskill line counts, correcting template bugs, and cleaning security debt. The critical path starts with schema alignment (the blocker for everything else) and a test suite (the safety net for all refactoring), then progresses through structural cleanup, correctness fixes, and finally a destructive git history purge.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Schema alignment, test suite, input validation, and SQL safety
- [ ] **Phase 2: Code Quality** - Tier rule deduplication and context budget reduction
- [ ] **Phase 3: Correctness** - Template syntax fixes, error handling, and command format corrections
- [ ] **Phase 4: Security Cleanup** - Git history purge

## Phase Details

### Phase 1: Foundation
**Goal**: The documented schema matches the actual database, all config keys are initialized, and a test suite exists to validate safe refactoring in subsequent phases
**Depends on**: Nothing (first phase)
**Requirements**: SCHEMA-01, SCHEMA-02, SCHEMA-03, REL-01, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, SEC-01, SEC-02, FIX-04
**Success Criteria** (what must be TRUE):
  1. `python scripts/init_db.py` creates all documented columns (next_review_date, score, response_window_end, feedback) and initializes all config keys (last_task_date, daily_count, weekly_count, response_window_end)
  2. `python -m pytest tests/` passes with tests covering DB operations, state transitions, URL validation, eval pipeline, and migration
  3. AGENTS.md schema documentation matches the actual CREATE TABLE statements in init_db.py
  4. migrate_db.py creates a backup before applying changes and supports down-migration to the previous version
  5. User submissions longer than a defined limit are rejected before being written to the database, and learning.db is created with 600 permissions
  6. All SQL LIKE clauses use parameterized patterns with ESCAPE clause instead of string interpolation
**Plans:** 3 plans

Plans:
- [x] 01-01: Schema migration, config initialization, backup/down-migration, and AGENTS.md alignment
- [ ] 01-02: Test suite for URL validation, DB init, migration, and eval pipeline state transitions
- [ ] 01-03: Input validation (CHECK constraint), DB file permissions (chmod 600), and SQL parameterization

### Phase 2: Code Quality
**Goal**: Tier rules exist in one canonical location, SKILL.md is under 200 lines, and init.md is under 150 lines
**Depends on**: Phase 1
**Requirements**: DEDUP-01, QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. Tier classification rules are defined in CONTRIBUTING.md and validate_urls.py only -- SKILL.md and init.md reference them instead of containing inline copies
  2. `wc -l SKILL.md` reports fewer than 200 lines and the skill routes commands correctly
  3. `wc -l subskills/init.md` reports fewer than 150 lines and the init flow (syllabus generation, URL validation, path activation) still works end-to-end
**Plans:** TBD

Plans:
- [ ] 02-01: Tier rule deduplication and SKILL.md reduction
- [ ] 02-02: init.md extraction (syllabus prompt to template, save logic to script)

### Phase 3: Correctness
**Goal**: Subskill templates use consistent syntax, daily.md handles failures gracefully, and syllabus commands reference the correct format
**Depends on**: Phase 2
**Requirements**: FIX-01, FIX-02, FIX-03
**Success Criteria** (what must be TRUE):
  1. eval.md uses a single consistent placeholder format throughout (no mixing of Mustache and plain text)
  2. daily.md produces a Telegram message or logs a specific error when task generation, DB write, or Telegram delivery fails
  3. Syllabus template output references `/tutor confirm` and `/tutor edit` (not any other command format)
**Plans:** TBD

Plans:
- [ ] 03-01: Template syntax and command format fixes
- [ ] 03-02: Error handling in daily.md

### Phase 4: Security Cleanup
**Goal**: learning.db is purged from all git history with no recoverable blob
**Depends on**: Phase 3
**Requirements**: SEC-03
**Success Criteria** (what must be TRUE):
  1. `git log --all --diff-filter=A -- learning.db` returns no results
  2. `git rev-list --all -- learning.db | xargs git grep -l` returns no results (no blob contains the file)
**Plans:** TBD

Plans:
- [ ] 04-01: Purge learning.db from git history

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/3 | Planning complete | - |
| 2. Code Quality | 0/2 | Not started | - |
| 3. Correctness | 0/2 | Not started | - |
| 4. Security Cleanup | 0/1 | Not started | - |
