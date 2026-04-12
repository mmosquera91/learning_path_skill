# Feature Research

**Domain:** Prompt-driven AI agent reliability and safety hardening (brownfield)
**Researched:** 2026-04-12
**Confidence:** MEDIUM (based on codebase audit, OWASP LLM Top 10, and industry patterns; web search was rate-limited so some findings rely on training data)

## Feature Landscape

This research focuses on what makes a prompt-driven AI system (specifically a Hermes Agent skill) go from "works on my machine" to production-grade reliability. The Tutor skill's architecture -- LLM executing SQL from Markdown prompts, stateless cron sessions, no compiled code layer -- creates a unique surface area where traditional software safety patterns don't directly apply.

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels broken or unsafe.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Error handling on every state transition | Every write to DB or Telegram delivery can fail; silent failure is the worst outcome | MEDIUM | `daily.md` has zero error handling. `init.md` has basic error handling but `eval.md` is thin. Every step that writes state or delivers output needs a documented failure path. |
| Schema-doc consistency | DB schema must match what prompts expect; mismatched columns cause runtime failures | LOW | Documented columns (`next_review_date`, `response_window_end`, `feedback`) don't exist in `init_db.py`. Fix is a migration + init_db.py update. |
| Input validation and sanitization | User submissions go into DB without length limits or sanitization; extremely long responses bloat DB | LOW | Add CHECK constraint on response length in `daily_tasks` table. Truncate before storage. Validate config values before INSERT. |
| Idempotent operations | Retrying a failed cron run or command should not create duplicate tasks, duplicate cron jobs, or corrupt state | MEDIUM | Cron duplicate prevention exists (checks `awaiting_response`), but init.md's cron job creation can create duplicates if re-run. `/tutor confirm` after crash is not idempotent. |
| Consistent template syntax | Output templates must use a single, consistent placeholder format; mixed Mustache/plain-text breaks rendering | LOW | `eval.md` uses `{{date}}`/`{{#completed}}` Mustache, `adapt.md` uses the same, while `daily.md` uses plain `{variables}`. Pick one. |
| SQL parameterization | String-interpolated LIKE clauses are an injection vector; even in prompt-driven systems the LLM can generate malformed SQL | LOW | Two instances in `SKILL.md` (line 163) and `adapt.md` (line 13). Replace with parameterized queries. The risk is low (LLLM constructs the SQL, not a user) but the fix is trivial. |
| DB file permissions | `learning.db` contains user learning data and should not be world-readable | LOW | `chmod 600` on the DB file. One-line fix in `init_db.py`. |
| Documented state machine | Every valid state and transition must be documented in one place; the LLM uses this as its source of truth | MEDIUM | Module lifecycle (`pending -> in_progress -> completed`) and path lifecycle (`draft -> active -> paused -> completed`) are partially documented across AGENTS.md and SKILL.md but never in a single canonical reference. The decompose transition (< 4.0 score) is documented but not implemented. |
| Automated test suite for scripts | Python scripts (`init_db.py`, `migrate_db.py`, `validate_urls.py`) have zero tests; changes can break URL classification or DB initialization silently | MEDIUM | CONTRIBUTING.md references `test_validate_urls.py` which doesn't exist. Tests should cover: `classify_url()` for each tier, `init_db.py` idempotency, `migrate_db.py` forward migration. Python stdlib `unittest` is sufficient. |
| Config key initialization | All config keys referenced by subskills must be initialized in `init_db.py` so the first read doesn't return NULL | LOW | `last_task_date`, `daily_count`, `weekly_count`, `response_window_end` are referenced but not initialized. The duplicate-task guard (`last_task_date`) silently fails until the first task is created. |

### Differentiators (Competitive Advantage)

Features that elevate the system from "working" to "robust." Not required for basic functionality, but they prevent the slow accumulation of operational failures that make a system unmaintainable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Stale cron prompt detection | Cron jobs contain verbatim copies of subskills; edits to daily.md/adapt.md don't propagate to running crons | MEDIUM | Add a version hash or timestamp comment at the top of each subskill. Cron checks if hash matches the file; on mismatch, log a warning to Telegram. Prevents running old buggy logic after fixes. |
| LLM state transition validation | All state transitions currently depend on the LLM correctly executing SQL; there is no programmatic enforcement of valid transitions | HIGH | The ideal fix is a Python wrapper that validates transitions before committing (e.g., reject `completed -> pending` without explicit decompose). But within Hermes constraints, a practical alternative is: document the state machine formally in one place, add transition-validation queries in each subskill step, and test them. |
| Subskill context budget enforcement | Each subskill must stay within a line/token budget to avoid crowding out content in small LLM context windows | MEDIUM | SKILL.md is 216 lines (budget: 200). init.md is 257 lines. Define explicit line budgets per subskill, document them in CONTRIBUTING.md, and enforce via a lint script. |
| Tier rule deduplication | Tier system rules are duplicated across 4+ files; a rule change requires editing all locations | LOW | Keep canonical rules in `CONTRIBUTING.md` and `validate_urls.py`. Replace inlined copies in SKILL.md and init.md with one-line references. Pure refactoring, no behavior change. |
| Comprehensive error reporting | When errors occur, the user gets actionable information rather than silence or cryptic messages | MEDIUM | `daily.md` currently fails silently on error. The cron should report: what failed, what was attempted, and what the user should do (e.g., "Could not generate task for Module X. Try /tutor skip and I'll retry tomorrow."). |
| DB migration rollback | `migrate_db.py` only migrates forward; a bad migration corrupts the DB with no recovery | MEDIUM | Add down-migration functions to `migrate_db.py`. Before every migration, create a backup copy of the DB. Simple but critical for a system storing user progress. |
| Inactivity handling | Users who stop responding never receive a nudge; the documented graduated system (2-day nudge, 3-day pause offer, 5-day auto-pause) does not exist in code | MEDIUM | Requires adding inactivity check logic to `daily.md` after step 2. Blocked on `last_task_date` config key being initialized. Already documented in AGENTS.md but never implemented. |
| Git history sanitization | `learning.db` was committed in early commits; the binary blob is recoverable from git history | LOW | One-time operation: `git filter-repo --path learning.db --invert-paths`. Verify with `git rev-list --objects --all \| grep learning.db`. Must be done before any public fork or share. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like good hardening but create problems in the prompt-driven Hermes architecture.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Compiled code layer for state transitions | Would make state machine enforcement deterministic rather than LLM-dependent | Violates the core Hermes architecture: all logic lives in Markdown files interpreted by the agent, not compiled code. Moving logic to Python scripts means the LLM can't inspect or adapt the flow. | Instead: validate transitions with explicit SQL checks in the prompt, test edge cases, and document the state machine formally. The LLM is the runtime -- work with that constraint. |
| External guardrail framework (NeMo Guardrails, Guardrails AI) | Would add input/output validation layers as seen in production LLM systems | These frameworks require a code runtime (Python/Node server). The Hermes skill has no persistent runtime -- it's invoked by the agent per-session. Adding a dependency server introduces deployment complexity that contradicts the skill's "single machine, zero external deps" constraint. | Instead: build lightweight validation into the Python scripts (which are already part of the skill) and into the prompt instructions themselves. Input validation in `validate_urls.py`-style scripts is the right pattern. |
| Real-time observability dashboard (LangSmith, Langfuse) | Would provide tracing and metrics for every LLM interaction | These tools require API keys, network access to external services, and a persistent agent runtime. The skill runs on a single machine with no telemetry infrastructure. Adding this would mean the skill fails without network access to the observability service. | Instead: structured logging to a local file. Each cron invocation and user command appends a JSON log line to `~/.hermes/skills/tutor/logs/tutor.log` with timestamp, action, result, and any errors. Grep-friendly and zero-dependency. |
| Multi-user support | Would allow the skill to serve multiple learners | The architecture is fundamentally single-user (one SQLite file, one Telegram delivery target, one `active_path_id` in config). Multi-user would require a users table, session management, per-user config, and auth -- a complete redesign of every SQL query and subskill. | Instead: keep single-user scope. Multi-user is a v2.0 goal that requires a different architecture (PostgreSQL, auth layer, session management). Document this boundary clearly. |
| Dynamic prompt versioning via API | Would allow hot-swapping prompt templates without editing files | Hermes loads skill files from disk on each invocation. There is no "deploy" step -- editing the file IS the deployment. Adding a prompt registry or API layer adds complexity for no benefit when you can just edit the Markdown file. | Instead: use Git for prompt versioning. Each change is a commit. Cron prompt staleness is a real problem, but the fix is staleness detection (hash check), not a deployment pipeline. |
| Encrypted database (SQLCipher) | Would protect learning data at rest | Requires a C extension to SQLite that is not in Python stdlib. Violates the "Python 3.11+ stdlib only" constraint. For a single-user, single-machine deployment where the DB file already has restricted permissions (600), the threat model doesn't justify the dependency. | Instead: file permissions (600) and ensuring learning.db is gitignored and purged from history. If encryption is needed later, it's a v2 concern with a different constraint set. |
| Automated red-team testing for prompt injection | Would test whether user submissions can manipulate the LLM's behavior | The skill has a narrow attack surface: the LLM receives user text only in two contexts (topic input during init, and task submissions during eval). The init input goes into a search query (not directly into SQL -- the LLM constructs SQL from its interpretation). The eval input is scored by the LLM and stored in DB. Prompt injection is theoretically possible but the blast radius is low (the LLM might generate a weird task or a wrong score, but can't execute arbitrary code or access other systems). | Instead: focus on the SQL parameterization fix (prevents the most concrete injection vector) and input length validation (prevents context flooding). Formal prompt injection testing is diminishing returns for this threat model. |

## Feature Dependencies

```
[Config key initialization]
    └──requires──> [Schema-doc consistency]
                       └──enables──> [Inactivity handling]
                                        └──requires──> [last_task_date config key]

[SQL parameterization]
    └──requires──> [Schema-doc consistency]  (must know actual column names)

[Stale cron prompt detection]
    └──requires──> [Subskill context budget enforcement]  (budget must be defined first)

[LLM state transition validation]
    └──requires──> [Documented state machine]  (can't validate what isn't defined)

[Tier rule deduplication]
    └──enables──> [Subskill context budget enforcement]  (removes ~30 lines from init.md)

[DB migration rollback]
    └──requires──> [Schema-doc consistency]  (migrations target documented schema)

[Error handling on every state transition]
    └──requires──> [Schema-doc consistency]  (error messages must reference correct columns)
    └──conflicts──> [Silent cron exits]  (daily.md's "END IMMEDIATELY -- NO OUTPUT" must be preserved for the no-active-path case, but real errors must surface)

[Input validation]
    └──requires──> [Schema-doc consistency]  (CHECK constraints need correct schema)
```

### Dependency Notes

- **Config key initialization requires Schema-doc consistency:** Adding missing config keys to `init_db.py` must happen alongside (or after) the schema migration that adds missing columns. Otherwise the init script and migration are out of sync.
- **Inactivity handling requires last_task_date config key:** The inactivity check computes days-since-last-response by comparing `last_task_date` to today. If this key is not initialized, the check always returns NULL and inactivity logic never triggers.
- **Tier rule deduplication enables context budget enforcement:** Removing the 3x duplicated tier rules from `init.md` (~30 lines) is the easiest win for bringing it under budget. Should be done before defining the formal budget, so the budget reflects the deduplicated state.
- **Error handling conflicts with silent cron exits:** The "no active path" silent exit is correct behavior (no message when there's nothing to do). But "DB connection failed" or "task generation failed" must produce output. The distinction is: *expected empty states* are silent, *unexpected failures* are reported.
- **Documented state machine is a prerequisite for transition validation:** You cannot validate transitions without a canonical definition of valid transitions. This must be a single document (not scattered across AGENTS.md and subskills) that both the LLM and any validation logic reference.

## MVP Definition

### Launch With (Phase 1 -- Foundation)

Minimum viable hardening. Without these, the system will continue to accumulate silent failures.

- [ ] Schema-doc consistency -- Missing columns and config keys cause runtime SQL errors that look like "the skill is broken." Fix migration + init_db.py.
- [ ] Config key initialization -- `last_task_date`, `daily_count`, `weekly_count`, `response_window_end` must exist from DB creation.
- [ ] SQL parameterization -- Replace string-interpolated LIKE clauses in SKILL.md and adapt.md with `?` placeholders.
- [ ] Input validation -- Add CHECK(length) constraints on text columns. Truncate user submissions before storage.
- [ ] DB file permissions -- `chmod 600` in init_db.py after DB creation.
- [ ] Error handling on daily.md -- Add explicit error recovery for task generation failure, DB write failure, and Telegram delivery failure.
- [ ] Consistent template syntax -- Pick plain-text `{variable}` format. Replace Mustache in eval.md and adapt.md.

### Add After Validation (Phase 2 -- Reliability)

Features that prevent operational drift and make the system maintainable.

- [ ] Automated test suite for Python scripts -- Unit tests for `classify_url()`, `init_db.py` idempotency, migration forward path. Use stdlib `unittest`.
- [ ] Documented state machine -- Single canonical reference for all valid states and transitions. Used by all subskills.
- [ ] Tier rule deduplication -- Move canonical rules to CONTRIBUTING.md + validate_urls.py. Reference from subskills.
- [ ] Subskill context budget enforcement -- Define line budgets per subskill. Lint script to check.
- [ ] Stale cron prompt detection -- Version hash in subskills. Cron checks hash, warns on mismatch.
- [ ] DB migration rollback -- Add down-migration functions and pre-migration backup to migrate_db.py.
- [ ] Git history sanitization -- Purge learning.db from all git history.

### Future Consideration (Phase 3 -- Resilience)

Features that elevate the system to hardened production quality.

- [ ] Inactivity handling -- Graduated nudge/pause/auto-pause system. Requires Phase 1 config key fix.
- [ ] LLM state transition validation -- Transition-verification queries before committing state changes.
- [ ] Comprehensive error reporting -- Actionable error messages for every failure mode across all subskills.
- [ ] Structured local logging -- JSON log file for every cron invocation and user command.
- [ ] URL validation test fixtures -- Known-good and known-bad URLs for each tier. Run as regression tests.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Schema-doc consistency | HIGH -- silent failures when columns are missing | LOW -- migration + init_db.py edits | P1 |
| Config key initialization | HIGH -- features silently fail without initialized keys | LOW -- add 4 INSERT statements | P1 |
| Error handling on daily.md | HIGH -- daily task silently fails to deliver | MEDIUM -- add error steps to prompt | P1 |
| SQL parameterization | MEDIUM -- low-risk injection vector | LOW -- rewrite 2 queries | P1 |
| Input validation | MEDIUM -- prevents DB bloat | LOW -- CHECK constraints | P1 |
| DB file permissions | MEDIUM -- basic data protection | LOW -- one chmod call | P1 |
| Consistent template syntax | MEDIUM -- broken output formatting | LOW -- find-and-replace | P1 |
| Automated test suite for scripts | HIGH -- enables safe refactoring | MEDIUM -- write tests for 3 scripts | P2 |
| Documented state machine | HIGH -- prevents invalid transitions | MEDIUM -- create single reference doc | P2 |
| Tier rule deduplication | MEDIUM -- prevents divergence | LOW -- text replacement | P2 |
| Subskill context budget | MEDIUM -- prevents context overflow | LOW -- define budgets + lint | P2 |
| Stale cron prompt detection | MEDIUM -- prevents running old bugs | MEDIUM -- hash + check logic | P2 |
| DB migration rollback | MEDIUM -- recovery from bad migrations | MEDIUM -- add down-migration | P2 |
| Git history sanitization | MEDIUM -- removes leaked data | LOW -- one-time git operation | P2 |
| Inactivity handling | HIGH -- users never get nudged | MEDIUM -- add logic to daily.md | P3 |
| LLM state transition validation | HIGH -- prevents corrupt state | HIGH -- design constraint challenge | P3 |
| Comprehensive error reporting | MEDIUM -- better debugging | MEDIUM -- update all subskills | P3 |
| Structured local logging | LOW -- debugging aid | LOW -- append to file | P3 |
| URL validation test fixtures | MEDIUM -- regression safety | LOW -- create fixture file | P3 |

**Priority key:**
- P1: Must have for reliability (fixes broken or fragile behavior)
- P2: Should have for maintainability (prevents future drift)
- P3: Nice to have for resilience (hardens against edge cases)

## Competitor Feature Analysis

The "competitors" for this research are not other tutor apps, but other approaches to prompt-driven system reliability. The question is: what do mature LLM agent frameworks do that this skill doesn't?

| Feature | LangGraph (State Graph) | NeMo Guardrails | Promptfoo (Testing) | Tutor Skill (Current) |
|---------|------------------------|-----------------|---------------------|----------------------|
| State transition enforcement | Built-in: graph edges define valid transitions | Policy-based: Colang rules define allowed flows | Tests transitions via evals | None: LLM executes SQL directly |
| Input validation | Pydantic schemas on graph nodes | Input validators (regex, JSON schema, classifiers) | Input mutation testing | None for user submissions |
| Output validation | Structured output schemas per node | Output validators (regex, JSON schema, fact-checking) | Output assertion testing | LLM trusted to produce correct JSON |
| Error recovery | Retry edges, fallback nodes, interrupt handling | Rejection + re-prompt on violation | Regression detection on error rate | Partial: init.md has retry for invalid JSON |
| Observability | LangSmith integration (traces, tokens, latency) | Logging + metrics hooks | Eval comparison dashboard | None: no logging of any kind |
| Idempotency | Node-level checkpointing | N/A (guardrails are stateless) | N/A (testing tool) | Partial: cron checks `awaiting_response` |
| Prompt versioning | Git-based (prompts are code) | Git-based (Colang files) | Git-based (prompt configs) | Git-based (Markdown files) but cron copies go stale |
| Testing | Unit test graph nodes with mocks | Test guardrail rules | Eval-driven with assertions | Zero tests |

**Key insight:** The Tutor skill's fundamental constraint is that it has no code runtime -- the LLM IS the runtime. Frameworks like LangGraph solve reliability by adding programmatic enforcement around the LLM. The Tutor skill can't do that. Instead, it must achieve reliability through: (1) rigorous documentation that the LLM can follow, (2) Python scripts for validation and DB operations, and (3) tests for those scripts. The "LLM as runtime" constraint means the margin of safety is inherently lower -- which makes the table-stakes features (error handling, schema consistency, input validation) even more critical.

## Sources

- OWASP LLM Top 10 (2025) -- LLM vulnerability taxonomy: prompt injection, insecure output handling, training data poisoning. [HIGH confidence for general principles]
- Codebase audit files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` [HIGH confidence -- directly analyzed]
- Source code review: `SKILL.md`, `subskills/daily.md`, `subskills/eval.md`, `subskills/init.md`, `subskills/adapt.md` [HIGH confidence -- directly read]
- Python scripts review: `scripts/init_db.py`, `scripts/validate_urls.py`, `scripts/migrate_db.py` [HIGH confidence -- directly read]
- Industry patterns for prompt-driven system reliability [MEDIUM confidence -- based on training data, web search was rate-limited]
- LangGraph, NeMo Guardrails, Promptfoo documentation [LOW confidence -- based on training data, not verified against current docs]

---
*Feature research for: Prompt-driven AI agent reliability hardening*
*Researched: 2026-04-12*
