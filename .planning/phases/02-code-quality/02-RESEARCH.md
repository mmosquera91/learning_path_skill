# Phase 2: Code Quality - Research

**Researched:** 2026-04-13
**Domain:** Markdown deduplication, file reduction, Hermes skill architecture
**Confidence:** HIGH

## Summary

Phase 2 is a refactoring/quality pass: deduplicate tier rules across files and shrink SKILL.md and init.md to meet line-count targets. The canonical sources are already identified (CONTRIBUTING.md + validate_urls.py). The main challenge is surgical line removal without breaking functionality. Key extraction: syllabus generation prompt moves to `templates/init-syllabus.md`, save-to-DB logic moves to `scripts/save_path.py`.

**Primary recommendation:** Follow the decisions exactly (D-07 through D-10). Extract save-to-DB to a Python script (net ~30 lines from init.md). Add 8-line tier table inline in subskills per D-09. SKILL.md reduction is primarily achieved by replacing the tier rules block (~26 lines) with a short reference, plus removing topic examples (~7 lines).

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-07:** SKILL.md and init.md reference CONTRIBUTING.md directly for tier rules -- no inline copies. validate_urls.py remains the enforcement canonical.
- **D-08:** Extract syllabus generation prompt to `templates/init-syllabus.md` (Approach A). Plus ~40 additional lines compressed from init.md through research phase compression and step consolidation to reach ~152 lines.
- **D-09:** Subskills (init.md, daily.md, etc.) include the inline 8-line tier summary table from CONTRIBUTING.md since they may run in cron with zero context. SKILL.md uses direct reference only.
- **D-10:** Remove topic-specific examples (lines 59-65 from current SKILL.md) from the tier rules section -- keep only the summary table and core rules. Trim PITFALLS section slightly to reach ~198 lines total.

### Deferred Ideas

None -- discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEDUP-01 | Tier system rules defined in one canonical location (CONTRIBUTING.md + validate_urls.py), referenced by SKILL.md and init.md instead of duplicated inline | D-07/D-09 define reference structure; CONTRIBUTING.md is canonical source |
| QUAL-01 | SKILL.md under 200 lines after tier rule deduplication and additional trimming | D-10 targets ~198 lines; topic examples removal + tier rules block replacement achieves this |
| QUAL-02 | init.md under 150 lines by extracting syllabus generation prompt to a template and save-to-DB logic to a Python script | D-08 targets ~152 lines; extraction of prompt (~45L) and save-to-DB (~30L) plus consolidation achieves this |

## Standard Stack

No new libraries needed. All Python uses stdlib only.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sqlite3 | stdlib | Database operations in extracted script | Already in use |
| json | stdlib | Parsing syllabus JSON in extracted script | Already in use |
| datetime | stdlib | Timestamps in extracted script | Already in use |

## Architecture Patterns

### Tier Rule Deduplication Structure

```
CONTRIBUTING.md (lines 9-14)        -- 8-line summary table (canonical)
  └── Referenced by: SKILL.md       -- "See CONTRIBUTING.md §1-3 for full rules"
  └── Inlined in: init.md, daily.md -- 8-line summary table (for cron context)

scripts/validate_urls.py             -- TIER_PATTERNS dict (enforcement canonical)
  └── validate_urls.py called by: init.md step 4 (already unchanged)
```

**Reference approach per D-07/D-09:**
- SKILL.md: Replace tier rules block with short reference + keep only 8-line summary table inline
- Subskills (init.md, daily.md, adapt.md, eval.md): Include the full 8-line summary table inline since cron sessions have zero context

### 8-line Tier Summary Table (from CONTRIBUTING.md lines 9-14)

```markdown
| Tier | Source Type | Examples | Reliability | Max/Module |
|------|-------------|----------|-------------|------------|
| TIER 1 | Interactive platforms | exercism.org, codecademy.com, duolingo.com, chess.com/lessons | ⭐⭐⭐⭐⭐ | Unlimited |
| TIER 2 | Official courses | Coursera, edX, Khan Academy, docs | ⭐⭐⭐⭐ | 2 |
| TIER 3 | YouTube (single videos ONLY) | Individual videos, NO playlists | ⭐⭐ | 1 |
| TIER 4 | Reference materials | Wikipedia, technical blogs | ⭐⭐ | 1 |
```

### Syllabus Template (templates/init-syllabus.md)

**Mustache variables needed:**

| Variable | Source | Description |
|----------|--------|-------------|
| `{{topic}}` | From user input | Learning topic |
| `{{description}}` | LLM-generated | Path description |
| `{{estimated_duration}}` | LLM-generated | Duration string |
| `{{#modules}}...{{/modules}}` | LLM-generated | Module loop |
| `{{number}}` | LLM-generated | Module sequence number |
| `{{title}}` | LLM-generated | Module title |
| `{{is_milestone}}` | LLM-generated | Milestone flag |
| `{{description}}` | LLM-generated | Module description |
| `{{estimated_time}}` | LLM-generated | Module duration |
| `{{#resources}}...{{/resources}}` | LLM-generated | Resource loop |
| `{{url}}`, `{{title}}`, `{{type}}` | From research | Resource fields |
| `{{verified}}` | From validation step | Verification status |

The template replaces the ~45-line prompt block currently embedded in init.md step 3. The LLM generates the JSON, then init.md renders it through the template.

### Save-to-DB Script (scripts/save_path.py)

Step 7 in init.md is 30 lines of inline Python handling path insertion, module insertion, resource insertion, and config update. Extracting this to a script:

**Interface:**
```bash
python3 scripts/save_path.py --syllabus-json '{"topic": "...", "modules": [...]}'
```

**Inputs:** JSON syllabus (from step 3 output), DB path (hardcoded as per project convention)
**Outputs:** Sets `active_path_id` in config, creates path + modules + resources records
**Error handling:** On failure, script exits non-zero; init.md reports error to user (no partial state)

The inline Python in step 7 (lines 194-224) gets replaced by:
```bash
python3 ~/.hermes/skills/tutor/scripts/save_path.py --syllabus-json "$SYLLABUS_JSON"
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tier classification | Custom regex patterns | TIER_PATTERNS in validate_urls.py | Already covers generic and topic-specific patterns |
| Syllabus JSON generation | Custom prompt template strings | templates/init-syllabus.md | Mustache template already established pattern in project |
| DB save logic | Inline Python in Markdown | scripts/save_path.py | Complex logic in f-strings breaks with backslashes/quotes |

## Common Pitfalls

### Pitfall 1: SKILL.md still exceeds 200 lines after only removing topic examples
**What goes wrong:** Removing lines 59-65 (7 lines) gets SKILL.md from 222 to ~215, still over target.
**How to avoid:** D-10 says "Trim PITFALLS section slightly" AND the tier rules block (26 lines) must be replaced with a shorter reference. The combination of these achieves the target.
**Warning signs:** `wc -l SKILL.md` returns > 200 after only removing topic examples.

### Pitfall 2: init.md research phase loses critical guidance when condensed
**What goes wrong:** Compressing the 15-line research phase to 5 lines might drop important guidance about URL specificity or search strategy.
**How to avoid:** Keep the search queries template (lines 37-42) and the "capture" bullet points (lines 44-47). Replace the TRUSTED SOURCE RULES block (lines 49-67) with a reference to CONTRIBUTING.md and the 8-line inline tier table per D-09.
**Warning signs:** LLM generates generic URLs instead of lesson-specific ones after the change.

### Pitfall 3: Breaking the init flow by extracting pieces that still have cross-references
**What goes wrong:** Extracting syllabus prompt to template but leaving some guidance about resource selection in init.md body, creating contradictory instructions.
**How to avoid:** The template is purely formatting (variables and Mustache sections). All guidance lives in init.md step 3 which calls the template. No embedded logic in template.

### Pitfall 4: save_path.py changes database schema assumptions
**What goes wrong:** If the extracted script doesn't handle all the same cases as the inline code (foreign keys, JSON field names, verified status defaults).
**How to avoid:** Script must handle: `verified` defaults to `"pending"` if not in resource dict. All other fields map directly from syllabus JSON. Foreign keys (`path_id`, `module_id`) set correctly.

## Code Examples

### SKILL.md tier rules block replacement

**Current (lines 42-66, ~25 lines):**
```markdown
## SOURCE TIER SYSTEM (URL Reliability)

When gathering resources, prioritize by tier:

| Tier | Source Type | Reliability | Max per Module |
|------|-------------|-------------|----------------|
| TIER 1 | Interactive platforms... | ⭐⭐⭐⭐⭐ | Unlimited |
...

**Topic-Specific TIER 1 Examples:**
- Programming: codecademy.com...
```

**After (reference + trimmed, ~8 lines):**
```markdown
## SOURCE TIER SYSTEM (URL Reliability)

See CONTRIBUTING.md §1-3 for full tier rules and topic-specific examples.

| Tier | Source Type | Reliability | Max/Module |
|------|-------------|-------------|------------|
| TIER 1 | Interactive platforms | ⭐⭐⭐⭐⭐ | Unlimited |
| TIER 2 | Official courses | ⭐⭐⭐⭐ | 2 |
| TIER 3 | YouTube (single videos ONLY) | ⭐⭐ | 1 |
| TIER 4 | Reference materials | ⭐⭐ | 1 |
```

### init.md tier rules consolidation

**Current:** Lines 49-67 duplicate the full tier rules in the research phase, AND lines 72-85 duplicate them again in the syllabus prompt section.

**After:** Replace both duplications with:
1. A single reference: "See CONTRIBUTING.md §1-3 for full rules"
2. The 8-line inline tier table (inserted once in the research phase section, before the search queries)

### daily.md cron context inline (D-09 compliance)

daily.md is 95 lines. Adding the 8-line tier table inline (D-09 says subskills need it for cron context) adds 8 lines but these are necessary for correctness. The subskill remains self-contained.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SKILL.md line-count target (~198) is achieved by replacing the ~26-line tier rules block with ~8 lines (reference + 6-line table) and removing topic examples (~7 lines) | QUAL-01 | If tier block can't be trimmed that much, target won't be met without additional cuts |
| A2 | The 8-line tier summary table in CONTRIBUTING.md (lines 9-14) is the exact table to inline in subskills | DEDUP-01 | If table content differs between files, subskills might show different rules than CONTRIBUTING.md |
| A3 | save_path.py interface (--syllabus-json flag) is the right approach; no other parameters needed | QUAL-02 | If LLM can't capture JSON to a variable for script invocation, alternative approach needed |

## Open Questions

1. **Cron job prompt inlining -- how is the subskill content actually inlined?**
   - What we know: CRON JOB NOTES (SKILL.md lines 216-223) describe that cron jobs inline full subskill content. daily.md (95 lines) and adapt.md (73 lines) are the cron subskills.
   - What's unclear: Whether the cron system literally inlines the file content or references it. If inlining, the 8-line tier table added to subskills per D-09 costs 8 lines per subskill but is necessary for correctness.
   - Recommendation: Verify by checking Hermes documentation or testing a cron job with a modified subskill.

2. **How does init.md invoke the extracted save_path.py if LLM generates JSON as text?**
   - What we know: The LLM generates syllabus JSON in step 3. Step 7 currently has inline Python that uses `syllabus["topic"]` etc.
   - What's unclear: How does the JSON from step 3 become available to a shell command in step 7? Options: (a) save to temp file in step 3, read in step 7; (b) LLM captures JSON to a variable passed to script; (c) inline the JSON directly in the bash command.
   - Recommendation: Option (a) -- save JSON to `/tmp/syllabus.json` in step 3, then `python3 scripts/save_path.py --file /tmp/syllabus.json` in step 7. This matches the pattern used for `validate_urls.py --http < /tmp/syllabus.json` in step 4.

3. **Should adapt.md and eval.md also get the inline 8-line tier table, or only init.md and daily.md?**
   - What we know: D-09 says "Subskills (init.md, daily.md, etc.)" -- broad but implies all cron-context subskills.
   - What's unclear: adapt.md and eval.md don't do resource gathering; they work with existing modules. They may not need the tier table.
   - Recommendation: Only add the 8-line table to init.md (resource gathering) and daily.md (resource review). adapt.md and eval.md don't gather new resources so the table is unnecessary.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified -- Phase 2 is purely file refactoring with existing Python stdlib scripts)

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pytest.ini (if any) or defaults |
| Quick run command | `python3 -m pytest tests/ -x` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Existing Test Infrastructure

| Test File | Coverage |
|-----------|----------|
| tests/test_validate_urls.py | Full coverage of classify_url(), 4 tiers + edge cases |
| tests/test_init_db.py | Idempotent table creation, config key initialization |
| tests/test_migrate_db.py | Forward migration v1->v2 |
| tests/test_eval_pipeline.py | State transitions (advance/repeat) with mocked JSON |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists |
|--------|----------|-----------|-------------------|-------------|
| DEDUP-01 | Tier rules referenced, not duplicated | Manual | `grep -c "TIER 1\|TIER 2\|TIER 3\|TIER 4" SKILL.md` | Manual verification |
| QUAL-01 | SKILL.md < 200 lines | Smoke | `wc -l SKILL.md` | N/A |
| QUAL-02 | init.md < 150 lines | Smoke | `wc -l subskills/init.md` | N/A |
| DEDUP-01 | validate_urls.py unchanged | Regression | `python3 -m pytest tests/test_validate_urls.py -x` | ✅ |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_validate_urls.py -x`
- **Per wave merge:** Full suite
- **Phase gate:** Line-count checks (`wc -l`) + full test suite green

### Wave 0 Gaps

None -- existing test infrastructure covers all phase requirements. DEDUP-01 is verified by line-count checks and grep, not unit tests.

## Security Domain

Step 2.6: SKIPPED (Phase 2 is a refactoring pass; no new security surfaces introduced)

## Sources

### Primary (HIGH confidence)
- CONTROLLING.md lines 1-74 -- canonical tier rules
- scripts/validate_urls.py lines 1-223 -- TIER_PATTERNS dict, enforcement canonical
- SKILL.md -- current router (222 lines)
- subskills/init.md -- current init flow (257 lines)
- templates/evaluation.md -- existing Mustache template pattern
- templates/daily-task.md -- existing Mustache template pattern
- templates/syllabus.md -- existing syllabus template

### Secondary (MEDIUM confidence)
- Phase 1 context (01-CONTEXT.md) -- for understanding prior decisions
- STATE.md -- for project state overview

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, pure refactoring
- Architecture: HIGH -- decisions (D-07 through D-10) fully specify the structure
- Pitfalls: MEDIUM -- some assumptions about line counts may need adjustment during implementation

**Research date:** 2026-04-13
**Valid until:** 2026-05-13 (30 days -- refactoring task, stable requirements)
