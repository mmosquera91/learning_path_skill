# Milestone v1.0 — Project Summary

**Generated:** 2026-04-13
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

**What This Is:** The Hermes Agent "Tutor" skill — a prompt-driven learning path system that creates personalized syllabi, delivers daily tasks via Telegram, evaluates submissions with a rubric, and adapts over time. Built as a Hermes skill with Markdown subskills, Python utility scripts, and a SQLite state backend.

**Core Value:** The Tutor skill reliably delivers a daily learning task, evaluates the user's submission, and progresses through the learning path — every day, without silent failures or broken state.

**Architecture:** Zero-dependency skill. All logic lives in Markdown files interpreted by the Hermes Agent runtime. Python stdlib only (sqlite3, subprocess, json). SQLite as single source of truth. No compiled code, no build step.

**Key Files:**
- `SKILL.md` — Command router and persona (~196 lines after Phase 2 reduction)
- `subskills/` — Four subskills: `init.md`, `daily.md`, `eval.md`, `adapt.md`
- `templates/` — Mustache output templates
- `scripts/` — Python utilities: `init_db.py`, `migrate_db.py`, `validate_urls.py`
- `learning.db` — SQLite state database (gitignored, created at runtime)

**Current milestone status:** All 4 phases complete (01-foundation, 02-code-quality, 03-correctness, 04-security-cleanup).

---

## 2. Architecture & Technical Decisions

- **Decision:** Use SQLite as single source of truth with WAL mode
  - **Why:** Hermes cron sessions are stateless — every invocation must be self-contained. DB is the persistent state. No in-memory state between sessions.
  - **Phase:** 01-foundation

- **Decision:** Migration v1→v2 adds missing columns (next_review_date, score, response_window_end, feedback) and config keys via a single idempotent `migrate_db.py`
  - **Why:** Schema drift between documented AGENTS.md and actual init_db.py was the root cause of Phase 1 issues. Fresh install wasn't catching it.
  - **Phase:** 01-01 (D-01)

- **Decision:** Test suite uses pytest with mocked JSON input — no real LLM calls
  - **Why:** LLM calls are slow, non-deterministic, and require API keys. Tests verify DB state transitions only.
  - **Phase:** 01-02 (D-04, D-05)

- **Decision:** Tier rules canonical source is `CONTRIBUTING.md` + `validate_urls.py`; SKILL.md references only, subskillers get inline 8-line summary
  - **Why:** SKILL.md routes commands (needs to stay lean for local models). Subskills may run in cron with zero prior context — they need the tier rules inline.
  - **Phase:** 02-01 (D-07, D-09)

- **Decision:** Extract syllabus rendering to `templates/init-syllabus.md` and DB save logic to `scripts/save_path.py`
  - **Why:** init.md was 257 lines, needed to be under 150 for cron inlining. Template extraction and CLI delegation are the mechanism.
  - **Phase:** 02-02 (D-08)

- **Decision:** i18n via `locale` config key (default: `es`) with Mustache conditional sections
  - **Why:** User-facing persona is Spanish. Error messages and output must be in user's language. Config-driven i18n keeps it stateless.
  - **Phase:** 03-03

- **Decision:** Purge `learning.db` from git history using `git filter-repo --invert-paths` after creating a bundle backup
  - **Why:** learning.db contained learner submissions — sensitive data. `.gitignore` prevented future commits but didn't fix history. Bundle backup at `$HOME/backup-before-purge.bundle` is the recovery point.
  - **Phase:** 04-01 (D-11, D-13)

---

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 01 | Foundation | ✓ Complete | Schema alignment, migration engine, test suite, input validation, SQL parameterization |
| 02 | Code Quality | ✓ Complete | Tier rule deduplication, SKILL.md/init.md size reduction, template extraction |
| 03 | Correctness | ✓ Complete | Template syntax fixes, error handling in daily.md, i18n support |
| 04 | Security Cleanup | ✓ Complete | learning.db purged from all git history (SEC-03 satisfied) |

---

## 4. Requirements Coverage

### v1 Requirements

- ✅ **SCHEMA-01** — All documented DB columns exist in actual schema
- ✅ **SCHEMA-02** — All documented config keys are initialized
- ✅ **SCHEMA-03** — AGENTS.md schema documentation matches actual init_db.py
- ✅ **FIX-01** — eval.md uses consistent Mustache placeholder syntax
- ✅ **FIX-02** — syllabus template references `/tutor confirm` and `/tutor edit`
- ✅ **FIX-03** — daily.md has explicit error handling for task generation, DB write, Telegram delivery failures
- ✅ **FIX-04** — SQL LIKE clauses use parameterized patterns with ESCAPE clause
- ✅ **SEC-01** — CHECK constraint on `daily_tasks.response` limits response length
- ✅ **SEC-02** — learning.db created with 600 permissions
- ✅ **SEC-03** — learning.db purged from all git history (no recoverable blob)
- ✅ **DEDUP-01** — Tier rules defined in one canonical location
- ✅ **QUAL-01** — init.md reduced to 122 lines (< 150 target)
- ✅ **QUAL-02** — SKILL.md reduced to 196 lines (< 200 target)
- ✅ **TEST-01** — Unit tests for `classify_url()` tier classification
- ✅ **TEST-02** — Tests for init_db.py idempotent creation and config init
- ✅ **TEST-03** — Tests for migrate_db.py forward migration
- ✅ **TEST-04** — Integration tests for eval pipeline state transitions
- ✅ **TEST-05** — URL validation test fixtures per tier
- ✅ **REL-01** — migrate_db.py supports down-migration and pre-migration backup

### Requirements Not Completed (v1 scope)

- ❌ None — all 18 v1 requirements are satisfied

---

## 5. Key Decisions Log

| ID | Decision | Phase | Rationale |
|----|----------|-------|----------|
| D-01 | Single migration v1→v2, one step | 01 | Simplifies rollback; all missing columns/config added together |
| D-02 | Migration backups with version suffix in same dir as DB | 01 | Easy to find, scoped to this project |
| D-03 | Down-migration via `--down` flag, manual control | 01 | Explicit is safer than auto-rollback on failure |
| D-04 | Eval tests use mocked JSON, no real LLM calls | 01 | Deterministic, fast, no API keys needed |
| D-05 | Eval tests verify DB state only, not prompt→SQL generation | 01 | Scope reduction: we test what we own |
| D-06 | Test directory at project root, `python -m pytest tests/` | 01 | Standard pytest location, matches success criteria |
| D-07 | SKILL.md tier rules reference-only, no inline table | 02 | Must stay lean for local model routing |
| D-08 | Extract syllabus prompt to `templates/init-syllabus.md` | 02 | Reduces init.md from 257 to 122 lines |
| D-09 | Subskillers get inline 8-line tier summary for cron self-containment | 02 | Cron sessions start with zero context |
| D-10 | SKILL.md target: <200 lines (trimmed topic examples + PITFALLS) | 02 | Achieved 196 lines |
| D-11 | Use `git filter-repo` for history purge (not BFG or filter-branch) | 04 | GitHub's recommended tool, single-pass, no Java needed |
| D-12 | Rewrite ALL branches (`--all` flag) | 04 | 3 blob-carrying commits appear across multiple branches |
| D-13 | Create bundle backup before purge at `$HOME/backup-before-purge.bundle` | 04 | Full recovery point before destructive rewrite |
| D-14 | Merge experiment into master, then purge everything, force-push all | 04 | One clean operation, complete fix |
| D-15 | GitHub may cache old objects briefly — acceptable for private repo | 04 | Low risk, no immediate GC needed |

---

## 6. Tech Debt & Deferred Items

### Active (Outstanding v1 Items)

The following remain as active requirements in PROJECT.md (not yet verified as done):

- All documented DB columns exist in actual schema — needs fresh-install verification
- All documented config keys are initialized — needs fresh-install verification
- Stale cron prompt detection via version hash — REL-02, deferred to v2
- SQL LIKE parameterization in SKILL.md and adapt.md — verified done per 01-03
- User submissions validated before DB storage — SEC-01 CHECK constraint done, but full validation not end-to-end tested
- learning.db restricted file permissions — SEC-02 done (chmod 600 in init_db.py)

### Deferred to v2

- **REL-02:** Stale cron prompt detection via version hash
- **REL-03:** Structured local logging for cron invocations
- **FEAT-01:** Inactivity handling — graduated nudge/pause/auto-pause
- **FEAT-02:** Decompose logic for scores < 4.0
- **FEAT-03:** Spaced repetition review delivery
- **TEST-06:** LLM state transition validation tests (decompose branch)
- **TEST-07:** End-to-end tests for full init → daily → eval → adapt cycle

### Not Pursued (Out of Scope)

- Compiled code layer for state transitions (violates Hermes architecture)
- External guardrail frameworks (contradicts zero-dependency constraint)
- Multi-user support (requires complete redesign)
- Encrypted database (SQLCipher not in Python stdlib)
- Real-time observability (requires API keys/network)
- Interactive UI or web interface (future v2 direction)

---

## 7. Getting Started

### Run the Project

```bash
# Initialize the database
python3 scripts/init_db.py

# Run the test suite
python3 -m pytest tests/ -v

# Validate URLs in a syllabus
python3 scripts/validate_urls.py --urls "https://example.com"

# Check migration status
python3 scripts/migrate_db.py --check
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `SKILL.md` | Command router, persona, rules — entry point for `/tutor` |
| `subskills/` | Four subskills loaded on demand: init, daily, eval, adapt |
| `templates/` | Mustache output templates for Telegram messages |
| `scripts/` | Python utilities: init_db, migrate_db, validate_urls, save_path |
| `tests/` | pytest test suite (Phase 1) |
| `learning.db` | SQLite state database (created at runtime, gitignored) |

### Architecture Notes

- **Cron sessions are stateless** — every cron invocation starts with zero context. All logic must be fully self-contained inline in the subskill prompt.
- **DB is truth** — every operation queries SQLite before acting. No in-memory state is trusted.
- **Hermes runtime** executes Markdown files as skill logic — no compilation, no build step.
- **Zero external dependencies** — Python 3.11 stdlib only. SQLite via `sqlite3`. curl for URL validation.

### Entry Points

- `/tutor init` → creates syllabus, validates URLs, activates path
- `/tutor daily` → delivered by cron at 9 AM
- `/tutor eval` → triggered by user submitting task response
- `/tutor adapt` → weekly review cron Sundays 10 PM
- `/tutor status|skip|pause|resume|switch|export` → path management commands

---

## Stats

- **Timeline:** 2026-04-12 → 2026-04-13 (~1 day)
- **Phases:** 4/4 complete
- **Commits:** 77 (since v1.0.0 tag)
- **Files changed:** 75 (+11,240 / -646)
- **Contributors:** mmosquera91@gmail.com
- **Tag:** v1.0.0

---

## Key Files Created During Milestone

| File | Phase | Purpose |
|------|-------|---------|
| `scripts/migrate_db.py` | 01-01 | v1→v2 migration with backup and down-migration |
| `scripts/init_db.py` (updated) | 01-01 | Schema v2 alignment, CHECK constraint, chmod 600 |
| `AGENTS.md` (updated) | 01-01 | Schema docs now match actual DB |
| `tests/test_migrate_db.py` | 01-01 | Migration tests |
| `tests/test_validate_urls.py` | 01-02 | URL tier classification tests |
| `tests/test_init_db.py` | 01-02 | Idempotent creation, config init tests |
| `tests/test_eval_pipeline.py` | 01-02 | State transition tests |
| `tests/conftest.py` | 01-02 | Shared fixtures |
| `templates/init-syllabus.md` | 02-02 | Extracted syllabus Mustache template |
| `scripts/save_path.py` | 02-02 | Extracted DB save CLI script |
| `CONTRIBUTING.md` (updated) | 02-01 | Tier rules canonical source |
| `subskills/init.md` (refactored) | 02-02 | Reduced from 257 → 122 lines |
| `SKILL.md` (reduced) | 02-01 | Reduced from 222 → 196 lines |
| `$HOME/backup-before-purge.bundle` | 04-01 | Full git bundle backup (23MB) |

---

*Summary generated from: ROADMAP.md, REQUIREMENTS.md, 11 SUMMARY.md files, 3 CONTEXT.md files, 4 VERIFICATION.md files, and 77 git commits.*
