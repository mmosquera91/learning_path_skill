# Tutor Skill Hardening

## What This Is

The Hermes Agent "Tutor" skill — a prompt-driven learning path system that creates personalized syllabi, delivers daily tasks via Telegram, evaluates submissions with a rubric, and adapts over time. Built as a Hermes skill with Markdown subskills, Python utility scripts, and a SQLite state backend.

## Core Value

The Tutor skill reliably delivers a daily learning task, evaluates the user's submission, and progresses through the learning path — every day, without silent failures or broken state.

## Requirements

### Validated

- ✓ Syllabus generation with web research and URL validation — existing
- ✓ Daily task delivery via cron at 9 AM — existing
- ✓ Task evaluation with two-axis rubric scoring — existing
- ✓ Module advancement on score >= 7.0 — existing
- ✓ Module repeat on score < 7.0 — existing
- ✓ Learning path management (init, status, pause, resume, switch, export) — existing
- ✓ Tier-based URL validation with HTTP checking — existing
- ✓ SQLite schema with migration system — existing
- ✓ Weekly adaptation review via cron — existing
- ✓ Obsidian vault export — existing
- ✓ eval.md uses consistent Mustache template syntax — Phase 03 (FIX-01)
- ✓ syllabus.md uses correct command format (/tutor confirm, /tutor edit) — Phase 03 (FIX-02)
- ✓ daily.md has error handling for task generation, DB write, and Telegram delivery failures — Phase 03 (FIX-03)
- ✓ i18n support with locale config key and parameterized error messages — Phase 03 (gap closure)

### Active

- [ ] All documented DB columns exist in actual schema (next_review_date, score, response_window_end, feedback)
- [ ] All documented config keys are initialized (last_task_date, daily_count, weekly_count, response_window_end)
- [ ] Tier system rules defined in one place, referenced elsewhere (not duplicated across 4+ files)
- [ ] SKILL.md stays under 200 lines
- [ ] init.md is slim enough to be inlined into cron without excessive context consumption
- [ ] Stale cron prompts are detectable (version hash or timestamp check)
- [ ] SQL queries use parameterized patterns or safe escaping for LIKE clauses
- [ ] learning.db is purged from git history
- [ ] User submissions are validated (length limits, sanitization) before DB storage
- [ ] learning.db has restricted file permissions (600)
- [ ] Automated tests cover DB operations, state transitions, URL validation, and eval pipeline
- [ ] AGENTS.md documentation matches actual schema and code

### Out of Scope

- Inactivity handling (nudge, pause offer, auto-pause) — feature gap, separate effort
- Decompose logic for scores < 4.0 — feature gap, separate effort
- Spaced repetition review delivery — depends on schema fix but implementation is separate
- Interactive UI or multi-user support — future v2 direction
- Hermes v0.7 slash command workarounds — already resolved by skill rename

## Context

The Tutor skill is a working Hermes Agent skill used for personal learning. It runs on a single machine with SQLite and Telegram delivery. The codebase audit (`.planning/codebase/`) revealed significant tech debt: tier rules duplicated across 4 files, init.md at 257 lines exceeding context budgets, documented DB columns that don't exist in the actual schema, zero automated tests, and security gaps (SQL injection vectors, leaked database in git history, no input validation). The skill works for its core loop but has accumulated drift between documentation and implementation, and lacks the safety net of tests for refactoring.

## Constraints

- **Runtime**: Hermes Agent — all logic must remain in Markdown files interpreted by the agent, not compiled code
- **Cron constraint**: Cron sessions have zero context — all logic must be self-contained when inlined
- **State**: SQLite is the single source of truth — no in-memory state between sessions
- **Language**: Python 3.11+ stdlib only (no external dependencies)
- **Delivery**: Telegram via Hermes deliver channel — no custom API integration
- **Single user**: One user, one machine — no multi-user or cross-device concerns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fix schema via migration, not fresh install | Existing learning progress must be preserved | — Pending |
| Deduplicate tier rules to CONTRIBUTING.md + validate_urls.py | These are the natural homes; subskills and router reference them | — Pending |
| Parameterize SQL instead of removing LIKE queries | LIKE is useful for search; parameterized queries are the safe pattern | — Pending |
| Purge learning.db from git history | Contains user data; removal from working tree wasn't enough | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after Phase 03 completion*
