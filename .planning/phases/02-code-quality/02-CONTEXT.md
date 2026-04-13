# Phase 2: Code Quality - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Deduplicate tier rules across SKILL.md, init.md, adapt.md, and eval.md — keeping only one canonical copy (CONTRIBUTING.md + validate_urls.py). Reduce SKILL.md to under 200 lines and init.md to under 150 lines. Safe to refactor thanks to the test suite built in Phase 1.

Requirements: DEDUP-01, QUAL-01, QUAL-02

</domain>

<decisions>
## Implementation Decisions

### Tier Rule Deduplication (DEDUP-01)
- **D-07:** SKILL.md and init.md reference `CONTRIBUTING.md` directly for tier rules — no inline copies. validate_urls.py remains the enforcement canonical.

### init.md Extraction (QUAL-02)
- **D-08:** Extract syllabus generation prompt to `templates/init-syllabus.md` (Approach A). Plus ~40 additional lines compressed from init.md through research phase compression and step consolidation to reach ~152 lines.

### Reference Structure (DEDUP-01)
- **D-09:** Subskills (init.md, daily.md, etc.) include the inline 8-line tier summary table from CONTRIBUTING.md since they may run in cron with zero context. SKILL.md uses direct reference only.

### SKILL.md Reduction (QUAL-01)
- **D-10:** Remove topic-specific examples (lines 59-65 from current SKILL.md) from the tier rules section — keep only the summary table and core rules. Trim PITFALLS section slightly to reach ~198 lines total.

### Folded Todos
None.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tier System
- `CONTRIBUTING.md` §1-3 — Full tier system rules, critical rules, topic-specific sources
- `scripts/validate_urls.py` — `TIER_PATTERNS` dict; the enforcement canonical
- `.planning/phases/01-foundation/01-CONTEXT.md` — Phase 1 decisions (D-01 to D-06)

### File Structure
- `SKILL.md` — Router; target: <200 lines (currently 222)
- `subskills/init.md` — Target: <150 lines (currently 257)
- `templates/evaluation.md` — Existing template pattern to follow
- `templates/daily-task.md` — Existing template pattern to follow

### Prior Decisions
- `D-06:` Test directory at project root (`tests/`), invoked via `python -m pytest tests/`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `templates/evaluation.md` — Mustache template pattern already established
- `scripts/validate_urls.py` — Already the enforcement canonical for tier classification

### Established Patterns
- Templates use Mustache-style `{{variable}}` syntax
- Error handling: try/except for specific exceptions, idempotent operations
- Python scripts use stdlib only

### Integration Points
- init.md step 7 (save to SQLite) is called after user confirms syllabus
- cron jobs inline the full subskill content — templates referenced in init.md must be self-contained

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-code-quality*
*Context gathered: 2026-04-13*