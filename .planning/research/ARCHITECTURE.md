# Architecture Research

**Domain:** Markdown-driven AI agent skill (Hermes Agent platform)
**Researched:** 2026-04-12
**Confidence:** HIGH -- derived from direct codebase analysis of 12 source files plus documented constraints

## Standard Architecture

### System Overview

The Hermes skill platform has an unusual architecture: all application logic lives in Markdown files interpreted by an LLM agent at runtime. There is no compiled code layer between the Markdown and the database. This creates a fundamentally different set of architectural constraints than traditional applications.

```
┌─────────────────────────────────────────────────────────────────┐
│                     HERMES AGENT RUNTIME                         │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │   SKILL.md       │    │        CRON SESSIONS              │   │
│  │   (Router)       │    │  ┌──────────┐  ┌──────────┐      │   │
│  │   ~215 lines     │    │  │ daily.md │  │ adapt.md │      │   │
│  │                  │    │  │ (inlined)│  │ (inlined)│      │   │
│  │  Persona + Rules │    │  └────┬─────┘  └────┬─────┘      │   │
│  │  Command Table   │    │       │              │            │   │
│  │  Inline SQL      │    │       └──────┬───────┘            │   │
│  │  (simple cmds)   │    │              │                     │   │
│  └────────┬─────────┘    └──────────────┼─────────────────────┘   │
│           │                            │                          │
│           │ (load on demand)            │ (zero context)           │
│           v                            v                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SUBSKILLS LAYER                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │  │ init.md  │  │ daily.md │  │ eval.md  │  │ adapt.md │   │ │
│  │  │ 257 lines│  │  95 lines│  │  90 lines│  │  67 lines│   │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │ │
│  └───────┼──────────────┼──────────────┼──────────────┼────────┘ │
└──────────┼──────────────┼──────────────┼──────────────┼──────────┘
           │              │              │              │
     ┌─────┴─────┐        │              │              │
     │ templates/ │        │              │              │
     │ (format)   │        │              │              │
     └───────────┘        │              │              │
           │              │              │              │
┌──────────┴──────────────┴──────────────┴──────────────┴──────────┐
│                    INFRASTRUCTURE LAYER                           │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ init_db.py    │  │ migrate_db.py │  │ validate_urls.py     │  │
│  │ (idempotent)  │  │ (versioned)   │  │ (tier classifier)    │  │
│  └───────┬───────┘  └───────┬───────┘  └──────────┬───────────┘  │
└──────────┼──────────────────┼──────────────────────┼──────────────┘
           │                  │                      │
┌──────────┴──────────────────┴──────────────────────┴──────────────┐
│                       STATE LAYER (SQLite)                        │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐ │
│  │ config │  │ paths  │  │modules │  │daily_tasks│  │resources │ │
│  │(KV)    │  │        │  │        │  │          │  │          │ │
│  └────────┘  └────────┘  └────────┘  └──────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With | Lines (current) | Lines (target) |
|-----------|----------------|-------------------|-----------------|----------------|
| `SKILL.md` | Command routing, persona, rules, simple inline SQL | Subskills, scripts, SQLite | 215 | <180 |
| `subskills/init.md` | Syllabus generation, URL validation, path activation, cron creation | templates/, scripts/validate_urls.py, scripts/init_db.py, SQLite | 257 | <120 |
| `subskills/daily.md` | Cron-driven task generation and delivery | scripts/init_db.py, SQLite, Telegram | 95 | <100 |
| `subskills/eval.md` | Task evaluation, scoring, state transitions | templates/evaluation.md, SQLite | 90 | <100 |
| `subskills/adapt.md` | Weekly review, adaptation rules, module re-review | templates/weekly-report.md, SQLite | 67 | <80 |
| `templates/*.md` | Output formatting only -- no logic, no SQL | Subskills (read-only) | 32-56 each | same |
| `scripts/init_db.py` | Idempotent DB initialization | SQLite | 103 | 103 |
| `scripts/migrate_db.py` | Schema versioning and migration | SQLite | 113 | 113 |
| `scripts/validate_urls.py` | Tier-based URL classification and HTTP checking | curl (external) | 217 | 217 |

## Recommended Project Structure

The current structure is well-organized in concept (router/subskills/templates/scripts separation is sound). The problems are not structural but **content-based**: duplication across files and excessive line counts in key files. No directory changes are needed. The refactoring target is within the existing file layout.

```
~/.hermes/skills/tutor/
├── SKILL.md                  # Router — persona, rules, dispatch table
│                             #   REMOVE: SOURCE TIER SYSTEM section (lines 42-66)
│                             #   KEEP:   PITFALLS (domain knowledge for LLM)
│
├── subskills/
│   ├── init.md               # DRASTICALLY REDUCE: 257 → ~120 lines
│   │                         #   Extract: syllabus generation prompt → templates/syllabus-gen.md
│   │                         #   Extract: tier rules (x3) → single reference line
│   │                         #   Extract: save-to-DB Python → scripts/save_path.py
│   │
│   ├── daily.md              # ADD: error handling section
│   │                         #   ADD: inactivity check step
│   │                         #   ADD: duplicate guard (last_task_date)
│   │
│   ├── eval.md               # FIX: Mustache → plain text placeholders
│   │                         #   ADD: decompose branch (score < 4.0)
│   │
│   └── adapt.md              # FIX: parameterize LIKE clause
│
├── templates/
│   ├── syllabus.md           # FIX: /confirm → /tutor confirm
│   ├── daily-task.md         # (no changes needed)
│   ├── evaluation.md         # (rubric is solid — keep as-is)
│   ├── weekly-report.md      # FIX: Mustache → plain text placeholders
│   ├── milestone.md          # (no changes needed)
│   └── syllabus-gen.md       # NEW: extracted from init.md Step 3
│                             #   Contains the full syllabus generation prompt
│                             #   Referenced by init.md, not inlined
│
├── scripts/
│   ├── init_db.py            # ADD: missing config keys + columns
│   ├── migrate_db.py         # ADD: migration v2 (missing columns)
│   ├── validate_urls.py      # (logic is correct — keep as-is)
│   └── save_path.py          # NEW: extracted from init.md Step 7
│                             #   Contains the Python save-to-DB script
│                             #   Accepts JSON input, writes to SQLite
│
└── learning.db               # (gitignored, runtime state)
```

### Structure Rationale

- **No new directories.** The four-layer structure (router/subskills/templates/scripts) is correct. The problem is content duplication, not missing directories.
- **One new template file (`templates/syllabus-gen.md`).** The syllabus generation prompt in init.md Step 3 is 44 lines of pure prompting logic. It belongs in templates because it defines *how to generate output*, not *when to run*. init.md should reference it: "Generate the syllabus using the prompt in `templates/syllabus-gen.md`".
- **One new script (`scripts/save_path.py`).** The 29-line Python block in init.md Step 7 should be a standalone script. The LLM already writes temp files for complex Python (per SKILL.md Pitfall), so this formalizes the pattern. Benefits: testable, reusable, reduces init.md by ~30 lines.
- **Templates stay formatting-only.** This is a critical boundary. Templates contain zero SQL, zero decision trees, zero error handling. They define *what the output looks like*. Subskills contain all the logic.

## Architectural Patterns

### Pattern 1: Single-Source-of-Truth References (for Markdown-driven systems)

**What:** When the same domain knowledge (like tier rules) must appear in multiple Markdown files consumed by an LLM, define the authoritative version in one file and use a one-line reference everywhere else.

**Why it matters here:** Tier rules are currently duplicated across 4 files with slight variations each time. The LLM sees slightly different instructions depending on which file it loaded, leading to inconsistent behavior.

**Implementation:**

In `CONTRIBUTING.md` and `scripts/validate_urls.py`: Keep the full tier rules (these are the source of truth for humans and Python execution).

In `SKILL.md`, `subskills/init.md`, and any other LLM-facing file: Replace the full tier rules section with:
```
**URL Tier Rules:** Follow the tier system enforced by `scripts/validate_urls.py`.
Minimum 50% TIER 1 (interactive platforms). No YouTube playlists.
See `CONTRIBUTING.md` for full tier definitions and examples.
```

This is ~3 lines instead of ~15-25 lines, and points to the machine-enforceable source (the Python script).

**Trade-offs:**
- Pro: Changes to tier rules only need to be made in two places (validate_urls.py + CONTRIBUTING.md)
- Pro: The LLM sees the actual enforcement mechanism (the script), not a potentially stale copy
- Con: The LLM must either read the referenced file or trust the summary. For cron sessions (zero context), the summary must be sufficient.
- Con: If the summary becomes too terse, the LLM may not enforce rules correctly.

**Confidence:** HIGH -- this directly addresses the documented duplication problem and follows the DRY principle.

### Pattern 2: Extract-Reference for LLM Prompts

**What:** When a subskill contains a large block of prompt text (like the 44-line syllabus generation prompt in init.md Step 3), extract it into a template file and reference it by name.

**Implementation:**

init.md Step 3 (before):
```
### 3. Generate the syllabus
[44 lines of prompt text defining how to generate the syllabus]
```

init.md Step 3 (after):
```
### 3. Generate the syllabus
Read the generation prompt from `templates/syllabus-gen.md` and execute it,
replacing {topic} and {research_results} with the values from Steps 1-2.
```

templates/syllabus-gen.md contains the full 44-line prompt.

**Trade-offs:**
- Pro: init.md drops from 257 to ~220 lines immediately
- Pro: The prompt is independently editable without touching the subskill logic
- Pro: Template file is reusable (could be referenced by other subskills if needed)
- Con: For cron sessions, this only works if the LLM can read files. Since init.md runs in interactive sessions (not cron), this is safe. The cron-inlined subskills are daily.md and adapt.md, neither of which references this template.
- Con: Adds indirection. The LLM must follow a file reference, which some models handle poorly.

**Confidence:** HIGH -- init.md runs only in interactive sessions where file reads are available.

### Pattern 3: Script Extraction for DB Operations

**What:** When a Markdown subskill contains inline Python code for database operations, extract it into a standalone Python script in `scripts/`. The subskill calls the script with appropriate arguments.

**Implementation:**

init.md Step 7 (before): 29 lines of inline Python that saves syllabus to SQLite.

init.md Step 7 (after):
```bash
python3 ~/.hermes/skills/tutor/scripts/save_path.py /tmp/syllabus.json
```

scripts/save_path.py: Accepts a JSON file path as argument, reads the syllabus, writes to SQLite (same logic as the extracted Python block).

**Trade-offs:**
- Pro: Reduces init.md by ~30 lines
- Pro: The save operation becomes testable (unit test with a temp DB)
- Pro: Follows the existing pattern (init_db.py, validate_urls.py are already scripts)
- Con: The LLM must pass the correct file path. If the temp file is in an unexpected location, the script fails.
- Con: Adds a file to maintain. But it follows the existing convention.

**Confidence:** HIGH -- the codebase already has three scripts, and SKILL.md Pitfall explicitly warns against inline Python in f-strings.

### Pattern 4: Self-Contained Cron Subskills (Context Budget)

**What:** Cron subskills (daily.md, adapt.md) must be fully self-contained because cron sessions start with zero context. Every SQL query, decision branch, and format string must be in the file. The constraint is not architectural but practical: keeping these files under ~100 lines to stay within LLM context budgets.

**Current state:**
- daily.md: 95 lines -- within budget
- adapt.md: 67 lines -- within budget

**Target:** Keep both under 100 lines. This means:
- No new logic that adds significant length
- Extract reusable patterns into scripts (like save_path.py) rather than inlining
- Use concise SQL and terse error handling

**Trade-offs:**
- Pro: Cron prompts consume minimal context, leaving room for the LLM to generate task content
- Pro: Shorter prompts are more reliably followed by smaller models (Ollama)
- Con: Limits what can be done in cron. Complex features (like inactivity escalation) add significant lines.
- Con: Must balance completeness (all SQL inline) with brevity.

**Confidence:** HIGH -- this is a documented platform constraint, not a hypothesis.

### Pattern 5: Defensive State Machine

**What:** Every operation queries SQLite before acting. No in-memory state is trusted between sessions. The LLM is the state machine executor, not the application.

**Why it matters:** The LLM cannot hold state between invocations. Each session (interactive or cron) starts fresh. The only shared state is the SQLite database. This means:

1. Every action must begin with a read (query current state)
2. Every action must end with a write (persist new state)
3. Every action must handle "state is not what I expected" gracefully

**Implementation note:** This pattern is already followed in most places. The gap is in daily.md (missing error handling) and eval.md (missing decompose branch for score < 4.0).

**Confidence:** HIGH -- this is the fundamental architectural pattern of the skill, documented in SKILL.md Rule 1 and AGENTS.md Section 2.

## Data Flow

### Interactive Flow (User Command)

```
User sends message via Telegram
        |
        v
[HERMES AGENT RUNTIME]
        |
        v
[SKILL.md loaded -- router]
        |
        +-- Simple command? (status, skip, pause, resume, switch, export)
        |       |
        |       v
        |   [Inline SQL in SKILL.md] --> [SQLite] --> [Telegram response]
        |
        +-- Complex command? (init, submit, edit, confirm, review)
                |
                v
            [Subskill loaded on demand]
                |
                +-- init.md: Research -> Generate -> Validate -> Save -> Create cron
                |       |
                |       +---> [templates/syllabus-gen.md] (prompt reference)
                |       +---> [scripts/validate_urls.py] (URL check)
                |       +---> [scripts/save_path.py] (DB write)
                |       +---> [templates/syllabus.md] (output format)
                |       +---> [SQLite] (read + write)
                |       +---> [Cron creation] (inlines daily.md + adapt.md)
                |
                +-- eval.md: Retrieve task -> Evaluate -> Score -> State transition
                        |
                        +---> [templates/evaluation.md] (rubric reference)
                        +---> [SQLite] (read + write)
                        +---> [Telegram response]
```

### Cron Flow (Daily Task)

```
[CRON TRIGGER: 0 9 * * *]
        |
        v
[HERMES CRON SESSION -- zero context]
        |
        v
[daily.md inlined verbatim as prompt]
        |
        +-- Step 1: Run init_db.py (ensure DB exists)
        |       |
        |       v
        |   [scripts/init_db.py] --> [SQLite]
        |
        +-- Step 2: Check active_path_id
        |       |
        |       +-- No active path? --> SILENT EXIT (no output, no message)
        |       +-- Path paused?     --> SILENT EXIT
        |
        +-- Step 3: Check for pending task (duplicate guard)
        |       |
        |       +-- Pending exists? --> SKIP (no new task)
        |
        +-- Step 4: Find next module
        |       |
        |       +-- No pending modules? --> Mark path complete, send completion message
        |
        +-- Step 5: Get module resources
        |
        +-- Step 6: LLM generates task content (inline prompt)
        |
        +-- Step 7: Save task to daily_tasks, set pending_task_id
        |       |
        |       v
        |   [SQLite]
        |
        +-- Step 8: Deliver via Telegram (cron's deliver field)
```

### Cron Flow (Weekly Review)

```
[CRON TRIGGER: 0 22 * * 0]
        |
        v
[HERMES CRON SESSION -- zero context]
        |
        v
[adapt.md inlined verbatim as prompt]
        |
        +-- Step 1: Query performance metrics (aggregation SQL)
        |       |
        |       v
        |   [SQLite]
        |
        +-- Step 2: Evaluate adaptation rules
        |
        +-- Step 3: Generate weekly report
        |
        +-- Step 4: Deliver via Telegram
```

### Key Data Flows

1. **Init flow:** User topic -> web research (external) -> LLM generates JSON syllabus -> validate_urls.py checks URLs -> save_path.py writes to SQLite -> cron jobs created with inlined subskills
2. **Daily flow:** Cron trigger -> SQLite read (config + modules + resources) -> LLM generates task -> SQLite write (daily_tasks + config) -> Telegram delivery
3. **Eval flow:** User submission -> SQLite read (pending task) -> LLM evaluates with rubric -> SQLite write (score, feedback, module status, config) -> Telegram feedback
4. **State transitions:** Eval score drives module lifecycle (pending -> in_progress -> completed) and path lifecycle (active -> paused/completed)

## Component Boundaries

### Boundary 1: SKILL.md vs Subskills

**Rule:** SKILL.md contains ONLY command routing and simple inline commands. Any flow requiring more than 10 lines of logic goes into a subskill.

**Current violation:** SKILL.md contains the full SOURCE TIER SYSTEM section (25 lines) which is domain knowledge, not routing logic.

**Fix:** Remove SOURCE TIER SYSTEM. Replace with a one-line reference pointing to `scripts/validate_urls.py`.

**Test:** Count lines of SKILL.md. Should be <180 after removal.

### Boundary 2: Subskills vs Templates

**Rule:** Templates contain ONLY formatting directives. No SQL, no decision trees, no error handling, no script invocations.

**Current violation:** None in structure (all templates are formatting-only). But `templates/syllabus-gen.md` (proposed) blurs this line -- it contains a prompt, not a format. This is intentional: it is a "prompt template" that the LLM fills in, analogous to how `templates/evaluation.md` contains the rubric that constrains LLM output.

**Clarification:** Two types of template content exist:
1. **Output format templates** (syllabus.md, daily-task.md, weekly-report.md, milestone.md) -- define what the user sees
2. **Prompt constraint templates** (evaluation.md, proposed syllabus-gen.md) -- define what the LLM produces

Both are "templates" in the sense that subskills reference them rather than inlining them. Both are formatting/prompting only. Neither contains executable logic.

**Test:** Grep each template for SQL keywords. Should return zero matches (except evaluation.md which contains example JSON schema).

### Boundary 3: Subskills vs Scripts

**Rule:** Python scripts handle ONLY deterministic operations (DB init, schema migration, URL validation, data persistence). The LLM handles ONLY non-deterministic operations (syllabus generation, task creation, evaluation, adaptation).

**Current violation:** None in principle, but init.md contains inline Python for DB save (Step 7) that should be a script.

**Fix:** Extract save_path.py.

**Test:** Grep subskills for `import sqlite3`. Should return zero matches after extraction.

### Boundary 4: Interactive Sessions vs Cron Sessions

**Rule:** Interactive sessions can load files on demand. Cron sessions cannot -- all logic must be inlined in the prompt.

**Implication:**
- init.md and eval.md can reference external files (templates, scripts) because they run in interactive sessions
- daily.md and adapt.md must be fully self-contained because they are inlined into cron prompts
- This means daily.md and adapt.md CANNOT use the "extract-reference" pattern for templates or scripts (except for init_db.py which is a bash command)

**Test:** daily.md and adapt.md should not contain file references like "read templates/X.md". They can contain bash commands like `python3 scripts/init_db.py`.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (1 user, 1 machine) | SQLite WAL mode is sufficient. No scaling needed. |
| Multiple learning paths | Already supported. `paths` table allows multiple rows with `is_active` flag. `/tutor switch` handles path switching. |
| Multi-user (same machine) | Would need a `users` table and user identification in the config. Cron would need to iterate users. Major refactor. |
| Multi-device sync | Requires replacing SQLite with a remote DB or adding a sync layer. Documented as v2.0 goal. |
| Long-running skill (months of data) | `daily_tasks` and `resources` grow unboundedly. Add pruning to weekly cron: archive tasks older than 90 days. |

### Scaling Priorities

1. **First bottleneck:** daily_tasks table growth. After 1 year of daily tasks across multiple paths, could reach thousands of rows. SQLite handles this fine, but query performance degrades on aggregation queries (weekly report). Mitigation: add periodic pruning.
2. **Second bottleneck:** Cron prompt length. If daily.md grows past 100 lines, the LLM context consumed by the prompt leaves less room for task generation. Mitigation: keep cron subskills lean.

## Anti-Patterns

### Anti-Pattern 1: Tier Rules Duplication

**What people do:** Copy-paste the tier system rules into every file that needs them (SKILL.md, init.md x3, CONTRIBUTING.md, validate_urls.py).

**Why it's wrong:** Five copies of the same rules will inevitably diverge. The LLM sees slightly different tier definitions depending on which file it loaded. A rule change requires editing five locations. One will be missed.

**Do this instead:** Define rules in two places: `scripts/validate_urls.py` (machine-enforced) and `CONTRIBUTING.md` (human-readable). Every other file references these with a one-line summary.

### Anti-Pattern 2: Inline Python in Markdown for DB Operations

**What people do:** Write 20+ line Python blocks directly in Markdown files for the LLM to execute.

**Why it's wrong:** Not testable. Not reusable. F-string escaping breaks with complex payloads (documented in SKILL.md Pitfall). The LLM may modify the script when executing it.

**Do this instead:** Extract into `scripts/`. The subskill calls `python3 scripts/save_path.py <args>`. The script is independently testable and version-controlled.

### Anti-Pattern 3: Mustache Syntax in Templates (without Mustache Engine)

**What people do:** Use `{{variable}}` and `{{#section}}...{{/section}}` Mustache syntax in templates, expecting the LLM to interpret them.

**Why it's wrong:** There is no Mustache rendering engine. The LLM must interpret the syntax, which it does inconsistently. Sometimes variables are left unresolved in the output.

**Do this instead:** Use plain text placeholders like `{variable}` or `[variable]` with an explicit instruction: "Replace each {placeholder} with the appropriate value." This is what the LLM actually does well -- fill in blanks, not parse template syntax.

### Anti-Pattern 4: Documented Features That Don't Exist in Code

**What people do:** Describe features (inactivity handling, decompose logic, spaced repetition) in AGENTS.md and README.md without implementing them in the actual subskills.

**Why it's wrong:** Creates false expectations. The LLM reads AGENTS.md and may attempt to execute unimplemented logic, producing errors or partial state. Users expect features that silently do nothing.

**Do this instead:** Either implement the feature or remove it from documentation. During development, mark clearly: "PLANNED: Not yet implemented" in AGENTS.md, and do not mention it in README.md.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Telegram | Hermes `deliver: telegram` field on cron | No custom API integration. Cron and interactive sessions both use Hermes delivery. |
| curl | `subprocess.run(['curl', ...])` in validate_urls.py | Used for HTTP HEAD checks on URLs. Sequential, 10s timeout per URL. |
| Web search | Hermes `delegate_task` with `web_search` | Used in init.md Step 2 for research phase. |
| Obsidian | File write to `$OBSIDIAN_VAULT_PATH/Learning/` | Used by /tutor export. Fallback to `~/Learning/`. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| SKILL.md <-> subskills/ | Hermes `skill_view("tutor")` or file read | Subskills are loaded by the agent on demand from the router dispatch table |
| subskills/ <-> templates/ | LLM reads template file, interpolates values | Templates are referenced by path. The LLM reads them and fills in values. |
| subskills/ <-> scripts/ | `python3 scripts/<name>.py` via terminal/bash | Scripts are invoked as subprocesses. Input via CLI args or stdin. Output via stdout. |
| All layers <-> SQLite | `sqlite3` Python module or inline SQL executed by LLM | DB is the single source of truth. No in-memory state between sessions. |
| init.md <-> cron | Cron creation inlines subskill content verbatim | daily.md and adapt.md are copied into cron prompts at creation time. No auto-sync. |

## Suggested Refactoring Order

The refactoring should proceed in dependency order. Each step should be independently testable before moving to the next.

### Phase 1: Foundation (Safety Net)

**Goal:** Establish correctness baseline before making architectural changes.

1. **Fix schema mismatch (migrate_db.py v2)**
   - Add missing columns: `modules.next_review_date`, `modules.score`, `daily_tasks.response_window_end`, `daily_tasks.feedback`
   - Add missing config keys: `last_task_date`, `daily_count`, `weekly_count`, `response_window_end`
   - Update `init_db.py` for fresh installs
   - **Why first:** Every subsequent change assumes the schema matches documentation. Without this, SQL queries in subskills will fail.
   - **Test:** Run migration on existing DB. Verify all documented columns exist.

2. **Add automated tests for scripts**
   - Test `validate_urls.py` with known URLs (tier classification)
   - Test `init_db.py` idempotency
   - Test `migrate_db.py` forward migration
   - Test `save_path.py` (new script) with temp DB
   - **Why second:** All subsequent refactoring must be validated. Zero tests means zero confidence.
   - **Test:** Run pytest. All pass.

### Phase 2: Deduplication

**Goal:** Eliminate tier rules duplication. This is the highest-value, lowest-risk change.

3. **Remove SOURCE TIER SYSTEM from SKILL.md**
   - Replace 25 lines (42-66) with a 3-line reference
   - **Dependency:** Phase 1 complete (schema tests pass)
   - **Test:** SKILL.md < 180 lines. Tier rules still enforced by validate_urls.py.

4. **Replace tier rules in init.md (3 occurrences) with references**
   - Lines 51-55, 73-77, 100-111 become short references to validate_urls.py
   - **Dependency:** Step 3 (pattern established)
   - **Test:** init.md < 200 lines. `/tutor init` still produces valid syllabi with correct tier balance.

### Phase 3: Extraction

**Goal:** Reduce init.md from 257 lines to ~120 lines.

5. **Extract syllabus generation prompt to templates/syllabus-gen.md**
   - Move init.md Step 3 prompt (44 lines) to new template file
   - init.md Step 3 becomes: "Read templates/syllabus-gen.md and execute with {topic} and {research_results}"
   - **Dependency:** Step 4 (tier deduplication reduces init.md first)
   - **Test:** init.md < 160 lines. Syllabus quality unchanged.

6. **Extract save-to-DB logic to scripts/save_path.py**
   - Move init.md Step 7 Python block (29 lines) to new script
   - Script accepts JSON file path as argument
   - **Dependency:** Step 5 (init.md already shorter, easier to validate)
   - **Test:** save_path.py tested independently. `/tutor init` -> `/tutor confirm` saves correctly.

7. **Final init.md line count check**
   - After all extractions: should be ~120 lines
   - **Test:** init.md < 130 lines.

### Phase 4: Correctness Fixes

**Goal:** Fix bugs and missing features in other subskills.

8. **Fix eval.md: Replace Mustache with plain text placeholders**
   - Lines 73-86: `{{date}}` -> `{date}`, `{{#completed}}` -> conditional instruction
   - **Dependency:** Phase 2 complete (init.md fixed first as highest priority)
   - **Test:** Evaluation output renders without raw template syntax.

9. **Add decompose branch to eval.md**
   - After Step 4, add score < 4.0 branch: insert sub-modules, shift orders
   - **Dependency:** Schema has all needed columns (Phase 1)
   - **Test:** Low-score evaluation produces sub-modules correctly.

10. **Add error handling to daily.md**
    - Wrap task generation, DB write, and Telegram delivery in error handling
    - **Dependency:** Phase 1 (schema correct)
    - **Test:** Simulate failure at each step. Daily cron reports errors instead of silent failure.

11. **Fix template command references**
    - templates/syllabus.md: `/confirm` -> `/tutor confirm`
    - **Dependency:** None (independent fix)
    - **Test:** Syllabus output shows correct commands.

### Phase 5: Security and Cleanup

**Goal:** Address security gaps and documentation drift.

12. **Purge learning.db from git history**
    - Use git-filter-repo to remove the binary blob
    - **Dependency:** Phase 1 (schema migration tested, DB is safe)
    - **Test:** `git rev-list --objects --all | grep learning.db` returns empty.

13. **Fix SQL injection vectors**
    - SKILL.md line 163 and adapt.md line 13: parameterize LIKE clauses
    - **Dependency:** Phase 4 (eval.md and daily.md already fixed)
    - **Test:** Topic with SQL metacharacters does not produce unexpected query results.

14. **Update AGENTS.md to match reality**
    - Remove unimplemented features from "current" sections
    - Mark planned features explicitly
    - **Dependency:** All code fixes complete
    - **Test:** AGENTS.md section 4 matches init_db.py schema exactly.

### Dependency Graph

```
Phase 1 (Foundation)
  1. Schema fix
  2. Script tests
       |
       v
Phase 2 (Deduplication)
  3. Remove tier from SKILL.md
  4. Replace tier in init.md
       |
       v
Phase 3 (Extraction)
  5. Extract syllabus-gen.md
  6. Extract save_path.py
  7. Verify init.md line count
       |
       v
Phase 4 (Correctness)
  8. Fix eval.md template syntax     (can run parallel with 9-11)
  9. Add decompose branch            (depends on Phase 1 schema)
  10. Add daily.md error handling     (depends on Phase 1 schema)
  11. Fix template commands          (independent, any time)
       |
       v
Phase 5 (Security)
  12. Purge git history              (depends on Phase 1 -- DB safe)
  13. Fix SQL injection              (any time after Phase 1)
  14. Update AGENTS.md               (last -- after all code changes)
```

### Build Order Implications

- **Phase 1 is blocking.** Do not touch subskill logic before the schema matches documentation. Every SQL query in the subskills assumes certain columns exist. If they don't, the skill breaks.
- **Phase 2 and Phase 3 are sequential.** Deduplicate first (low risk, high value), then extract (moderate risk, high value). This way, if extraction introduces a bug, the deduplication is already done and init.md is already shorter.
- **Phase 4 items can be partially parallelized.** eval.md fixes, daily.md fixes, and template command fixes are independent of each other.
- **Phase 5 should be last.** Git history rewrite is destructive. Security fixes (SQL injection) are important but don't block other work. AGENTS.md update should reflect the final state of the code.
- **Tests should be written BEFORE modifying code.** Each phase should have tests that pass before the phase starts and still pass after. This is the safety net that makes the refactoring possible.

## How to Test Each Component

| Component | Test Strategy | Test Type |
|-----------|--------------|-----------|
| `scripts/init_db.py` | Create temp DB, run init, verify all tables and config keys exist. Run again, verify idempotency. | Unit test (pytest) |
| `scripts/migrate_db.py` | Create DB at v0, run migration, verify new columns exist. Run again, verify idempotency. | Unit test (pytest) |
| `scripts/validate_urls.py` | Test classify_url() against known URLs per tier. Test YouTube playlist rejection. Test HTTP status check. | Unit test (pytest) |
| `scripts/save_path.py` (new) | Create temp DB, pass test JSON, verify paths/modules/resources tables populated correctly. | Unit test (pytest) |
| `SKILL.md` | Verify line count < 180. Grep for "TIER" -- should appear only in reference line. Grep for SQL -- only in command implementations. | Static analysis |
| `subskills/init.md` | Verify line count < 130. Grep for "TIER" -- should appear only in references. Grep for `import sqlite3` -- zero matches. Manual test: `/tutor init <topic>` produces valid syllabus. | Static + manual |
| `subskills/daily.md` | Verify self-contained (no file references beyond init_db.py). Manual test: cron runs without errors, delivers task. | Manual |
| `subskills/eval.md` | Grep for `{{` -- zero matches. Manual test: `/tutor submit` produces score and feedback without raw template syntax. | Static + manual |
| `templates/*.md` | Grep for SQL keywords (SELECT, INSERT, UPDATE) -- zero matches except in evaluation.md example JSON. | Static analysis |
| Schema alignment | Script: compare AGENTS.md column documentation against `PRAGMA table_info()` output for each table. | Integration test |

## Sources

- All findings derived from direct analysis of the codebase files listed in `.planning/codebase/STRUCTURE.md`
- Architecture patterns inferred from the existing subskill router pattern documented in AGENTS.md Section 2
- Cron constraints documented in AGENTS.md Section 5 and SKILL.md Rule 4
- Tech debt items catalogued in `.planning/codebase/CONCERNS.md`
- Platform constraint: Hermes Agent -- all logic in Markdown, cron sessions have zero context (HIGH confidence -- this is the runtime environment)

---
*Architecture research for: Hermes Agent skill hardening (Tutor)*
*Researched: 2026-04-12*
