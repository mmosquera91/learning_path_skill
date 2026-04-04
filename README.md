# Learning Path Generator

A personal AI tutor skill for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Generates structured learning paths, delivers daily tasks via Telegram, evaluates responses with a structured rubric, and adapts to the learner's pace.

## What It Does

1. **Generates a syllabus** from any topic (e.g., "I want to learn Rust") — modules, resources, milestones, estimated duration
2. **Sends a daily task** via Telegram at 9:00 AM using a cron job
3. **Evaluates responses** with a two-axis rubric (conceptual comprehension + application ability, 1-10)
4. **Adapts the plan** — accelerates on high scores, repeats weak areas, decomposes modules on low scores
5. **Weekly review** every Sunday at 10 PM with metrics and recommendations
6. **Spaced repetition** — completed modules get reviewed at increasing intervals
7. **All state in SQLite** — portable, zero-config, easy to back up
8. **Exports to Obsidian** — full learning journey as Markdown

## Architecture

```
~/.hermes/skills/learning-path/
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
| `/confirm` | Activate the pending syllabus |
| `/edit <feedback>` | Regenerate syllabus with modifications |
| `/submit <response>` | Submit your answer for evaluation |
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
# Clone into Hermes skills directory
git clone https://github.com/mmosquera91/learning_path_skill.git ~/.hermes/skills/learning-path

# Initialize the database
python3 ~/.hermes/skills/learning-path/scripts/init_db.py

# Verify
python3 ~/.hermes/skills/learning-path/scripts/migrate_db.py
```

### Cron Jobs (Optional — for automated delivery)

Create the daily task job:

```python
cronjob(
    action="create",
    name="learning-path-daily",
    schedule="0 9 * * *",        # 9 AM daily
    skill="learning-path",
    deliver="telegram",
    prompt="""Eres Hermilio Tutor..."""  # See SKILL.md for full prompt
)
```

Create the weekly review job:

```python
cronjob(
    action="create",
    name="learning-path-weekly",
    schedule="0 22 * * 0",       # Sundays 10 PM
    skill="learning-path",
    deliver="telegram",
    prompt="""Eres Hermilio Tutor..."""  # See SKILL.md for full prompt
)
```

Or via CLI:

```bash
hermes cron create "0 9 * * *" --skill learning-path --deliver telegram
hermes cron create "0 22 * * 0" --skill learning-path --deliver telegram
```

### Obsidian Integration (Optional)

Set the vault path in `~/.hermes/.env`:

```
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

Exports will be saved to `$OBSIDIAN_VAULT_PATH/Learning/`.

## Evaluation Rubric

Every submission is scored on two axes (1-10):

| Axis | 1-3 | 4-5 | 6-7 | 8-9 | 10 |
|------|-----|-----|-----|-----|----|
| **Conceptual Comprehension** | Cannot explain core concept | Partial, significant gaps | Solid, minor gaps | Deep, handles edge cases | Expert, cross-domain |
| **Application Ability** | Cannot apply even with help | Can apply with substantial help | Independent on standard problems | Handles novel problems | Can teach and optimize |

**Decision rules:**
- Average >= 7.0 → Advance to next module
- Average 4.0-6.9 → Repeat with clarification
- Average < 4.0 → Decompose into sub-modules

**Spaced repetition:**
- Score >= 8 → Review in 7 days
- Score 5-7.9 → Review in 3 days
- Score < 5 → Review next session

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

| Decision | Choice | Why |
|----------|--------|-----|
| Persona in SKILL.md, not separate profile | Cron jobs run on default profile, no `--profile` flag available | Keeps everything self-contained |
| Explicit /submit command | Prevents casual messages from being evaluated as submissions | 20h window as fallback for untagged responses |
| Skill split into subskills | Single SKILL.md too large for local models | Router pattern keeps context lean |
| SQLite over JSON files | Concurrent access, querying, atomicity | WAL mode for safety |
| LLM generates JSON for evaluations | Structured output prevents hallucinated scoring | Parseable, storable, comparable |

## Limitations & Known Issues

- LLM may generate unverified URLs in syllabi — HEAD request validation mitigates this
- Evaluation quality depends on the model's instruction-following ability
- No progress sync across devices (single SQLite file)
- `/tutor switch` requires at least 2 paths to exist
- Obsidian export requires `OBSIDIAN_VAULT_PATH` to be set

## License

MIT
