# Phase 2: Code Quality - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 02-code-quality
**Areas discussed:** Tier rule deduplication, init.md extraction, reference structure, SKILL.md reduction

---

## Tier Rule Deduplication

| Option | Description | Selected |
|--------|-------------|----------|
| A: Minimal summary in SKILL.md | Keep brief table in SKILL.md, reference CONTRIBUTING.md | |
| B: Direct reference only | SKILL.md and init.md both just say "See CONTRIBUTING.md" | ✓ |
| C: validate_urls.py as canonical | Only validate_urls.py is referenced | |

**User's choice:** Option B (direct reference)
**Notes:** validate_urls.py is the enforcement mechanism, not the explanation. SKILL.md and init.md should reference CONTRIBUTING.md directly.

---

## init.md Extraction

| Option | Description | Selected |
|--------|-------------|----------|
| A: Prompt → template | Extract syllabus generation prompt to templates/init-syllabus.md | ✓ |
| B: Save → script | Extract save-to-DB logic to scripts/save_path.py | |
| C: Both | Both prompt to template AND save to script | |

**User's choice:** Approach A (prompt → template), but also compress ~40 additional lines to reach ~152 total
**Notes:** This codebase already uses templates for output formatting — it's an established pattern. User agreed with recommendation to also compress remaining lines through research phase compression and step consolidation.

---

## Reference Structure

| Option | Description | Selected |
|--------|-------------|----------|
| A: Direct reference only | "See CONTRIBUTING.md" — cross-file reading required | |
| B: Inline summary table | Subskills include 8-line tier summary table inline | ✓ |
| C: Claude's discretion | Let LLM handle with validate_urls.py as only source | |

**User's choice:** Option B
**Notes:** For cron sessions with zero context, the LLM needs the tier table inline. SKILL.md uses direct reference only.

---

## SKILL.md Reduction Target

| Option | Description | Selected |
|--------|-------------|----------|
| A: Strip detailed tier rules entirely | Remove lines 42-65 completely | |
| B: Keep summary table, remove topic examples | Pragmatic middle ground | ✓ |
| C: Keep everything but reorganize | Minimal change, stays over 200 lines | |

**User's choice:** Option B (keep summary table + trim topic examples + compress PITFALLS)
**Notes:** Target ~198 lines. Remove topic-specific examples (lines 59-65), trim PITFALLS section, keep summary table and core rules.

---

## Claude's Discretion

No areas deferred to Claude — all decisions made by user.

## Deferred Ideas

None — discussion stayed within phase scope.