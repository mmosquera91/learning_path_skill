# README Audit Report — Phase 05-01

**Audited:** 2026-04-13
**Source files:** README.md, SKILL.md, subskills/eval.md, subskills/init.md, subskills/daily.md, subskills/adapt.md
**Verification:** git remote URL

---

## Discrepancies Found

### D1: eval.md Trigger Mismatch (CODE BUG — not just documentation)

| Location | Current | Should Be | Source |
|----------|---------|-----------|--------|
| eval.md line 4 | `/submit <response>` | `/tutor submit <response>` | SKILL.md router (line 58) maps `/tutor submit <response>` to eval.md |

**Analysis:** The SKILL.md ROUTER table maps `/tutor submit <response>` to eval.md. However, eval.md's own trigger condition says `/submit <response>`. This is a bug — the trigger in eval.md should match the router's command so the subskill loads correctly when the user invokes `/tutor submit`. The bare `/submit` trigger is inconsistent with all other commands which use the `/tutor <subcommand>` pattern.

**Fix required:** Change eval.md line 4 from `/submit <response>` to `/tutor submit <response>`.

---

### D2: README Example Session — Score Format Mismatch

| Location | Current | Should Be | Source |
|----------|---------|-----------|--------|
| README line 65 | `Score: 4.5/10` with Conceptual/Application axis breakdown | Single averaged score (e.g., `Score: 6/10`) with overall feedback | eval.md step 2: "Score: 1-10" (single score, no axis breakdown requested) |

**Analysis:** The eval.md prompt asks for a single "Score: 1-10" with feedback. It does NOT explicitly ask for separate Conceptual Comprehension and Application Ability scores. The example session in README shows `Score: 4.5/10` with an axis breakdown that is not what eval.md prompts for. A realistic example should show a single averaged score with overall feedback.

**Note:** The README header claims "This is an actual session." However, the specific score breakdown does not match the eval.md prompt. Whether it is a real transcript or illustrative, the example should match the actual evaluation prompt.

---

### D3: README Limitations — Bare `/confirm` Reference

| Location | Current | Should Be | Source |
|----------|---------|-----------|--------|
| README line 227 | "The `/confirm` step should create cron jobs automatically" | "The `/tutor confirm` step should create cron jobs automatically" | SKILL.md router (line 56): `/tutor confirm` activates pending syllabus |

**Analysis:** All commands in the router table use `/tutor <subcommand>` format. The bare `/confirm` in the Limitations section is inconsistent.

---

### D4: README Evaluation Rubric — Two-Axis Description

| Location | Current | Should Be | Source |
|----------|---------|-----------|--------|
| README lines 169-175 | Two-axis rubric: Conceptual Comprehension + Application Ability | Single 1-10 score with feedback | eval.md step 2: "Score: 1-10" with feedback on Completeness, Understanding, Effort |

**Analysis:** The eval.md prompt asks for a single "Score: 1-10" with feedback on Completeness, Understanding, and Effort. It does NOT explicitly ask for separate axis scores. The README's two-axis table describes what the JSON schema *accepts* (per AGENTS.md) but not what the evaluation prompt *requests*. The rewrite should describe a single 1-10 score.

---

### D5: README Cron Jobs Section — Bare `/confirm` Reference

| Location | Current | Should Be | Source |
|----------|---------|-----------|--------|
| README line 148 | "`/confirm` after `/tutor init`" | "`/tutor confirm` after `/tutor init`" | SKILL.md router (line 56) |

**Analysis:** Consistent with D3 — bare `/confirm` should be `/tutor confirm`.

---

## Items Verified Correct

The following items were audited and found to be accurate:

| Item | Status | Evidence |
|------|--------|----------|
| GitHub URL | CORRECT | git remote: `https://github.com/mmosquera91/learning_path_skill.git` — matches README |
| `/tutor init` command | CORRECT | SKILL.md line 55, README line 31 |
| `/tutor confirm` command | CORRECT | SKILL.md line 56, README line 31 |
| `/tutor edit` command | CORRECT | SKILL.md line 57, README line 111 |
| `/tutor submit` command | CORRECT | SKILL.md line 58, README lines 51, 53 |
| `/tutor status` command | CORRECT | SKILL.md line 59, README line 113 |
| `/tutor skip`, `/tutor pause`, `/tutor resume` | CORRECT | SKILL.md lines 60-62, README lines 114-116 |
| `/tutor review`, `/tutor switch`, `/tutor export` | CORRECT | SKILL.md lines 63-65, README lines 117-119 |
| Inactivity handling table | CORRECT | daily.md step 2+: 0-1 days normal, 2 days nudge+skip, 3 days pause offer, 5+ auto-pause |
| Spaced repetition rules | CORRECT | eval.md step 6: >= 8.0 review 7 days, 5.0-7.9 review 3 days, < 5.0 next session |
| Evaluation decision rules | CORRECT | eval.md step 4-5: >= 7.0 completed, 4.0-6.9 in_progress, < 4.0 decompose |
| Cron creation during `/tutor confirm` | CORRECT | init.md step 8 |
| Architecture diagram | CORRECT | File structure matches actual layout |
| Design decisions table | CORRECT | Describes actual architecture decisions |

---

## Summary

| Discrepancy | Severity | Fix Location |
|-------------|----------|--------------|
| D1: eval.md trigger `/submit` vs `/tutor submit` | CODE BUG | eval.md line 4 |
| D2: Example session score format | Documentation | README line 65 |
| D3: Bare `/confirm` in Limitations | Documentation | README line 227 |
| D4: Two-axis rubric description | Documentation | README lines 169-175 |
| D5: Bare `/confirm` in Cron Jobs | Documentation | README line 148 |

**Note on GitHub URL:** The research phase (05-RESEARCH.md) incorrectly flagged the GitHub URL as wrong. Verification against `git remote` confirms the URL in README (`https://github.com/mmosquera91/learning_path_skill.git`) is correct. The skill was renamed from `learning_path_skill` directory naming convention (auto-registers as `/tutor`) but the repo URL remains `learning_path_skill`.
