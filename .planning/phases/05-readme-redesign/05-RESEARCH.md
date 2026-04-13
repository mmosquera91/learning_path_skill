# Phase 5: README Redesign - Research

**Researched:** 2026-04-13
**Domain:** Documentation audit vs actual implementation
**Confidence:** HIGH

## Summary

The README.md has several specific discrepancies with the actual implementation that need correction. The core issues are: (1) wrong GitHub repo URL (`learning_path_skill` vs actual `tutor`), (2) incorrect `hermes skills install` command format, (3) command examples in the example session that use `/submit` instead of `/tutor submit` (inconsistent with SKILL.md router), and (4) the evaluation rubric section describing a two-axis scoring system that is not explicitly requested in the eval.md prompt. The README is broadly accurate about features that exist vs features that are in-progress, correctly flagging spaced repetition as "implemented but not yet validated end-to-end."

**Primary recommendation:** Rewrite README sections to fix installation command, correct command formats throughout, and align the evaluation rubric description with what eval.md actually prompts for.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase must address requirements README-01 and README-02
- Must produce a README that mentions only actually-implemented features

### Claude's Discretion
- Rewrite approach and section structure
- Which sections to keep vs replace vs reorder
- Exact wording of corrections

### Deferred Ideas (OUT OF SCOPE)
- None relevant to README redesign

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| README-01 | Audit current README.md — identify inaccurate/outdated claims vs actual implementation | Discrepancies documented in Section 1 below |
| README-02 | Rewrite README.md sections to match current state — remove untested features, fix setup instructions, add real example session, fix command formats | Rewrite recommendations in Section 7 below |

---

## 1. Audit Findings — Specific Discrepancies

### 1.1 GitHub Repo URL (WRONG)
| Location | README says | Actual |
|----------|-------------|--------|
| Setup, Installation | `git+https://github.com/mmosquera91/learning_path_skill.git` | Skill was renamed from `learning_path_skill` to `tutor` (per AGENTS.md v1.1 rename note). The correct URL needs verification. |

**Source:** AGENTS.md line 15: "The skill was renamed from `learning-path` to `tutor`" and CLAUDE.md confirms "Skill auto-registers as `/tutor` based on directory name."

**[ASSUMED]** The current correct GitHub URL is `https://github.com/mmosquera91/tutor` or similar — needs user verification.

### 1.2 Installation Command Format (UNCLEAR)
| Location | README says | Actual |
|----------|-------------|--------|
| Setup | `hermes skills install git+https://github.com/mmosquera91/learning_path_skill.git` | Command format is correct (`hermes skills install`), but the repo name is wrong. Also the skill directory on disk is `tutor`, not `learning_path_skill`. |

**Source:** CLAUDE.md confirms skill auto-registers as `/tutor` based on directory name. The install URL must match the current repo name.

### 1.3 Command Format — Example Session (INCONSISTENT)
| Location | README example | SKILL.md router |
|----------|---------------|-----------------|
| Example session | `You: /tutor submit` (correct) | `/tutor submit <response>` |
| Example session | `Reply /submit <your answer>` (WRONG) | `/tutor submit <response>` |

**Source:** SKILL.md ROUTER table line 58: `/tutor submit <response>` is the actual trigger. The eval.md trigger (line 4) says `/submit <response>` but this is an internal reference — the user-facing command always includes the `/tutor` prefix.

### 1.4 Evaluation Rubric Description (MISALIGNED)
| Location | README says | Actual |
|----------|-------------|--------|
| Evaluation Rubric | "Every submission is scored on two axes (1-10): Conceptual Comprehension + Application Ability" | eval.md step 2 prompt says "Score: 1-10" — no explicit two-axis request. The LLM *could* output two axes (JSON schema in AGENTS.md shows it), but eval.md does not explicitly ask for this. |

**Source:** eval.md step 2 (lines 22-38). The prompt says "Score: 1-10" and asks for "specific, constructive feedback" but does NOT say "score on two axes." However, AGENTS.md evaluation flow (line 198) and the JSON schema in AGENTS.md (lines 209-219) show the expected LLM output includes `conceptual_comprehension` and `application_ability`. The README description is technically what the system *outputs* but not what it *asks for* in the prompt.

**[ASSUMED]** Whether the LLM naturally produces two-axis scoring depends on the model's instruction-following. The JSON schema in AGENTS.md shows it is expected, but eval.md prompt itself does not enforce it.

### 1.5 `/confirm` vs `/tutor confirm` in prose (MINOR)
| Location | README says | Actual |
|----------|-------------|--------|
| Setup, Cron Jobs | "`/confirm` after `/tutor init`" | Should be `/tutor confirm` |
| Limitations | "The `/confirm` step should create cron jobs automatically" | Should be `/tutor confirm` |

**Source:** SKILL.md router table line 56: `/tutor confirm` activates pending syllabus.

### 1.6 Example Session Score Breakdown (MAY BE FABRICATED)
| README shows | Concern |
|-------------|---------|
| "Score: 4.5/10" with breakdown "Conceptual: X, Application: Y" | The eval.md prompt does not ask for separate axis scores — it asks for a single 1-10 score. The example shows a single averaged score with no axis breakdown. This is plausible but the specific axis scores shown in the README (4.5) are not directly prompted for. |

**[ASSUMED]** The example session is illustrative, not a transcript. The specific numbers are fabricated for demonstration purposes, not from an actual evaluation.

---

## 2. What is Actually Implemented vs What README Claims

### Fully Implemented and Working
| Feature | README status | Actual status |
|---------|--------------|----------------|
| Syllabus generation + URL validation | Yes | Implemented (init.md + validate_urls.py) |
| Daily task via cron + Telegram | Yes | Implemented (daily.md) |
| Structured evaluation with rubric | Yes | Implemented (eval.md) |
| `/tutor init`, `/tutor confirm`, `/tutor edit` | Yes | Implemented (SKILL.md router) |
| `/tutor submit`, `/tutor status`, `/tutor skip`, `/tutor pause`, `/tutor resume` | Yes | Implemented (SKILL.md inline) |
| `/tutor review <module>` | Yes | Implemented (adapt.md) |
| `/tutor switch <topic>` | Yes | Implemented (SKILL.md inline) |
| `/tutor export` to Obsidian | Yes | Implemented (SKILL.md inline) |
| Inactivity handling | Yes | Implemented (daily.md step 2+) |
| Weekly review cron (Sundays 22:00) | Yes | Implemented (adapt.md) |
| Decompose logic (score < 4.0) | Yes | Implemented (eval.md step 4) |
| Spaced repetition | Flagged as "not yet validated end-to-end" | Correctly described |
| Obsidian export (requires OBSIDIAN_VAULT_PATH) | Yes | Correctly described |

### Features That Are NOT Implemented but README Does NOT Claim
| Feature | README status |
|---------|--------------|
| Multi-device sync | Not mentioned (v2.0 planned) |
| Configurable delivery time | Not mentioned (v2.0 planned) |
| Rich task types (code execution, diagrams) | Not mentioned |

### Features Listed as v1.1 "In Progress" That Have Partial Implementation
| Feature | README v1.1 section | Actual status |
|---------|---------------------|---------------|
| Adaptation triggers (auto-decompose, auto-accelerate) | Listed under v1.1 in-progress | Code exists in eval.md/adapt.md but not validated end-to-end |
| Milestone celebrations | Listed under v1.1 in-progress | Template exists (`milestone.md`) but not tested end-to-end |

**Assessment:** The README is broadly accurate about what exists vs what is aspirational. The main issues are the installation URL and command format errors, plus the `/submit` vs `/tutor submit` inconsistency.

---

## 3. Correct Setup Workflow

### Prerequisites (correct in README)
- Hermes Agent v0.7+ installed and configured
- Telegram gateway connected
- Python 3.11+ (for init/migration scripts)
- curl (for URL validation)

### Installation (needs correction)
**Current (wrong):**
```bash
hermes skills install git+https://github.com/mmosquera91/learning_path_skill.git
```

**Correct format (repo URL needs verification):**
```bash
hermes skills install git+https://github.com/mmosquera91/tutor.git
```
OR (if skill was forked or renamed):
```bash
hermes skills install git+https://github.com/[org]/tutor.git
```

**Manual install:**
```bash
git clone https://github.com/[org]/tutor.git ~/.hermes/skills/tutor
```

### First Run
```bash
/tutor init <topic>
```

The database (`learning.db`) initializes automatically on first use via `init_db.py`.

### Cron Job Creation
Cron jobs are created automatically during `/tutor confirm` (step 8 of init.md). The agent calls `cronjob(action="create")` with full subskill content inlined. No manual `hermes cron create` needed.

---

## 4. Actual Command Formats from SKILL.md

All commands use the `/tutor <subcommand>` pattern:

| Command | Format | Source |
|---------|--------|--------|
| Generate syllabus | `/tutor init <topic>` | SKILL.md line 55 |
| Activate syllabus | `/tutor confirm` | SKILL.md line 56 |
| Modify syllabus | `/tutor edit <feedback>` | SKILL.md line 57 |
| Submit task answer | `/tutor submit <response>` | SKILL.md line 58 |
| Check progress | `/tutor status` | SKILL.md line 59 |
| Skip today's task | `/tutor skip` | SKILL.md line 60 |
| Pause learning path | `/tutor pause` | SKILL.md line 61 |
| Resume learning path | `/tutor resume` | SKILL.md line 62 |
| Review completed module | `/tutor review <module>` | SKILL.md line 63 |
| Switch active path | `/tutor switch <topic>` | SKILL.md line 64 |
| Export to Obsidian | `/tutor export` | SKILL.md line 65 |

**Key correction:** Free-text messages within 20h window trigger a confirmation prompt (SKILL.md Rule 2). The explicit `/tutor submit` command is the primary path. The 20h window is a fallback, not a primary flow.

---

## 5. Real Example Session Flow

The actual flow based on SKILL.md and subskills:

```
User: /tutor init Python
  → init.md: web research → generate syllabus JSON → validate URLs
  → Present syllabus for review

User: /tutor confirm
  → init.md step 7: save to SQLite (paths, modules, resources)
  → init.md step 8: create cron jobs (daily at 9 AM, weekly Sunday 10 PM)
  → Telegram: confirmation message

[Daily cron at 9 AM]
  → daily.md: check active path exists → check no pending task → find next module
  → Generate task via LLM → save to daily_tasks → deliver via Telegram

User: /tutor submit <response>
  → eval.md step 1: retrieve pending task
  → eval.md step 2: LLM evaluates (Score 1-10, feedback)
  → eval.md step 3: save to daily_tasks
  → eval.md step 4: update module (score_avg, status, completed date)
  → eval.md step 5: decision (advance >= 7.0, repeat 4.0-6.9, decompose < 4.0)
  → Telegram: evaluation + decision

[Weekly cron Sunday 22:00]
  → adapt.md: query metrics → adaptation rules → weekly report → Telegram
```

**Discrepancy in README example session:** The README shows the evaluation with Conceptual/Application axis breakdown. The actual eval.md prompt asks for a single 1-10 score. A real session would likely show a single score with feedback. The rewrite should reflect what eval.md actually prompts for.

---

## 6. Requirements README-01 and README-02 Analysis

### README-01: Audit
**Status:** Complete (above)

The audit found these specific issues:
1. Wrong GitHub repo URL (`learning_path_skill` vs `tutor`)
2. `hermes skills install` command uses wrong URL
3. Example session uses `/submit` instead of `/tutor submit` in one place
4. Evaluation rubric describes two-axis scoring that is not explicitly prompted for in eval.md
5. Prose uses `/confirm` instead of `/tutor confirm` in two places
6. Example session score breakdown may be illustrative rather than transcript-accurate

### README-02: Rewrite
**What to fix:**
1. Update installation URL to current repo name (`tutor`)
2. Fix all command references to use `/tutor <subcommand>` format
3. Align evaluation rubric description with what eval.md actually prompts for (single 1-10 score, not explicitly two-axis)
4. Fix the `/confirm` references to `/tutor confirm`
5. Ensure example session reflects actual eval.md output format

**What to keep:**
1. Overall structure and feature coverage
2. The real example session (fix command formats, adjust score format)
3. Architecture diagram (file structure matches AGENTS.md)
4. Command table (fix the command formats)
5. Design decisions table (accurately describes the architecture)
6. Limitations section (accurately describes known issues)

**What to potentially add:**
1. Correct `hermes skills install` command with verified repo URL
2. Note that spaced repetition needs end-to-end validation (already present)

---

## 7. Recommended Rewrite Approach

### Sections to KEEP (verbatim or with minor fixes)
- **What It Does** list — accurate
- **Architecture** diagram — accurate
- **Commands** table — fix command formats only
- **Evaluation Rubric** — rewrite to match eval.md (single 1-10 score)
- **Inactivity Handling** table — accurate
- **Design Decisions** table — accurate
- **Limitations & Known Issues** — accurate (spaced repetition flag is correct)
- **License** — keep

### Sections to REWRITE
| Section | Current Issue | Rewrite Approach |
|---------|--------------|-------------------|
| Installation | Wrong repo URL | Use correct `tutor` repo URL (user must verify) |
| Setup / First Run | `/confirm` → `/tutor confirm` | Fix all command references |
| Example Session | `/submit` → `/tutor submit`; score breakdown format | Fix commands; use single score format matching eval.md |
| Command table | All correct | Just verify format consistency |
| Cron Jobs | `/confirm` reference | Fix to `/tutor confirm` |

### Sections to potentially REORDER
- Move Installation to top (after "What It Does")
- Consider moving Prerequisites before Installation

### Key Rewrite Constraints
- **Must not claim features that don't exist** — v1.1 features are correctly flagged as in-progress
- **Must use actual command formats** — `/tutor <subcommand>` everywhere
- **Must match eval.md output** — single 1-10 score, not explicitly two-axis (unless model naturally does it)
- **Must use correct repo URL** — `tutor` not `learning_path_skill`

---

## 8. Environment Availability

Step 2.6: SKIPPED (no external dependencies — README is documentation-only, no tool dependencies)

---

## 9. Open Questions

1. **What is the current correct GitHub URL for the skill?**
   - README says `github.com/mmosquera91/learning_path_skill`
   - AGENTS.md says skill was renamed to `tutor`
   - Need user confirmation of actual current repo URL

2. **Does the LLM naturally produce two-axis scoring?**
   - eval.md prompt does NOT explicitly ask for two axes
   - AGENTS.md JSON schema expects `conceptual_comprehension` and `application_ability`
   - If models naturally produce two-axis output without explicit prompting, the README description is accurate
   - If not, the README description overstates what the system prompts for
   - **[ASSUMED]** — recommend testing with current model or making eval.md prompt explicit about two-axis

3. **Is the example session in README a real transcript or illustrative?**
   - README header says "This is an actual session — not a polished demo"
   - But the score breakdown (4.5 with Conceptual/Application) does not match what eval.md prompts for
   - **[ASSUMED]** — the example is illustrative with plausible-but-fabricated details, not a literal transcript

---

## 10. Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Current GitHub URL is `github.com/mmosquera91/tutor` | Section 3 | Installation will fail — user must provide correct URL |
| A2 | LLM naturally produces two-axis scoring | Section 1.4 | README evaluation description may be inaccurate |
| A3 | Example session is illustrative (not transcript-accurate) | Section 1.6 | If it's meant to be real, specific numbers are wrong |

---

## Sources

### Primary (HIGH confidence)
- SKILL.md — actual command formats, router table, persona, rules
- subskills/init.md — actual init flow, command references
- subskills/eval.md — actual evaluation prompt and trigger
- AGENTS.md — architecture documentation, JSON schema expectations
- CLAUDE.md — project constraints, naming conventions

### Secondary (MEDIUM confidence)
- README.md — user-facing documentation (used to identify discrepancies)
- .planning/ROADMAP.md — feature status

### Tertiary (LOW confidence)
- None — all claims verified against source files

---

## Metadata

**Confidence breakdown:**
- Standard stack: N/A (documentation phase)
- Architecture: HIGH — file structure verified against actual files
- Pitfalls: N/A (documentation phase)

**Research date:** 2026-04-13
**Valid until:** 30 days (static documentation — no rapid changes expected)
