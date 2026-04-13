# Learning Path Generator

A personal AI tutor skill for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Generates structured learning paths, delivers daily tasks via Telegram, evaluates responses with a structured rubric, and adapts to the learner's pace.

## What It Does

1. **Generates a syllabus** from any topic (e.g., "I want to learn Rust") — modules, resources, milestones, estimated duration
2. **Sends a daily task** via Telegram at 9:00 AM using a cron job
3. **Evaluates responses** with a structured rubric (1-10 score with specific feedback)
4. **Adapts the plan** — accelerates on high scores, repeats weak areas, decomposes modules on low scores
5. **Weekly review** every Sunday at 10 PM with metrics and recommendations
6. **Spaced repetition** — completed modules get reviewed at increasing intervals *(implemented but not yet validated end-to-end)*
7. **All state in SQLite** — portable, zero-config, easy to back up
8. **Exports to Obsidian** — full learning journey as Markdown

### Example Session (Real)

This is an actual session — not a polished demo. The evaluator gave a low score because the code had real bugs. That's the point.

```
You: /tutor init Python

Tutor: 📚 Syllabus: Python (12 modules, ~6 weeks)
       1. Variables & Data Types
       2. Control Flow (if/else, loops)
       3. Functions & Scope
       ...
       12. File I/O & Error Handling
       
       36 resources found. 28 verified OK, 8 unverified.
       Reply /tutor confirm to activate or /tutor edit [feedback] to modify.

You: /tutor confirm

Tutor: ✅ Learning path activated: Python
       📚 12 modules loaded
       🎯 First module: Variables & Data Types
       Cron jobs created (daily 9 AM, weekly Sunday 10 PM).

--- First task ---

Tutor: 📚 Daily Task — Variables & Data Types
       
       Declare variables for: your name (string), age (int), height 
       in meters (float), and is_student (bool). Then:
       1. Print a greeting using an f-string
       2. Print your age in months
       3. Print your height in cm
       4. Use type() to verify each variable's type
       
       Reply /tutor submit <your answer> when done.

You: /tutor submit 
     name = "Sarah"
     age = 27
     height = 1.65
     is_student = True
     
     print(f"Hi, I'm {name}")
     print(f"I am {age/12} months old")
     print(f"My height is {1.65 * 100} cm")
     print(type(name), type(age), type(height), type(is_student))

Tutor: 📋 Evaluation — Variables & Data Types
       Score: 4.5/10
       
       ❌ age/12 divides age by 12 (2.25 months?) — you wanted age*12 
          for age in months
       ❌ Hardcoded 1.65 instead of using the height variable
       
       ✅ Correct variable types declared
       ✅ Correct use of f-strings
       
       Decision: REPEAT — Let's reinforce this. A new task will focus 
       on the areas that need work.
       Review in 1 day.

--- Module repeated with targeted task next session ---
```

## Architecture

```
~/.hermes/skills/tutor/
├── SKILL.md                  # Router + persona + command dispatch
├── subskills/
│   ├── init.md               # Syllabus generation, URL validation, confirmation flow
│   ├── daily.md              # Task generation, inactivity handling, spaced repetition
│   ├── eval.md               # Structured evaluation, scoring, adaptation triggers
│   └── adapt.md              # Weekly review, reports, path adjustments
├── templates/
│   ├── syllabus.md           # Syllabus presentation template
│   ├── daily-task.md         # Telegram task format
│   ├── evaluation.md         # Full rubric + JSON output schema
│   ├── weekly-report.md      # Weekly report template
│   └── milestone.md          # Module completion celebration
├── scripts/
│   ├── init_db.py            # SQLite initialization (idempotent)
│   └── migrate_db.py         # Schema migration engine
└── learning.db               # Generated at runtime
```

## Commands

| Command | Description |
|---------|-------------|
| `/tutor init <topic>` | Generate a syllabus for the given topic |
| `/tutor confirm` | Activate the pending syllabus |
| `/tutor edit <feedback>` | Regenerate syllabus with modifications |
| `/tutor submit <response>` | Submit your answer for evaluation |
| `/tutor status` | Show current progress, module, score |
| `/tutor skip` | Skip today's task (no penalty) |
| `/tutor pause` | Pause the active learning path |
| `/tutor resume` | Resume a paused path |
| `/tutor review <module>` | Repeat a completed module |
| `/tutor switch <topic>` | Switch between multiple active paths |
| `/tutor export` | Export full journey to Obsidian |

## Setup

### Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed and configured
- Telegram gateway connected (or adjust cron delivery target)
- Python 3.11+ (for init/migration scripts)

### Installation

```bash
hermes skills install git+https://github.com/mmosquera91/learning_path_skill.git
```

Or manually:
```bash
git clone https://github.com/mmosquera91/learning_path_skill.git ~/.hermes/skills/tutor
```

Then start with:
```
/tutor init <topic>
```

The database initializes automatically on first use.

### Cron Jobs

Cron jobs are created **automatically** when you run `/tutor confirm` after `/tutor init`. You don't need to set them up manually.

If you ever need to recreate them (e.g., after a reset), ask your agent:

> "Create the cron jobs for the tutor skill: daily at 9 AM and weekly review Sundays at 10 PM, deliver to telegram."

The agent will call the `cronjob` tool with the full self-contained prompts from `subskills/daily.md` and `subskills/adapt.md`. Those prompts include all SQL queries and step-by-step logic — no prior session context needed.

> **Why not manual `hermes cron create`?** The prompts are ~500 lines each (all the SQL + decision logic). The cronjob tool handles this correctly when called programmatically, but typing them in a shell would be impractical. The agent does it for you during `/tutor confirm`.

### Obsidian Integration (Optional)

Set the vault path in `~/.hermes/.env`:

```
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

Exports will be saved to `$OBSIDIAN_VAULT_PATH/Learning/`.

## Evaluation Rubric

Every submission is scored on a single 1-10 scale with specific, constructive feedback:

| Score | Meaning |
|-------|---------|
| 1-3 | Cannot apply even with help; significant conceptual gaps |
| 4-5 | Can apply with substantial help; major gaps |
| 6-7 | Independent on standard problems; minor gaps |
| 8-9 | Handles novel problems; deep understanding |
| 10 | Can teach, optimize, and cross-domain |

**Decision rules:**
- Score >= 7.0 → Advance to next module
- Score 4.0-6.9 → Repeat with clarification
- Score < 4.0 → Decompose into sub-modules

**Spaced repetition:**
- Score >= 8 → Review in 7 days
- Score 5.0-7.9 → Review in 3 days
- Score < 5.0 → Review next session

## Inactivity Handling

The daily cron adapts based on days since last response:

| Days Inactive | Action |
|---------------|--------|
| 0-1 | Normal task |
| 2 | Gentle nudge + option to skip |
| 3 | Offer to pause |
| 5+ | Auto-pause + notification |

## SQLite Schema

6 tables: `schema_version`, `config`, `paths`, `modules`, `daily_tasks`, `resources`.

See `scripts/init_db.py` for the complete CREATE TABLE statements.

Migration support via `scripts/migrate_db.py` — add new columns without data loss.

## Design Decisions

These are the non-obvious problems we hit and how we solved them. If you're building on this stack (Hermes + crons + Telegram), these will save you time.

| Decision | Choice | Why |
|----------|--------|-----|
| Persona in SKILL.md, not separate profile | Cron jobs run on default profile — Hermes has no `--profile` flag for cron | Embedding the persona in the skill keeps it self-contained. A separate profile would be cleaner but the cron layer doesn't support it. |
| Explicit /tutor submit command | A casual message like "what is a lifetime in Rust?" would get evaluated as a task submission | 20h response window as fallback (asks for confirmation before evaluating), but /tutor submit is the primary path. Without this, every question becomes an evaluation. |
| Skill split into 4 subskills | A single SKILL.md with all the logic would be 500+ lines | Local models (Ollama) struggle with long prompts. The router pattern keeps context lean — SKILL.md is ~180 lines, subskills are loaded on demand. |
| SQLite over JSON files | Concurrent access, atomic writes, querying | WAL mode handles the write pattern (cron writes, agent reads). JSON files would need manual locking. |
| LLM outputs structured JSON for evaluations | Free-form text evaluation leads to inconsistent scoring | JSON schema forces the model to commit to numbers and specific feedback. Easier to parse, store, and compare. |
| Cron prompts include all SQL inline | Cron sessions start with zero context — no conversation history | Every query, every decision branch is written out in the prompt. This makes them long (~500 lines) but reliable. |

## Limitations & Known Issues

- LLM may generate unverified URLs in syllabi — HEAD request validation mitigates this
- Evaluation quality depends on the model's instruction-following ability. Tested with glm-5.1; local models via Ollama may need simplified prompts or shorter subskills
- **Spaced repetition is implemented but not yet validated end-to-end** — the logic exists in daily.md and eval.md, but needs a full cycle (init → submit → eval → review) to confirm it works correctly
- No progress sync across devices (single SQLite file)
- `/tutor switch` requires at least 2 paths to exist
- Obsidian export requires `OBSIDIAN_VAULT_PATH` to be set in `~/.hermes/.env`
- The `/tutor confirm` step should create cron jobs automatically — currently this requires the agent to have cronjob tool access during the init flow

## Roadmap

**v1.0 — Current**
- Syllabus generation with URL validation
- Daily tasks via cron + Telegram
- Structured evaluation with rubric
- Inactivity handling
- Weekly review

**v1.1 — In progress**
- Spaced repetition validated end-to-end
- Multi-path with /tutor switch
- Adaptation triggers (auto-decompose, auto-accelerate)
- Milestone celebrations

**v2.0 — Planned**
- Configurable delivery time (not hardcoded 9 AM)
- Multi-language support beyond Spanish/English
- Local model (Ollama) optimized prompts
- Progress sync across devices

## License

MIT
