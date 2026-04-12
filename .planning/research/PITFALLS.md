# Pitfalls Research

**Domain:** LLM prompt-driven state machine (Hermes Agent skill, Markdown + SQLite + cron)
**Researched:** 2026-04-12
**Confidence:** HIGH (derived from codebase analysis of CONCERNS.md, ARCHITECTURE.md, and actual source files)

## Critical Pitfalls

### Pitfall 1: Refactoring a Prompt Breaks a State Transition You Didn't Know Existed

**What goes wrong:**
You edit a subskill Markdown file (e.g., shortening `init.md` from 257 lines to 80 lines by extracting references) and the LLM stops executing a critical SQL step -- like saving the syllabus to the DB or creating cron jobs. The user gets a syllabus but nothing is persisted, and the daily cron never activates.

**Why it happens:**
In a prompt-driven system, the "code" is natural language interpreted by an LLM. There is no compiler, no type checker, no linter. The LLM reads the Markdown and decides what steps to execute. When you refactor for conciseness, you can accidentally remove implicit instructions the LLM was relying on. Unlike traditional code refactoring where the AST preserves semantics, prompt refactoring changes the semantic content the LLM receives.

This is already visible in the codebase: `daily.md` (95 lines) has zero error handling while `init.md` (257 lines) has explicit error handling (lines 254-257). The LLM's behavior differs between these two subskills not because of architecture, but because of what the prompt text contains.

**How to avoid:**
1. Before any subskill edit, capture the LLM's step-by-step execution trace against a fixed test input. This is your "golden run."
2. After the edit, replay the same input and compare the execution trace. The steps must match.
3. When extracting content from a subskill into a reference file, the subskill must still contain an explicit "Step N: Read and follow [reference file]" instruction. Do not just remove text and assume the LLM will figure out it needs to look elsewhere.
4. Keep the numbered step structure intact during refactoring. The LLM follows the step numbers as a program counter. Reordering or collapsing steps changes execution order.

**Warning signs:**
- After editing a subskill, the LLM produces output but skips a DB write step
- Test runs show fewer SQL statements being executed than before the edit
- The cron job produces output but state in the DB doesn't change
- AGENTS.md documentation describes steps that no longer appear in the subskill

**Phase to address:** Phase 1 (Foundation) -- establish golden run traces before any refactoring begins

---

### Pitfall 2: Stale Cron Prompts Run Old Buggy Logic Indefinitely

**What goes wrong:**
You fix a bug in `subskills/daily.md` (e.g., adding error handling for DB write failures). The fix works for interactive sessions. But the daily cron job still contains the old verbatim copy of `daily.md` from when it was created. Users continue receiving the buggy behavior every morning at 9 AM. You think the fix shipped, but it silently didn't.

**Why it happens:**
Cron jobs in Hermes are created with the full text of the subskill inlined as the prompt. The cron system stores a snapshot, not a reference. Editing the source file does not update running cron jobs. There is no automatic sync mechanism. This is a known issue documented in CONCERNS.md line 25-29.

This is the prompt-system equivalent of "deployed binary wasn't actually replaced" -- except it's worse because there's no deployment step at all. The stale version persists until someone manually deletes and recreates the cron job.

**How to avoid:**
1. Add a version identifier (hash or timestamp) as a comment at the top of each cron-consumed subskill: `<!-- version: 2026-04-12-a3f2 -->`
2. Add a staleness check as Step 0 in the cron prompt: "Read the current version of `subskills/daily.md` and compare to the version in this prompt header. If they differ, send a warning to Telegram: 'Cron prompt is stale -- manual refresh required' and exit."
3. Document the cron refresh procedure prominently in CONTRIBUTING.md: after editing `daily.md` or `adapt.md`, you MUST delete and recreate the corresponding cron job.
4. Add a post-edit checklist item: "Did you refresh the cron job?"

**Warning signs:**
- A fix works interactively but not in cron
- Cron output differs from what the source file should produce
- `git log` shows edits to `daily.md` or `adapt.md` but the cron job creation date is older

**Phase to address:** Phase 1 (Foundation) -- implement version detection before any cron-consuming subskill is refactored

---

### Pitfall 3: Schema-Documentation Drift Causes Silent LLM Failures

**What goes wrong:**
The LLM reads `AGENTS.md` which documents columns like `modules.next_review_date`, `daily_tasks.feedback`, and config keys like `last_task_date`. The LLM generates SQL using these columns. SQLite throws "no such column" errors. The LLM interprets this as "the operation failed" and may either silently skip the step or report a generic error to the user. The spaced repetition feature appears to work but never actually stores review dates.

This is already happening. The CONCERNS.md documents 4 missing columns and 4 missing config keys. The LLM has been generating SQL against a phantom schema.

**Why it happens:**
In a traditional application, the ORM or type system catches column mismatches at compile time. In a prompt-driven system, the LLM reads documentation to learn the schema. If documentation is wrong, the LLM generates wrong SQL. The error only surfaces at runtime, and the LLM may handle it gracefully (by reporting an error) or silently (by skipping the step entirely).

The root cause is having two sources of truth: `init_db.py` defines the actual schema, while `AGENTS.md` documents the intended schema. They diverged because no automated check enforces consistency.

**How to avoid:**
1. Make `init_db.py` the single source of truth. Auto-generate schema documentation from the actual `CREATE TABLE` statements.
2. Add a schema validation script that compares `AGENTS.md` documented columns against `init_db.py` actual columns and reports mismatches.
3. As an interim fix: add the missing columns via migration before any refactoring, then update `AGENTS.md` to match. This is a prerequisite -- do not refactor anything that depends on the schema until this is fixed.
4. Never add a column to documentation without simultaneously adding it to `init_db.py` and `migrate_db.py`.

**Warning signs:**
- LLM generates SQL that references columns not in the actual schema
- "No such column" errors appear in cron or agent logs
- Features documented as working (spaced repetition, inactivity) have no observable effect
- AGENTS.md section 4 describes state transitions that reference columns missing from init_db.py

**Phase to address:** Phase 1 (Foundation) -- schema sync is a prerequisite for all subsequent phases

---

### Pitfall 4: Duplicated Logic Drifts Apart During Partial Fixes

**What goes wrong:**
The tier system rules exist in 4 files (SKILL.md, init.md x3, CONTRIBUTING.md, validate_urls.py). You fix a tier rule in `validate_urls.py` (the canonical source) but forget to update `SKILL.md`. The LLM sees different tier rules in the router vs. the validation script. Syllabi pass validation but the LLM's syllabus generation uses the old rules from SKILL.md, producing inconsistent results.

**Why it happens:**
The codebase has no single-source-of-truth enforcement. The LLM reads Markdown files, not Python code. Even if you declare `validate_urls.py` as canonical, the LLM will use whatever rules it sees in the prompt it was given. If the router prompt (SKILL.md) has different rules than the validation script, the LLM follows the router rules during generation and the Python script follows its own rules during validation.

**How to avoid:**
1. Deduplicate FIRST, before any feature work. Replace inline tier rules in SKILL.md and init.md with a single-line reference: "Follow tier rules defined in scripts/validate_urls.py."
2. After deduplication, verify the LLM actually reads and follows the reference file by testing init with a known input and checking tier classification matches validate_urls.py output.
3. Add a CI check: grep for tier rule keywords in SKILL.md and init.md. If found, fail.
4. Never add a platform exception or tier rule change in more than one file. One edit, one file.

**Warning signs:**
- Tier rules in different files have slightly different wording or thresholds
- validate_urls.py rejects URLs that the LLM-generated syllabus includes (or vice versa)
- Adding a new platform requires editing more than 2 files

**Phase to address:** Phase 1 (Foundation) -- deduplication before any feature additions

---

### Pitfall 5: No Tests Means Every Refactoring is a Blind Leap

**What goes wrong:**
You simplify eval.md's state transition logic (combining the score >= 7 and score < 7 branches into a cleaner CASE statement). The LLM now produces slightly different SQL. You test it once manually and it works. Two weeks later, a user scores 3.5 and the LLM executes the wrong branch, advancing instead of repeating. The user skips a critical module.

**Why it happens:**
The codebase has zero automated tests. Every change is validated by manual spot-checking against a single happy path. The eval pipeline has at least 4 distinct branches (advance, repeat, decompose, no-pending-task) but testing only covers the most common one. Edge cases (exactly 7.0, exactly 4.0, NULL scores, concurrent submissions) are untested.

In a traditional codebase, unit tests catch regressions immediately. Here, regressions surface as silent data corruption in the user's learning path -- the worst possible failure mode because the user doesn't know their progress is wrong.

**How to avoid:**
1. Write tests BEFORE refactoring. The test suite is your safety net. Without it, every edit is risk.
2. Priority test targets: DB operations (init_db.py, migrate_db.py), state transitions (eval.md decision branches), URL classification (validate_urls.py). These are the components where bugs cause data corruption.
3. For prompt-testing: create a golden dataset of LLM inputs and expected SQL outputs. Run the LLM against these inputs and verify the generated SQL matches. This is the prompt-system equivalent of snapshot testing.
4. For Python scripts: standard pytest with an in-memory SQLite database (`:memory:`) for DB tests, and mock HTTP responses for URL validation tests.

**Warning signs:**
- Manual testing is the only validation strategy
- "Works on my machine" is the only quality gate
- Changes to eval.md or daily.md require full manual walkthroughs
- No test fixtures for any component

**Phase to address:** Phase 1 (Foundation) -- test suite must exist before Phase 2 refactoring begins

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inlining full subskill into cron prompt | Cron works with zero context, no file loading needed | Stale prompts, 500-line cron payloads, no way to update without recreating jobs | Acceptable only as Hermes constraint. Mitigate with version detection. |
| Running init_db.py on every cron invocation | Defensive against missing DB, no upfront setup required | Wastes time on 5 DDL statements per run (trivial now, adds up) | Acceptable for single-user. Add fast-path (file existence check) if it becomes measurable. |
| LLM executing raw SQL from prompts | No ORM needed, maximum flexibility | No type safety, no query validation, LLM can hallucinate column names | Acceptable for single-user, single-file DB. Dangerous at scale. Mitigate with schema validation. |
| String interpolation in LIKE queries | Simpler prompt text, LLM can construct queries easily | SQL injection risk (low for single-user, but bad pattern) | Never acceptable. Parameterize all queries. |
| Mustache template syntax in eval.md feedback | Looks like a real template system, familiar syntax | Not processed by any engine, LLM must interpret `{{variable}}` notation, ambiguous | Never acceptable. Use plain text placeholders consistent with other templates. |
| Copy-pasting tier rules into multiple files | Each file is self-contained, LLM doesn't need to read external references | Drift between copies, maintenance burden, inconsistency | Never acceptable after Phase 1. Deduplicate to single source. |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Hermes cron system | Editing a subskill file and assuming the cron job picks up changes automatically | Cron stores a verbatim snapshot. After editing daily.md or adapt.md, delete and recreate the cron job. Add version hash detection. |
| Hermes v0.7 slash commands | Using `/tutor submit`, `/tutor confirm`, `/tutor edit` in prompts or templates | Hermes v0.7 rejects unknown slash commands. Use plain text triggers or register as quick_commands in config.yaml. Update templates/syllabus.md lines 30-31. |
| SQLite in WAL mode from cron | Multiple cron jobs or concurrent sessions writing to the DB without transaction handling | Wrap cron DB operations in explicit transactions. Use `BEGIN`/`COMMIT` pairs. The current subskills issue individual SQL statements without transaction boundaries. |
| Telegram delivery | Assuming the LLM's `deliver: telegram` instruction always succeeds | Add explicit error handling: if delivery fails, retry once, then log to DB for manual review. Currently daily.md has no delivery error handling. |
| Python stdlib for URL validation | Assuming curl is available on all systems and subprocess.run won't hang | Add timeout to all subprocess calls (already done at 10s). Consider using urllib.request instead of curl subprocess to eliminate the external dependency. |
| Git history with binary data | Removing learning.db from working tree but not purging git objects | Use `git filter-repo --invert-paths --path learning.db`. Verify with `git rev-list --objects --all \| grep learning.db`. Force-push after cleaning. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous URL validation (one at a time, 10s timeout each) | init takes 400+ seconds for a 40-resource syllabus | Use concurrent.futures.ThreadPoolExecutor, cap at 10 concurrent | At 20+ resources per syllabus (current syllabi have 15-20, so this is near-term) |
| init_db.py DDL on every cron run | 5 CREATE TABLE IF NOT EXISTS + 4 INSERT OR IGNORE per cron invocation | Add fast path: `if os.path.exists(db_path) and schema_version matches: skip` | At 2 cron jobs/day = 18 redundant DDL executions/day. Trivial now, adds monitoring overhead at scale. |
| No DB pruning for daily_tasks and resources | Tables grow unboundedly, queries slow over months | Add weekly pruning step to adapt.md: archive tasks >90 days, remove unused resources | At hundreds of rows (months of multi-path usage). Not immediate, but no ceiling exists. |
| Full subskill inlined in cron prompt (~500 lines) | Every cron invocation sends 500 lines to LLM, consuming context and tokens | Keep subskills under 100 lines. Extract templates and scripts. Reference, don't inline. | Already breaking: init.md at 257 lines exceeds local model context budgets (4K-8K tokens) |
| LLM generates task content every cron run | No caching of generated tasks, each day costs a full LLM invocation | Pre-generate tasks for the upcoming week during the weekly review. Store in DB. | At 1 LLM call/day this is fine. If multi-user or more frequent delivery, cost scales linearly. |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| User data in git history (learning.db committed in 3 early commits) | Anyone with repo access can recover user learning progress, responses, PII via `git show <hash>` | Purge with `git filter-repo --invert-paths --path learning.db`. Verify with `git rev-list --objects --all \| grep learning.db`. Force-push. |
| SQL injection via f-string interpolation in LIKE clauses | LLM could generate malicious SQL if user input contains SQL metacharacters. Low probability for single-user, but bad pattern. | Replace all string-interpolated SQL with parameterized queries using `?` placeholder. For LIKE patterns, escape `%` and `_` in user input. |
| No input validation on user submissions before DB storage | Extremely long responses bloat DB. No schema-level constraint. | Add `CHECK(length(response) <= 10000)` to daily_tasks.response column. Enforce in eval.md step 3. |
| learning.db with default file permissions (644 or worse) | Any process running as the user can read/modify the learning database | Set permissions to 600 in init_db.py: `os.chmod(db_path, 0o600)`. Verify on every cron run. |
| No authentication on DB access | No mechanism to verify only the Hermes agent can read/write the DB | Acceptable for single-user, single-machine. Document as a scaling limitation. For v2, consider SQLite user-auth extension or file-level ACLs. |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent cron failures (daily.md exits with no output when no active path) | User expects a daily task, gets nothing. No way to know if the system is broken or just inactive. | Distinguish "no active path" from "system error." Send a weekly heartbeat even when inactive: "Tutor system operational. No active learning path." |
| `/tutor submit` silently dropped by Hermes v0.7 | User types the documented command, nothing happens. They think the system is broken. | Update all user-facing command references to plain text alternatives. Add a note in the first bot message: "Tip: just type your response, no /submit needed." |
| Template commands reference `/confirm` and `/edit` without prefix | User follows template instructions, commands are rejected | Update templates/syllabus.md to use plain text: "Type 'confirm' to start" not "/tutor confirm" |
| No way to delete a learning path | User starts a bad init, cannot reset without destroying all paths and history | Add `/tutor delete` command that archives (not destroys) the path. Soft-delete: set status to 'archived'. |
| Inactivity system documented but not implemented | User expects nudges after 2 days of inactivity, receives nothing | Either implement the inactivity checks in daily.md (Phase 3+ feature) or remove the documentation claiming it exists (Phase 1 cleanup). |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Schema migration adds columns AND init_db.py matches:** Migration (version 2) adds `next_review_date`, `score`, `response_window_end`, `feedback` columns AND `init_db.py` CREATE TABLE statements are updated for fresh installs. Verify both, not just the migration.
- [ ] **Tier deduplication is complete across ALL locations:** After deduplicating, grep for tier-specific keywords ("TIER 1", "TIER 2", "50%", "playlist") in SKILL.md, init.md, CONTRIBUTING.md. Ensure only CONTRIBUTING.md and validate_urls.py contain the full rules.
- [ ] **Cron job is refreshed after subskill edit:** After editing daily.md or adapt.md, verify the cron job contains the updated text. Do not trust that "it should be fine."
- [ ] **eval.md template syntax matches the evaluation prompt:** The feedback template (lines 73-86) uses `{{date}}`, `{{score}}` etc. Verify the evaluation prompt in step 2 defines these variables. If not, the LLM will output raw template syntax to the user.
- [ ] **init.md is short enough to be cron-inlined:** After refactoring, count lines. If >100 lines, it will not fit comfortably in local model context when inlined into a cron prompt.
- [ ] **Git history is actually purged:** After running filter-repo, verify with `git rev-list --objects --all | grep learning.db`. An empty result means success. A non-empty result means the blob still exists (reflog may need expiring).
- [ ] **Tests actually run and pass:** Having test files is not enough. Run `pytest scripts/test_*.py` and verify green. Tests that import but don't assert are worthless.
- [ ] **Config keys are initialized for first run:** After adding missing config keys to init_db.py, test with a fresh DB (delete learning.db, run init_db.py, query all config keys). NULL values indicate the INSERT OR IGNORE silently failed.
- [ ] **AGENTS.md section 4 state machine matches eval.md branches:** The documented state machine (advance/repeat/decompose) must exactly match the implemented branches in eval.md step 5. If AGENTS.md describes a decompose branch that eval.md doesn't implement, that's a bug.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM skips a DB write step after prompt refactor | LOW | Manually execute the SQL against learning.db. Check the step the LLM skipped in the subskill, construct the SQL, run it via sqlite3 CLI. Verify state is correct. |
| Stale cron prompt running old logic | LOW | Delete the cron job (`hermes cron remove tutor-daily` or equivalent), recreate it with the current subskill content. One-time fix. |
| Schema migration corrupts data | MEDIUM | Restore from backup (you made one before running migrate_db.py, right?). If no backup: the migration is additive (ADD COLUMN), so original data is intact. Drop the added column manually if the migration added wrong types. |
| Git history purge goes wrong | MEDIUM | Re-clone the original repo from remote (if force-push hasn't happened). If already force-pushed: restore from the mirror clone you made before running filter-repo. Always make a mirror clone first. |
| Refactoring breaks eval state transitions | HIGH | Check daily_tasks table for incorrect status values. Manually fix: UPDATE modules SET status='in_progress' WHERE status was incorrectly set to 'completed'. Recalculate score_avg. This is why tests are critical -- recovery requires manual DB surgery. |
| User loses learning progress from DB corruption | HIGH | SQLite WAL mode provides crash recovery. If the DB file is corrupted: `sqlite3 learning.db ".recover" > recovery.sql`, then `sqlite3 learning.db_new < recovery.sql`. This is why file permissions (600) and backups matter. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Prompt refactor breaks state transitions | Phase 1 (Foundation) -- capture golden traces before any edits | Replay golden traces after each edit. Steps must match. |
| Stale cron prompts | Phase 1 (Foundation) -- add version detection to cron subskills | Edit daily.md, run cron, verify staleness warning appears. |
| Schema-documentation drift | Phase 1 (Foundation) -- sync schema via migration + doc update | Run schema validation script. Zero mismatches. |
| Duplicated logic drifts apart | Phase 1 (Foundation) -- deduplicate tier rules | Grep for tier keywords in SKILL.md and init.md. Zero inline rules. |
| No tests = blind refactoring | Phase 1 (Foundation) -- write test suite before Phase 2 | `pytest scripts/test_*.py` passes. Golden traces match. |
| SQL injection in LIKE clauses | Phase 1 (Foundation) -- parameterize all queries | Grep for f-string SQL patterns. Zero matches. |
| User data in git history | Phase 1 (Foundation) -- purge with git filter-repo | `git rev-list --objects --all \| grep learning.db` returns empty. |
| init.md too long for context budget | Phase 2 (Consolidation) -- extract templates, scripts, references | Line count < 100. Verify cron inlined version fits in 4K context. |
| eval.md uses wrong template syntax | Phase 2 (Consolidation) -- replace Mustache with plain text placeholders | Generate evaluation output, verify no raw `{{` syntax in user-facing message. |
| daily.md has no error handling | Phase 2 (Consolidation) -- add error handling for DB, LLM, and Telegram failures | Test with deliberate failures (DB locked, empty response, delivery timeout). |
| Missing config keys on first run | Phase 1 (Foundation) -- add all documented keys to init_db.py defaults | Fresh DB init, query all config keys, verify non-NULL. |
| Spaced repetition untested end-to-end | Phase 3 (Reliability) -- implement and test full review cycle | Complete a module, verify next_review_date is set, wait for review task delivery. |
| Decompose logic not implemented | Phase 3 (Reliability) -- add decompose branch to eval.md | Score below 4.0, verify sub-modules are inserted and module_order shifts. |
| No path deletion command | Phase 3 (Reliability) -- add /tutor delete with soft-delete | Delete a path, verify it's archived not destroyed, other paths intact. |

## Sources

- **Codebase analysis (HIGH confidence):** CONCERNS.md, ARCHITECTURE.md, PROJECT.md, actual source files (daily.md, eval.md, init.md, SKILL.md, init_db.py, validate_urls.py, migrate_db.py)
- **Domain knowledge (MEDIUM confidence):** LLM prompt regression testing patterns, SQLite migration best practices, git filter-repo usage
- **Web search (LOW confidence):** Rate-limited during research session. Findings from training data for SQLite migration patterns and git filter-repo best practices -- verified against official documentation where possible.

---
*Pitfalls research for: Hermes Agent Tutor Skill Hardening*
*Researched: 2026-04-12*
