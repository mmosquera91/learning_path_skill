# Codebase Concerns

**Analysis Date:** 2026-04-12

## Tech Debt

### SKILL.md exceeds stated line budget
- Issue: `SKILL.md` is 215 lines, but `AGENTS.md` states the budget is "under 200 lines" (`AGENTS.md:396`). The SOURCE TIER SYSTEM section alone is 25 lines and largely duplicates the tier rules already in `subskills/init.md`.
- Files: `SKILL.md` (lines 42-66), `AGENTS.md` (line 396)
- Impact: Every line in SKILL.md is loaded into context for every command. The router should be lean. Local models (Ollama) with small context windows are especially affected.
- Fix approach: Remove the TIER SYSTEM section from `SKILL.md` entirely -- it already lives in `subskills/init.md` (lines 51-66) and `CONTRIBUTING.md`. Add a one-line reference instead: "See `subskills/init.md` Step 2 for URL tier rules."

### TIER SYSTEM rules duplicated across 4 files
- Issue: The tier reliability system (TIER 1-4, 50% minimum TIER 1 rule, YouTube playlist ban) is copied nearly verbatim in `SKILL.md`, `subskills/init.md` (appears 3 separate times within the single file: lines 51-55, 73-77, 100-111), `CONTRIBUTING.md`, and `scripts/validate_urls.py`.
- Files: `SKILL.md` (lines 42-66), `subskills/init.md` (lines 51-55, 73-77, 100-111), `CONTRIBUTING.md` (lines 5-60), `scripts/validate_urls.py` (lines 16-48)
- Impact: Changing a tier rule (e.g., adding a new platform) requires editing 4+ locations. High risk of divergence. The validate_urls.py patterns are the source of truth, but the skill prompt files are what the LLM sees.
- Fix approach: Keep the canonical rules in `CONTRIBUTING.md` and `scripts/validate_urls.py`. In `SKILL.md` and `subskills/init.md`, replace with a short reference: "Follow the TIER rules in `scripts/validate_urls.py` -- minimum 50% TIER 1, no YouTube playlists."

### Inactivity logic described in docs but absent from daily.md
- Issue: `AGENTS.md` (lines 146-152) and `README.md` (lines 189-196) describe a graduated inactivity system (2 days nudge, 3 days offer pause, 5 days auto-pause). However, `subskills/daily.md` (95 lines) contains NO inactivity check at all -- it only checks for active path, pending task, and next module.
- Files: `subskills/daily.md`, `AGENTS.md` (lines 146-152), `README.md` (lines 189-196)
- Impact: The inactivity handling documented as a core feature does not exist in the actual cron subskill. Users who stop responding will never receive a nudge, pause offer, or auto-pause.
- Fix approach: Add an inactivity check step to `subskills/daily.md` after step 2 (check active path). Query `last_response_date`, compute days inactive, and implement the escalation logic described in AGENTS.md.

### Cron prompts are stale after any subskill edit
- Issue: Cron jobs contain a verbatim copy of `daily.md` or `adapt.md` in their prompt field at creation time. Editing either subskill file does NOT update running cron jobs. There is no mechanism to detect or auto-sync stale prompts.
- Files: `subskills/daily.md`, `subskills/adapt.md`, `AGENTS.md` (lines 268-278)
- Impact: Bug fixes or feature additions to daily/weekly flows require manually deleting and recreating cron jobs. If a developer forgets this step, users run old buggy logic indefinitely.
- Fix approach: Add a version hash or timestamp comment at the top of each subskill. Include a check in the daily cron: compare the hash in the prompt against the file. If mismatched, log a warning in the Telegram message. Document this in `CONTRIBUTING.md`.

### init.md is excessively long for a subskill
- Issue: `subskills/init.md` is 257 lines -- longer than SKILL.md itself (215 lines). It includes the full TIER SYSTEM rules 3 times, full syllabus generation prompt, full validation instructions, and inline Python code. This defeats the purpose of the subskill router pattern (designed to keep context lean).
- Files: `subskills/init.md` (257 lines)
- Impact: Loading init.md consumes significant context. For local models with 4K-8K context, this may crowd out the actual syllabus content being generated.
- Fix approach: Extract the tier rules into a reference file. Move the syllabus generation prompt into a template. Move the Python save script into `scripts/save_path.py`. The subskill should reference these, not inline them.

## Known Bugs

### `/tutor submit` and `/tutor confirm` are rejected by Hermes v0.7
- Issue: Hermes v0.7 rejects unknown slash commands before they reach the LLM. Only `/tutor` auto-registers from the skill name. Commands like `/tutor submit`, `/tutor confirm`, `/tutor edit` are silently dropped.
- Files: `SKILL.md` (line 40)
- Trigger: Any user sending `/tutor submit`, `/tutor confirm`, or `/tutor edit` on Hermes v0.7+
- Workaround: Users must send plain text without the slash prefix. The 20h window confirmation logic handles this for submissions. For confirm/edit, there is no workaround -- the user must type the command as plain text ("confirm" instead of "/tutor confirm").
- Fix approach: Register sub-commands as `quick_commands` in `~/.hermes/config.yaml`. The root cause is documented at `gateway/run.py:2177` in the Hermes agent repo.

### Template command references use old format
- Issue: `templates/syllabus.md` (lines 30-31) references `/confirm` and `/edit` without the `/tutor` prefix. These are inconsistent with the renamed command format (`/tutor confirm`, `/tutor edit`) and will not work on Hermes v0.7+ regardless.
- Files: `templates/syllabus.md` (lines 30-31)
- Impact: Users following template instructions will send commands that get rejected.
- Fix approach: Update to `/tutor confirm` and `/tutor edit`, or better yet, to plain text alternatives given the Hermes v0.7 issue.

### eval.md uses incorrect template syntax
- Issue: `subskills/eval.md` (lines 73-86) uses Mustache-style template variables (`{{date}}`, `{{#completed}}`) that are not actually processed by any templating engine. The LLM is expected to interpret these, but they are not defined in the evaluation prompt.
- Files: `subskills/eval.md` (lines 73-86)
- Impact: The feedback format template is ambiguous. The LLM may output raw template syntax instead of resolved values.
- Fix approach: Replace Mustache syntax with plain text placeholders like `{date}` and `{score}` consistent with other templates in `templates/`.

## Security Considerations

### SQL injection via string interpolation in LIKE clauses
- Issue: Two SQL queries use Python f-string or string interpolation with user input in LIKE clauses:
  - `SKILL.md` line 163: `WHERE topic LIKE '%{topic}%'`
  - `subskills/adapt.md` line 13: `AND title LIKE '%{module}%'`
- Files: `SKILL.md` (line 163), `subskills/adapt.md` (line 13)
- Risk: A topic or module name containing SQL metacharacters (`%`, `_`, `'`) could manipulate query behavior. For example, topic `%` would match all paths.
- Current mitigation: The LLM constructs the SQL and the values come from user messages filtered through the LLM. Direct SQL injection is unlikely but not impossible.
- Recommendations: Use parameterized queries with SQLite's `?` placeholder. For LIKE patterns, escape user input before interpolation. Since these are in markdown files consumed by an LLM (not executed directly), the practical risk is that the LLM generates a malformed query, not that a user exploits it.

### User data leaked in git history
- Issue: `learning.db` was committed to the repository in the initial commit (3078283b) and two subsequent commits before being removed (dd3918fb). The binary blob (32KB) remains in git history. The git object `3478380115c525f436c9451dfdce3ba746478b6e` still exists.
- Files: Git history, `learning.db` (object `3478380115c525f436c9451dfdce3ba746478b6e`)
- Risk: The DB may contain user learning progress, task responses, and personally identifiable information. Anyone with repo access can recover it with `git show <hash>`.
- Current mitigation: The file was removed in a dedicated commit (dd3918fb).
- Recommendations: Run `git filter-branch` or `git filter-repo` to purge `learning.db` from all history. Force-push the cleaned history. Verify with `git rev-list --objects --all | grep learning.db`.

### No input validation on user submissions before DB storage
- Issue: The eval flow saves user responses directly to `daily_tasks.response` without any sanitization or length limits.
- Files: `subskills/eval.md` (lines 39-46)
- Risk: Extremely long responses could bloat the DB. No schema-level constraint on response length.
- Recommendations: Add a `CHECK(length(response) <= 10000)` constraint to the `daily_tasks.response` column, or enforce truncation in the Python save script.

### No authentication on DB access
- Issue: `learning.db` is a plain SQLite file at `~/.hermes/skills/tutor/learning.db` with no access controls.
- Files: `scripts/init_db.py`, `scripts/migrate_db.py`
- Risk: Any process running as the user can read/modify the database. No encryption at rest.
- Recommendations: Set file permissions to `600`. For multi-user systems, this is a bigger concern.

## Performance Bottlenecks

### URL validation is synchronous and sequential
- Issue: `scripts/validate_urls.py` validates URLs one at a time using `subprocess.run(['curl', ...])` with a 10-second timeout per URL. A syllabus with 40 resources takes 400+ seconds in the worst case.
- Files: `scripts/validate_urls.py` (lines 73-89)
- Cause: Each `check_http_status` call blocks on `curl` with no parallelism.
- Improvement path: Use `concurrent.futures.ThreadPoolExecutor` or `asyncio` with `aiohttp` to validate URLs in parallel. Cap concurrency at 10 to avoid rate limiting.

### init_db.py runs on every cron invocation
- Issue: Both `subskills/daily.md` (step 1) and `subskills/init.md` (step 0) run `init_db.py` at the start. This script opens a SQLite connection, runs 5 CREATE TABLE IF NOT EXISTS statements, inserts 4 defaults, and closes -- on every single cron run.
- Files: `subskills/daily.md` (lines 8-11), `subskills/init.md` (lines 8-12), `scripts/init_db.py`
- Cause: Defensive design to handle DB-not-found edge case in cron.
- Improvement path: Add a fast path: check if the DB file exists before connecting. `os.path.exists(db_path)` is an order of magnitude faster than opening SQLite and running DDL. Alternatively, check `schema_version` table first and exit immediately if it matches.

### Cron prompt is ~500 lines of inline text
- Issue: Cron prompts include the full verbatim content of `daily.md` or `adapt.md`. At ~500 lines, this is sent to the LLM as input on every cron invocation.
- Files: `AGENTS.md` (lines 29, 164-165)
- Cause: Cron sessions have zero context. All logic must be self-contained.
- Improvement path: This is a fundamental constraint of the Hermes cron system. Not fixable without changes to Hermes itself. Mitigation: keep subskills as short as possible (see "init.md is excessively long" above).

## Fragile Areas

### LLM-dependent state transitions
- Issue: All state transitions (module completion, path activation, score application, decompose logic) depend on the LLM correctly executing SQL statements from markdown prompts. The LLM must:
  1. Parse the correct SQL from the markdown
  2. Execute it via `execute_code` or `terminal`
  3. Handle errors correctly
  4. Not hallucinate column names or table structures
- Files: `subskills/eval.md`, `subskills/daily.md`, `subskills/init.md`, `SKILL.md`
- Why fragile: LLMs can misquote SQL, skip steps, or hallucinate extra operations. There is no application-level enforcement of state machine rules -- it is entirely prompt-driven.
- Safe modification: When changing state transitions, update both the SQL in the subskill AND the state machine documentation in `AGENTS.md` section 4. Test manually.
- Test coverage: Zero. There are no automated tests for any state transition.

### Schema mismatch between documentation and init_db.py
- Issue: `AGENTS.md` documents several columns that do not exist in the actual `CREATE TABLE` statements in `init_db.py`:

  | Documented Column | In AGENTS.md | In init_db.py |
  |---|---|---|
  | `modules.next_review_date` | Line 90 | Missing |
  | `modules.score` | Line 90 | Missing (only `score_avg`) |
  | `daily_tasks.response_window_end` | Line 91 | Missing |
  | `daily_tasks.feedback` | Line 91 | Missing |

  Additionally, `AGENTS.md` documents config keys `last_task_date`, `daily_count`, `weekly_count` (lines 104, 106, 107) that are NOT in the `init_db.py` defaults list (lines 88-93).

- Files: `AGENTS.md` (lines 90-107), `scripts/init_db.py` (lines 43-85, 88-93)
- Why fragile: The LLM will try to use these columns in SQL queries, which will fail with "no such column" errors. The skill will appear broken.
- Fix approach: Add the missing columns via a migration in `migrate_db.py` (version 2). Add the missing config defaults to `init_db.py`. Then update `init_db.py` SCHEMA to match for fresh installs.

### Decompose logic has no implementation
- Issue: `templates/evaluation.md` (line 29) and `AGENTS.md` (line 113, 202, 339) describe a "DECOMPOSE" decision for scores < 4.0. This should insert 2-3 sub-modules, shift module_order, and reset the current module. However, `subskills/eval.md` (90 lines) only handles score >= 7 (advance) and score < 7 (repeat). The decompose branch is not implemented.
- Files: `subskills/eval.md` (lines 62-70), `AGENTS.md` (lines 202, 339)
- Impact: A user scoring below 4.0 will get the "repeat" treatment instead of the intended decompose treatment. Weak modules are never broken into smaller pieces.
- Fix approach: Add a decompose branch to `subskills/eval.md` after step 4. Query the current module's module_order. Insert 2-3 new modules at module_order+1, +2, +3. Increment module_order for all subsequent modules. Set current module status to 'pending'.

### Spaced repetition is untested end-to-end
- Issue: The spaced repetition feature (setting `next_review_date` on module completion, daily cron picking up review tasks) is documented but has never been tested through a full cycle. Additionally, the `next_review_date` column does not exist in `init_db.py`.
- Files: `subskills/daily.md`, `subskills/eval.md`, `scripts/init_db.py`, `AGENTS.md` (line 294)
- Impact: Users may never receive review tasks even after completing modules. The feature appears to work but silently does nothing because the column does not exist.
- Fix approach: This is blocked on the schema mismatch fix above. Once `next_review_date` is added to the modules table, implement the review check in `daily.md` step 5 (currently described in AGENTS.md but not in the actual subskill).

## Scaling Limits

### Single SQLite file = single machine
- Issue: `learning.db` is a local file with no replication or sync. Progress is tied to one machine.
- Files: `AGENTS.md` (line 304), `README.md` (line 224)
- Current capacity: One user, one machine.
- Limit: Cannot be used across devices or by multiple users.
- Scaling path: Documented as a v2.0 goal. Could use git-based sync, a remote DB (PostgreSQL), or a file sync service (Syncthing).

### No database size limits or pruning
- Issue: `daily_tasks` and `resources` tables grow unboundedly. Old completed tasks and unused resources are never pruned.
- Files: `scripts/init_db.py` (lines 73-85)
- Current capacity: SQLite handles up to ~281 TB. Practical limit for this use case: thousands of tasks before query performance degrades.
- Limit: For a single learning path of 15 modules with ~3 tasks each, this is ~45 rows. For multi-path users over months, could reach hundreds of rows. Not a near-term concern.
- Scaling path: Add a pruning step to the weekly cron: archive tasks older than 90 days to a separate table or export and delete.

### Cron jobs are single-instance, single-schedule
- Issue: The daily cron runs at 9 AM and weekly at Sunday 10 PM. These are hardcoded. Multiple users on the same machine share the same schedule.
- Files: `AGENTS.md` (lines 143, 155)
- Current capacity: One schedule, one delivery target (Telegram).
- Limit: Cannot support user-configurable times, timezones, or multiple delivery channels.
- Scaling path: Store delivery preferences in the `config` table. Pass them to the cron prompt as parameters.

## Dependencies at Risk

### Hard dependency on Hermes Agent cron behavior
- Issue: The entire daily workflow depends on Hermes cron jobs executing self-contained prompts with zero context. Any change to Hermes cron behavior (e.g., adding context persistence, changing prompt format, altering delivery) could break the skill.
- Files: `AGENTS.md` (lines 128-165)
- Risk: The skill is tightly coupled to a specific Hermes version's cron implementation. The v0.7 slash command change already broke `/tutor submit`.
- Impact: Cron job creation, delivery, and execution could fail silently.
- Migration plan: Abstract the cron-specific logic into a wrapper. Add version detection in cron prompts. Document the minimum Hermes version in `SKILL.md`.

### `validate_urls.py` uses regex patterns that will go stale
- Issue: URL patterns for TIER 1-2 sources (`scripts/validate_urls.py` lines 16-48) are hardcoded regex. Platform URL structures change frequently (e.g., Coursera restructured URLs in 2025).
- Files: `scripts/validate_urls.py` (lines 16-48)
- Risk: Patterns will silently stop matching valid URLs, causing them to be classified as "Unknown/untrusted domain."
- Impact: Syllabi will fail validation for valid resources. LLM will be forced to regenerate, adding latency and potentially degrading quality.
- Migration plan: No automated fix. Add a periodic check: run the validator against known-good URLs for each platform. Document the test URLs in `scripts/test_tier_patterns.py`.

### No pinned Python version
- Issue: `scripts/init_db.py`, `scripts/migrate_db.py`, and `scripts/validate_urls.py` use only stdlib (`sqlite3`, `json`, `subprocess`, `argparse`), but `README.md` (line 129) requires Python 3.11+. No `.python-version` or `pyproject.toml` enforces this.
- Files: `README.md` (line 129), `scripts/init_db.py`, `scripts/migrate_db.py`, `scripts/validate_urls.py`
- Risk: Running on Python 3.10 or earlier could hit `sqlite3` behavioral differences.
- Impact: Low -- all scripts use basic stdlib features available since Python 3.7+.
- Migration plan: Add a `requires-python = ">=3.11"` to a `pyproject.toml` or a version check at the top of each script.

## Missing Critical Features

### No automated testing
- Issue: There are zero test files. `CONTRIBUTING.md` references `python3 -m pytest scripts/test_validate_urls.py -v` but no such file exists. All validation is manual via the checklist in `AGENTS.md` section 9.
- Files: Missing: `scripts/test_validate_urls.py`, any `tests/` directory
- Blocks: Cannot safely refactor SQL, state transitions, or URL validation. Every change requires full manual testing of the init-eval-daily cycle.
- Priority: High

### No error handling in daily.md
- Issue: `subskills/daily.md` has no error handling section. If the LLM fails to generate a task, the DB update fails, or Telegram delivery fails, there is no documented recovery path. Compare with `subskills/init.md` (lines 254-257) which has explicit error handling.
- Files: `subskills/daily.md` (95 lines, no error handling)
- Blocks: Silent failures in the daily cron. User expects a task at 9 AM but receives nothing, with no way to diagnose why.
- Priority: Medium

### No way to delete a learning path
- Issue: There is no `/tutor delete` or `/tutor reset` command. The only way to start over is to manually delete `learning.db` and re-run `init_db.py`, which destroys ALL paths and progress.
- Files: `SKILL.md` (router table, lines 67-84)
- Blocks: Users cannot correct a bad init without losing all history. Multi-path users lose all paths to reset one.
- Priority: Low

### Missing config keys in init_db.py
- Issue: `AGENTS.md` documents these config keys that are not initialized in `scripts/init_db.py`:
  - `last_task_date` (AGENTS.md line 104)
  - `daily_count` (AGENTS.md line 106)
  - `weekly_count` (AGENTS.md line 107)
  - `response_window_end` (AGENTS.md line 103)

  Only `active_path_id`, `pending_task_id`, `last_response_date`, and `streak_count` are initialized (lines 88-93).
- Files: `scripts/init_db.py` (lines 88-93), `AGENTS.md` (lines 103-107)
- Impact: The LLM will try to SELECT these keys and get NULL/empty results. The first INSERT/UPDATE will set them, but the initial read-before-write pattern could cause unexpected behavior.
- Priority: High -- this causes the duplicate task guard (`last_task_date`) to not work until the first task is sent.

## Test Coverage Gaps

### Zero automated tests for any component
- What's not tested: Everything. No unit tests for `validate_urls.py`, no integration tests for DB operations, no end-to-end tests for any flow.
- Files: All `.py` files in `scripts/`, all `.md` files in `subskills/`
- Risk: Any change can break the skill silently. The evaluation pipeline (LLM JSON parsing, score calculation, state transitions) is especially fragile and untested.
- Priority: High

### URL validation has no test fixtures
- What's not tested: The `classify_url()` function in `scripts/validate_urls.py` has no test cases. The CONTRIBUTING.md references `scripts/test_validate_urls.py` which does not exist.
- Files: `scripts/validate_urls.py` (lines 50-71), missing `scripts/test_validate_urls.py`
- Risk: Regex changes can silently break URL classification. A pattern change could cause all YouTube URLs to be classified as invalid, or TIER 1 patterns to stop matching.
- Priority: High

### Migration system has no rollback
- What's not tested: `scripts/migrate_db.py` only migrates forward. There is no down-migration. If a migration introduces a bug (e.g., wrong column type), the only recovery is restoring from backup.
- Files: `scripts/migrate_db.py` (112 lines)
- Risk: A bad migration could corrupt the database with no recovery path.
- Priority: Medium

---

*Concerns audit: 2026-04-12*
