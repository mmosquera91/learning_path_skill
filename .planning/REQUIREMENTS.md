# Requirements: Tutor Skill Hardening

**Defined:** 2026-04-12
**Updated:** 2026-04-13 (v1.1 requirements added)
**Core Value:** The Tutor skill reliably delivers a daily learning task, evaluates the user's submission, and progresses through the learning path — every day, without silent failures or broken state.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Schema & Config

- [x] **SCHEMA-01**: All documented DB columns exist in actual schema (next_review_date on modules, score on modules, response_window_end on daily_tasks, feedback on daily_tasks) — Phase 1
- [x] **SCHEMA-02**: All documented config keys are initialized in init_db.py (last_task_date, daily_count, weekly_count, response_window_end) — Phase 1
- [x] **SCHEMA-03**: AGENTS.md schema documentation matches actual init_db.py CREATE TABLE statements — Phase 1

### Correctness

- [x] **FIX-01**: eval.md uses plain text placeholders ({variable}) instead of Mustache syntax ({{variable}}) — Phase 3
- [x] **FIX-02**: syllabus template references correct command format (/tutor confirm, /tutor edit) — Phase 3
- [x] **FIX-03**: daily.md has explicit error handling for task generation failure, DB write failure, and Telegram delivery failure — Phase 3
- [x] **FIX-04**: SQL LIKE clauses in SKILL.md and adapt.md use parameterized patterns with ESCAPE clause instead of string interpolation — Phase 1

### Security

- [x] **SEC-01**: User submissions are validated with length limits (CHECK constraint on daily_tasks.response) before DB storage — Phase 1
- [x] **SEC-02**: learning.db has file permissions set to 600 after creation in init_db.py — Phase 1
- [x] **SEC-03**: learning.db is purged from all git history (no recoverable blob) — Phase 4

### Code Quality

- [x] **DEDUP-01**: Tier system rules are defined in one canonical location (CONTRIBUTING.md + validate_urls.py), referenced by SKILL.md and init.md instead of duplicated inline — Phase 2
- [x] **QUAL-01**: init.md is reduced to under 150 lines by extracting syllabus generation prompt to a template and save-to-DB logic to a Python script — Phase 2
- [x] **QUAL-02**: SKILL.md is under 200 lines after tier rule deduplication and any additional trimming — Phase 2

### Testing

- [x] **TEST-01**: Unit tests for classify_url() cover each tier classification and edge cases — Phase 1
- [x] **TEST-02**: Tests for init_db.py verify idempotent table creation and config key initialization — Phase 1
- [x] **TEST-03**: Tests for migrate_db.py verify forward migration from version 1 to current — Phase 1
- [x] **TEST-04**: Integration tests verify eval pipeline state transitions (advance on >= 7.0, repeat on < 7.0) — Phase 1
- [x] **TEST-05**: URL validation test fixtures with known-good and known-bad URLs per tier — Phase 1

### Reliability

- [x] **REL-01**: migrate_db.py supports down-migration and creates a pre-migration backup before applying changes — Phase 1

## v1.1 Requirements

Requirements for v1.1 milestone: Usability & Upgrade Path.

### Documentation

- [ ] **README-01**: Audit current README.md — identify inaccurate/outdated claims vs actual implementation
- [ ] **README-02**: Rewrite README.md sections to match current state — remove untested features, fix setup instructions, add real example session, fix command formats

### Migration

- [ ] **MIGRATE-01**: Wire migrate_db.py into subskills/init.md — Step 0 must call `python3 scripts/migrate_db.py --check` and run migrations before init
- [ ] **UPGRADE-01**: Document upgrade path — what existing v1.0 users must do, what data is preserved, what might break
- [ ] **UPGRADE-02**: Test upgrade path end-to-end — simulate existing user with schema v1 data, run migration, verify everything works

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Reliability

- **REL-02**: Stale cron prompt detection via version hash in subskills, with Telegram warning on mismatch
- **REL-03**: Structured local logging for cron invocations and user commands

### Features

- **FEAT-01**: Inactivity handling — graduated nudge (2 days), pause offer (3 days), auto-pause (5 days)
- **FEAT-02**: Decompose logic for scores < 4.0 — insert sub-modules, shift module order
- **FEAT-03**: Spaced repetition review delivery via daily cron

### Testing

- **TEST-06**: LLM state transition validation tests (decompose branch)
- **TEST-07**: End-to-end tests for full init -> daily -> eval -> adapt cycle

## Out of Scope

| Feature | Reason |
|---------|--------|
| Compiled code layer for state transitions | Violates Hermes architecture — all logic lives in Markdown |
| External guardrail frameworks (NeMo, Guardrails AI) | Requires persistent runtime; contradicts zero-dependency constraint |
| Multi-user support | Requires complete architecture redesign (PostgreSQL, auth, sessions) |
| Encrypted database (SQLCipher) | Not in Python stdlib; single-user threat model doesn't justify it |
| Real-time observability (LangSmith, Langfuse) | Requires API keys and network; contradicts offline-first design |
| Interactive UI or web interface | Future v2 direction, not current scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCHEMA-01 | Phase 1 | Complete |
| SCHEMA-02 | Phase 1 | Complete |
| SCHEMA-03 | Phase 1 | Complete |
| REL-01 | Phase 1 | Complete |
| TEST-01 | Phase 1 | Complete |
| TEST-02 | Phase 1 | Complete |
| TEST-03 | Phase 1 | Complete |
| TEST-04 | Phase 1 | Complete |
| TEST-05 | Phase 1 | Complete |
| SEC-01 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| FIX-04 | Phase 1 | Complete |
| DEDUP-01 | Phase 2 | Complete |
| QUAL-01 | Phase 2 | Complete |
| QUAL-02 | Phase 2 | Complete |
| FIX-01 | Phase 3 | Complete |
| FIX-02 | Phase 3 | Complete |
| FIX-03 | Phase 3 | Complete |
| SEC-03 | Phase 4 | Complete |
| README-01 | Phase 5 | Pending |
| README-02 | Phase 5 | Pending |
| MIGRATE-01 | Phase 6 | Pending |
| UPGRADE-01 | Phase 6 | Pending |
| UPGRADE-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 18 total, 18 mapped to phases, 18 complete
- v1.1 requirements: 5 total, 5 mapped to phases, 0 complete
- All 23 requirements mapped

---
*Requirements defined: 2026-04-12*
*Last updated: 2026-04-13 with v1.1 requirements added*
