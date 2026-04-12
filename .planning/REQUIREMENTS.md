# Requirements: Tutor Skill Hardening

**Defined:** 2026-04-12
**Core Value:** The Tutor skill reliably delivers a daily learning task, evaluates the user's submission, and progresses through the learning path — every day, without silent failures or broken state.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Schema & Config

- [ ] **SCHEMA-01**: All documented DB columns exist in actual schema (next_review_date on modules, score on modules, response_window_end on daily_tasks, feedback on daily_tasks)
- [ ] **SCHEMA-02**: All documented config keys are initialized in init_db.py (last_task_date, daily_count, weekly_count, response_window_end)
- [ ] **SCHEMA-03**: AGENTS.md schema documentation matches actual init_db.py CREATE TABLE statements

### Correctness

- [ ] **FIX-01**: eval.md uses plain text placeholders ({variable}) instead of Mustache syntax ({{variable}})
- [ ] **FIX-02**: syllabus template references correct command format (/tutor confirm, /tutor edit)
- [ ] **FIX-03**: daily.md has explicit error handling for task generation failure, DB write failure, and Telegram delivery failure
- [ ] **FIX-04**: SQL LIKE clauses in SKILL.md and adapt.md use parameterized patterns with ESCAPE clause instead of string interpolation

### Security

- [ ] **SEC-01**: User submissions are validated with length limits (CHECK constraint on daily_tasks.response) before DB storage
- [ ] **SEC-02**: learning.db has file permissions set to 600 after creation in init_db.py
- [ ] **SEC-03**: learning.db is purged from all git history (no recoverable blob)

### Code Quality

- [ ] **DEDUP-01**: Tier system rules are defined in one canonical location (CONTRIBUTING.md + validate_urls.py), referenced by SKILL.md and init.md instead of duplicated inline
- [ ] **QUAL-01**: init.md is reduced to under 150 lines by extracting syllabus generation prompt to a template and save-to-DB logic to a Python script
- [ ] **QUAL-02**: SKILL.md is under 200 lines after tier rule deduplication and any additional trimming

### Testing

- [ ] **TEST-01**: Unit tests for classify_url() cover each tier classification and edge cases
- [ ] **TEST-02**: Tests for init_db.py verify idempotent table creation and config key initialization
- [ ] **TEST-03**: Tests for migrate_db.py verify forward migration from version 1 to current
- [ ] **TEST-04**: Integration tests verify eval pipeline state transitions (advance on >= 7.0, repeat on < 7.0)
- [ ] **TEST-05**: URL validation test fixtures with known-good and known-bad URLs per tier

### Reliability

- [ ] **REL-01**: migrate_db.py supports down-migration and creates a pre-migration backup before applying changes

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
- **TEST-07**: End-to-end tests for full init → daily → eval → adapt cycle

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
| SCHEMA-01 | — | Pending |
| SCHEMA-02 | — | Pending |
| SCHEMA-03 | — | Pending |
| FIX-01 | — | Pending |
| FIX-02 | — | Pending |
| FIX-03 | — | Pending |
| FIX-04 | — | Pending |
| SEC-01 | — | Pending |
| SEC-02 | — | Pending |
| SEC-03 | — | Pending |
| DEDUP-01 | — | Pending |
| QUAL-01 | — | Pending |
| QUAL-02 | — | Pending |
| TEST-01 | — | Pending |
| TEST-02 | — | Pending |
| TEST-03 | — | Pending |
| TEST-04 | — | Pending |
| TEST-05 | — | Pending |
| REL-01 | — | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 0
- Unmapped: 18

---
*Requirements defined: 2026-04-12*
*Last updated: 2026-04-12 after initial definition*
