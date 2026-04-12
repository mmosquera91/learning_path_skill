# Project Research Summary

**Project:** Tutor Skill Hardening
**Domain:** Prompt-driven AI agent reliability and safety hardening (brownfield)
**Researched:** 2026-04-12
**Confidence:** HIGH

## Executive Summary

The Hermes Tutor skill is a prompt-driven AI learning system where all application logic lives in Markdown files interpreted by an LLM at runtime, backed by a SQLite database and Python utility scripts. The core learning loop (init, daily task delivery, eval, weekly adaptation) works for personal use, but a thorough codebase audit revealed serious accumulated tech debt: 4 missing DB columns, 4 missing config keys, zero automated tests, tier rules duplicated across 4+ files, init.md at 257 lines exceeding LLM context budgets, and security gaps (SQL injection vectors, user data leaked in git history, no input validation). The fundamental constraint is that the LLM IS the runtime -- there is no compiled code layer, so traditional safety patterns (ORMs, type checkers, guardrail frameworks) cannot be applied directly.

The recommended approach is a phased hardening strategy that begins with establishing a correctness baseline (schema migration, config initialization, automated tests) before any refactoring. All four research files converge on the same first priority: fix the schema-documentation mismatch and write tests before touching any subskill logic. Refactoring should then proceed through deduplication (tier rules), extraction (syllabus prompt, save script), correctness fixes (error handling, template syntax, decompose branch), and security cleanup (git history purge, SQL parameterization). The key risk throughout is that prompt refactoring can silently break state transitions -- mitigated by capturing golden execution traces before edits and replaying them after.

## Key Findings

### Recommended Stack

The existing stack is correct and should not change. The project is a brownfield hardening effort, not a greenfield build. The only addition is a test framework -- everything else is already in place.

**Core technologies:**
- Python 3.11+ (stdlib only): All script logic and DB operations -- already in use, no changes needed. Runtime scripts must remain zero-dependency per PROJECT.md.
- SQLite 3.45+ via `sqlite3` stdlib: State backend -- WAL mode and foreign keys already configured. Add missing columns via migration.
- pytest 8.3+: Test framework -- the single most important stack addition. Zero test coverage is the biggest blocker to safe refactoring. Install in venv only (PEP 668 constraint).
- Markdown: Skill logic and subskills -- this is a Hermes platform constraint, not a technology choice.

**One-time tools:**
- `git-filter-repo`: Purge learning.db from 3 early git commits. Install in venv, run once, remove.

### Expected Features

**Must have (table stakes -- P1):**
- Schema-doc consistency -- missing columns cause silent SQL failures across every subskill
- Config key initialization -- 4 documented keys (`last_task_date`, `daily_count`, `weekly_count`, `response_window_end`) silently return NULL
- Error handling on daily.md -- current silent failure means users get no task with no explanation
- SQL parameterization -- 2 f-string LIKE queries are injection vectors (low risk but bad pattern)
- Input validation -- no length limits on user submissions, risks DB bloat
- DB file permissions -- `chmod 600` one-line fix in init_db.py
- Consistent template syntax -- eval.md uses Mustache, daily.md uses plain text; pick one format

**Should have (competitive -- P2):**
- Automated test suite for Python scripts -- enables safe refactoring (pytest with in-memory SQLite)
- Documented state machine -- single canonical reference for module and path lifecycles
- Tier rule deduplication -- 4+ copies of the same rules across files; replace with references
- Subskill context budget enforcement -- SKILL.md at 215 lines (budget: 200), init.md at 257 lines
- Stale cron prompt detection -- version hash prevents running old buggy logic after fixes
- DB migration rollback -- down-migration functions and pre-migration backup
- Git history sanitization -- purge leaked learning.db from git objects

**Defer (v2+ -- P3):**
- Inactivity handling -- graduated nudge/pause/auto-pause system (documented but never implemented)
- LLM state transition validation -- programmatic transition enforcement beyond prompt instructions
- Comprehensive error reporting -- actionable error messages across all subskills
- Structured local logging -- JSON log file for cron invocations and user commands
- Multi-user support -- requires PostgreSQL, auth layer, complete architecture redesign

**Anti-features (do NOT build):**
- Compiled code layer for state transitions -- violates Hermes architecture (all logic in Markdown)
- External guardrail frameworks (NeMo Guardrails, etc.) -- requires persistent runtime the skill doesn't have
- Real-time observability dashboards (LangSmith, etc.) -- requires API keys and network access the skill doesn't have
- Encrypted database (SQLCipher) -- violates stdlib-only constraint; file permissions sufficient for single-user

### Architecture Approach

The system has a four-layer architecture: router (SKILL.md), subskills (init/daily/eval/adapt), templates (output formatting only), and scripts (deterministic Python operations). The existing structure is sound -- no directory changes needed. The problems are content-based: duplication across files and excessive line counts in key files.

**Major components:**
1. **SKILL.md (Router)** -- command routing, persona, rules. Currently 215 lines (target: <180). Remove inlined tier rules.
2. **subskills/init.md** -- syllabus generation, URL validation, path activation. Currently 257 lines (target: <120). Extract syllabus prompt to template, save logic to script.
3. **subskills/daily.md** -- cron-driven task generation and delivery. Currently 95 lines (within budget). Add error handling and inactivity check.
4. **subskills/eval.md** -- task evaluation, scoring, state transitions. Currently 90 lines. Fix Mustache template syntax, add decompose branch.
5. **scripts/** (init_db.py, migrate_db.py, validate_urls.py, save_path.py new) -- deterministic DB operations and validation.

**Key patterns to follow:**
- Single-Source-of-Truth References: define domain knowledge once, reference elsewhere (for tier rules)
- Extract-Reference for LLM Prompts: large prompt blocks go in templates, subskills reference them
- Script Extraction for DB Operations: inline Python blocks become standalone scripts
- Self-Contained Cron Subskills: daily.md and adapt.md must be under 100 lines with zero file references
- Defensive State Machine: every session reads state from DB, acts, writes back, handles mismatches

### Critical Pitfalls

1. **Refactoring a prompt silently breaks state transitions** -- the LLM follows numbered steps in Markdown like a program counter. Removing text during refactoring can cause the LLM to skip DB write steps. Mitigate by capturing golden execution traces before edits and replaying after.

2. **Stale cron prompts run old buggy logic indefinitely** -- Hermes cron stores a verbatim snapshot of subskills at creation time. Editing the source file does NOT update running crons. Mitigate with version hash detection and documented cron refresh procedure.

3. **Schema-documentation drift causes silent LLM failures** -- the LLM reads AGENTS.md to learn the schema, generates SQL against phantom columns that don't exist in init_db.py. Currently happening with 4 missing columns. Fix via migration before any other work.

4. **Duplicated logic drifts apart during partial fixes** -- tier rules in 4 files will inevitably diverge when only some copies are updated. Deduplicate BEFORE any feature work.

5. **No tests means every refactoring is a blind leap** -- zero automated tests, manual spot-checking only. Changes to eval.md state transitions can corrupt user learning progress silently. Write tests BEFORE refactoring.

## Implications for Roadmap

Based on the convergence of all four research files, the roadmap should follow a strict dependency order. The research is remarkably aligned: all files agree that schema fixes and tests must come first, deduplication second, extraction third, and security cleanup last.

### Phase 1: Foundation -- Safety Net
**Rationale:** Every subsequent phase assumes the schema matches documentation. Without this, SQL queries in subskills will fail. Tests are the safety net that makes all later refactoring possible. All four research files flag this as the blocking prerequisite.
**Delivers:** Correct schema, initialized config keys, automated test suite, parameterized SQL, input validation, DB file permissions
**Addresses:** Schema-doc consistency, config key initialization, SQL parameterization, input validation, DB permissions, error handling on daily.md, consistent template syntax (from FEATURES.md P1)
**Avoids:** Schema-documentation drift (Pitfall 3), no-tests blind leap (Pitfall 5), duplicated logic drift (Pitfall 4)
**Stack:** pytest with in-memory SQLite, migrate_db.py v2
**Implements:** Schema migration, init_db.py updates, test fixtures, escape_like() function

### Phase 2: Deduplication and Context Budget
**Rationale:** Once the safety net is in place, deduplicate tier rules (highest-value, lowest-risk change) and reduce SKILL.md and init.md line counts. Tier deduplication removes ~30 lines from init.md, making subsequent extraction easier to validate.
**Delivers:** Deduplicated tier rules, reduced SKILL.md (<180 lines), reduced init.md (<120 lines), new template (syllabus-gen.md), new script (save_path.py), context budget enforcement
**Addresses:** Tier rule deduplication, subskill context budget enforcement, documented state machine (from FEATURES.md P2)
**Avoids:** Duplicated logic drift (Pitfall 4), init.md exceeding context budget
**Stack:** pytest (test extractions), wc -l CI check
**Implements:** Single-source-of-truth references pattern, extract-reference pattern, script extraction pattern

### Phase 3: Correctness and Reliability
**Rationale:** With a clean foundation and deduplicated codebase, fix remaining bugs: eval.md template syntax, daily.md error handling, decompose branch, inactivity handling, stale cron detection. These are the features that make the system robust rather than just working.
**Delivers:** Fixed eval.md output formatting, error handling in daily.md, decompose logic for low scores, stale cron prompt detection, inactivity handling, DB migration rollback, comprehensive error reporting
**Addresses:** Stale cron prompt detection, inactivity handling, LLM state transition validation, comprehensive error reporting (from FEATURES.md P2-P3)
**Avoids:** Stale cron prompts (Pitfall 2), prompt refactor breaks (Pitfall 1)
**Stack:** version hash mechanism, migration rollback in migrate_db.py
**Implements:** Error handling pattern for cron subskills, version detection in cron prompts

### Phase 4: Security and Cleanup
**Rationale:** Security fixes are important but don't block other work. Git history rewrite is destructive and should come last when the codebase is stable. AGENTS.md documentation update should reflect the final state.
**Delivers:** Purged git history, verified SQL parameterization, updated documentation, clean codebase state
**Addresses:** Git history sanitization, SQL parameterization verification (from FEATURES.md P2)
**Avoids:** User data exposure, documentation drift
**Stack:** git-filter-repo (one-time)
**Implements:** Final AGENTS.md alignment with code reality

### Phase Ordering Rationale

- Phase 1 is blocking -- do not touch subskill logic before schema matches documentation and tests exist
- Phase 2 depends on Phase 1 tests to validate that deduplication doesn't break init behavior
- Phase 3 depends on Phase 2 extraction because init.md must be short before adding inactivity logic to daily.md (the overall context budget matters)
- Phase 4 last because git history rewrite is destructive and should reflect the final codebase state
- This ordering maps directly to the PITFALLS.md pitfall-to-phase mapping and ARCHITECTURE.md dependency graph, which are in strong agreement

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (inactivity handling):** The graduated nudge/pause/auto-pause system requires defining timeout thresholds and escalation logic that doesn't exist in any current documentation. Needs design research.
- **Phase 3 (decompose branch):** Score < 4.0 handling requires defining how sub-modules are generated and inserted. The documented behavior exists but the implementation design is unresolved.
- **Phase 3 (stale cron detection):** The version hash mechanism needs to work within the Hermes cron system's constraints. Unclear if cron sessions can read files to compare hashes.

Phases with standard patterns (skip research-phase):
- **Phase 1 (schema migration):** Standard SQLite migration pattern. migrate_db.py already has the framework.
- **Phase 1 (test suite):** Standard pytest with in-memory SQLite. Well-documented pattern.
- **Phase 2 (deduplication):** Text replacement with reference pattern. No ambiguity.
- **Phase 4 (git-filter-repo):** Standard procedure, well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Based on direct codebase analysis, Python docs, and git-filter-repo docs. Stack is mostly "don't change anything, just add pytest." |
| Features | MEDIUM | Based on thorough codebase audit and OWASP LLM Top 10. Some competitor analysis (LangGraph, NeMo) based on training data rather than current docs. Web search was rate-limited. |
| Architecture | HIGH | Based on direct analysis of all 12 source files. Architecture patterns derived from observed structure and documented constraints. Four-layer model is descriptive, not speculative. |
| Pitfalls | HIGH | Based on CONCERNS.md, ARCHITERCTURE.md, and direct source file review. Pitfalls are grounded in observed issues (missing columns, duplicated rules, zero tests) rather than hypothetical risks. |

**Overall confidence:** HIGH

All four research files are derived primarily from direct codebase analysis, giving them high internal consistency. The findings converge strongly on the same priorities (schema first, tests first, deduplicate, extract, fix, secure). The main gap is in competitor analysis (FEATURES.md), which relied on training data for LangGraph/NeMo Guardrails comparison -- but this is non-critical since the Hermes constraint makes those frameworks inapplicable anyway.

### Gaps to Address

- **Inactivity handling design:** The graduated system (2-day nudge, 3-day pause offer, 5-day auto-pause) is documented in AGENTS.md but never designed for implementation. Timeout values and escalation logic need to be defined during Phase 3 planning.
- **Decompose branch implementation design:** When eval score < 4.0, how are sub-modules generated? By the LLM at eval time, or by re-running a modified init flow? This is undefined and needs a design decision.
- **Cron file-reading capability:** Stale prompt detection requires the cron session to read the current version of daily.md/adapt.md from disk. It's unclear whether Hermes cron sessions support file reads. Must validate during Phase 3 planning.
- **Template syntax decision:** Research recommends plain text `{variable}` format over Mustache `{{variable}}`, but this is a recommendation, not a validated choice. Should confirm during Phase 1 planning that the LLM reliably handles plain text placeholders.
- **Context budget numbers:** Research suggests <100 lines for cron subskills and <180 for SKILL.md, but the actual token budget depends on the LLM model in use. The line-count heuristic should be validated against the target model's context window during Phase 2.

## Sources

### Primary (HIGH confidence)
- Codebase audit files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` -- directly analyzed
- Source code review: `SKILL.md`, `subskills/daily.md`, `subskills/eval.md`, `subskills/init.md`, `subskills/adapt.md` -- directly read
- Python scripts review: `scripts/init_db.py`, `scripts/validate_urls.py`, `scripts/migrate_db.py` -- directly read
- PROJECT.md constraints -- internal project document
- Python `sqlite3` module documentation -- parameterized queries and ESCAPE clause
- `git-filter-repo` GitHub repository (newren/git-filter-repo)
- pytest documentation -- fixture patterns for database testing
- OWASP LLM Top 10 (2025) -- LLM vulnerability taxonomy

### Secondary (MEDIUM confidence)
- Industry patterns for prompt-driven system reliability -- based on training data, web search was rate-limited
- LangGraph, NeMo Guardrails, Promptfoo documentation -- based on training data, not verified against current docs

### Tertiary (LOW confidence)
- Competitor feature comparison (LangGraph, NeMo Guardrails, Promptfoo) -- training data estimates of current capabilities
- git-filter-repo version (2.47+) -- training data estimate, verify with pip install output

---
*Research completed: 2026-04-12*
*Ready for roadmap: yes*
