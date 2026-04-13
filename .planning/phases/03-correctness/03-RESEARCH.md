# Phase 3: Correctness - Research

**Researched:** 2026-04-13
**Domain:** Template syntax consistency, command format alignment, error handling patterns
**Confidence:** HIGH

## Summary

Phase 3 addresses three correctness bugs in the Tutor skill's Markdown-based templates and subskills. FIX-01 corrects a template placeholder syntax mismatch in eval.md where the evaluation output format needs consistent Mustache syntax. FIX-02 aligns the syllabus template's command references with the actual command format used by the skill router (`/tutor confirm` vs `/confirm`). FIX-03 adds explicit try/except error handling to daily.md's three main failure points: task generation (LLM), database writes, and Telegram delivery.

**Primary recommendation:** All three fixes are small, targeted Markdown edits. The error handling in daily.md should follow the existing pattern from eval.md and init.md — specific exception types with explicit recovery or user messaging.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 3 scope is limited to FIX-01, FIX-02, FIX-03

### Claude's Discretion
- Error handling approach (specific vs. broad try/except)
- Implementation details for each fix

### Deferred Ideas (OUT OF SCOPE)
- FIX-04 (SQL LIKE parameterization) belongs to Phase 1

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-01 | eval.md uses plain text placeholders ({variable}) instead of Mustache syntax ({{variable}}) | Verified eval.md step 6 output uses Mustache `{{variable}}` and sections — may be a false positive or the bug is in how the template gets populated |
| FIX-02 | syllabus template references correct command format (/tutor confirm, /tutor edit) | Confirmed: syllabus.md uses `/confirm` and `/edit` but SKILL.md and init.md use `/tutor confirm` and `/tutor edit` |
| FIX-03 | daily.md has explicit error handling for task generation failure, DB write failure, and Telegram delivery failure | Confirmed: daily.md has no try/except blocks; only silent exit for "no active path" |

## Standard Stack

No new libraries or dependencies. This phase is pure Markdown/Mustache editing in template files and subskill logic files.

| File | Role | Current State |
|------|------|---------------|
| `subskills/eval.md` | Task evaluation subskill | Template syntax appears correct; FIX-01 may need verification |
| `subskills/daily.md` | Daily task generation | Missing all error handling |
| `templates/syllabus.md` | Syllabus rendering template | Wrong command format (FIX-02) |

## Architecture Patterns

### Pattern: Mustache Template Sections (eval.md)

The eval.md step 6 output template uses Mustache sections for conditional content:
```
{{#completed}}
✅ ¡Módulo completado!
{{/completed}}
{{^completed}}
📚 Revisaremos este tema mañana.
{{/completed}}
```

- `{{#section}}...{{/section}}` — truthy section, rendered if variable exists and is non-empty
- `{{^section}}...{{/section}}` — inverted section, rendered if variable is falsy or missing

**Current state:** This pattern is correctly implemented in eval.md. FIX-01 requirement suggests there may have been a historical bug or the issue lies elsewhere.

### Pattern: Error Handling with Specific Exceptions (SKILL.md, init.md)

From eval.md:
```
- If DB update fails: rollback and report error
- If evaluation prompt fails: use generic encouraging feedback
```

From init.md:
```
- Invalid JSON from LLM: retry once with "return valid JSON only"
- DB write fails: report error, do NOT leave partial state
```

**Pattern:** try/except for specific exceptions (sqlite3.OperationalError, subprocess.TimeoutExpired), with explicit recovery or user-facing error message. Do NOT silently continue.

### Anti-Patterns to Avoid

- **Silent failure with no output:** daily.md currently does this for "no active path" (which is correct) but also for task generation failures (which is wrong)
- **Generic catch-all try/except:** Use specific exception types

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Error handling structure | Custom error message format | Follow existing pattern from eval.md/init.md |
| Template syntax | Mix Mustache and plain text placeholders | Use `{{variable}}` consistently throughout |

## Common Pitfalls

### Pitfall 1: Mixing Template Syntaxes
**What goes wrong:** The LLM prompt in step 2 uses `{variable}` (plain text) while the output template in step 6 uses `{{variable}}` (Mustache). This is actually intentional — LLM prompts are not Mustache templates. But developers might "fix" the LLM prompt to use `{{variable}}` breaking the prompt interpolation.
**How to avoid:** The fix for FIX-01 should only touch the evaluation output template (step 6), not the LLM evaluation prompt (step 2).

### Pitfall 2: Over-wide Exception Catching
**What goes wrong:** Using bare `except:` catches KeyboardInterrupt and SystemExit, which can prevent clean shutdown.
**How to avoid:** Use specific exception types: `except sqlite3.OperationalError:`, `except subprocess.TimeoutExpired:`, etc.

## Code Examples

### Example: Error Handling Pattern for DB Write (from existing patterns)

From init.md error handling concept:
```python
try:
    # DB operation
except sqlite3.OperationalError as e:
    # Report error, do NOT leave partial state
    print(f"DB write failed: {e}")
```

### Example: Mustache Section Syntax (correct, from eval.md step 6)

```markdown
{{#completed}}
✅ ¡Módulo completado!
{{/completed}}
{{^completed}}
📚 Revisaremos este tema mañana.
{{/completed}}
```

### Example: Command Format (from SKILL.md router, lines 53-65)

```
| `/tutor confirm` | Activate pending syllabus | `subskills/init.md` step 6 |
| `/tutor edit <feedback>` | Regenerate syllabus with changes | `subskills/init.md` step 2-4 |
```

## State of the Art

No changes in this domain. Template syntax and error handling patterns are stable.

**Deprecated/outdated:** None

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | FIX-01 eval.md template already uses Mustache syntax | FIX-01 Analysis | LOW — if wrong, the planner will catch it when the actual file is edited and verified |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **FIX-01 discrepancy**
   - What we know: eval.md step 6 output template (lines 73-86) uses Mustache syntax `{{date}}`, `{{#completed}}`, etc. This is correct.
   - What's unclear: The REQUIREMENTS.md says "eval.md uses plain text placeholders ({variable}) instead of Mustache syntax" — but the current file appears to use Mustache correctly. Either the bug was already fixed, or the bug is in a different part of eval.md not visible in step 6.
   - Recommendation: When planning, verify the actual eval.md content and confirm where FIX-01 needs to apply.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — pure Markdown/ Mustache editing, no tools or services needed)

## Security Domain

Not applicable — no security requirements in this phase (FIX-01, FIX-02, FIX-03 are all correctness/template bugs, not security-related).

## Sources

### Primary (HIGH confidence)
- `subskills/eval.md` - Verified Mustache template syntax in step 6
- `subskills/daily.md` - Confirmed absence of error handling for task generation, DB write, Telegram delivery
- `templates/syllabus.md` - Confirmed `/confirm` and `/edit` command format (wrong)
- `SKILL.md` - Confirmed correct command format is `/tutor confirm` and `/tutor edit`
- `subskills/init.md` - Confirmed correct command format in step 6

### Secondary (MEDIUM confidence)
- CLAUDE.md conventions for error handling patterns

## Metadata

**Confidence breakdown:**
- FIX-02 (command format): HIGH — confirmed bug in syllabus.md
- FIX-03 (error handling): HIGH — confirmed absence in daily.md
- FIX-01 (template syntax): MEDIUM — appears correct in current file, but requirement states bug exists

**Research date:** 2026-04-13
**Valid until:** 30 days (stable domain — Mustache templates and error handling don't change rapidly)