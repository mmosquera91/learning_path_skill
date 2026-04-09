# Contributing to learning-path skill

## URL Validation System

The most common issue with this skill is **broken URLs**, especially from YouTube. We've implemented a TIER system to ensure reliability across ALL topics.

### Source Tiers (Topic-Agnostic)

| Tier | Source Type | Examples | Reliability | Max/Module |
|------|-------------|----------|-------------|------------|
| TIER 1 | Interactive platforms | exercism.org, codecademy.com, duolingo.com, chess.com/lessons | ⭐⭐⭐⭐⭐ | Unlimited |
| TIER 2 | Official courses | Coursera, edX, Khan Academy, docs | ⭐⭐⭐⭐ | 2 |
| TIER 3 | YouTube (single videos ONLY) | Individual videos, NO playlists | ⭐⭐ | 1 |
| TIER 4 | Reference materials | Wikipedia, technical blogs | ⭐⭐ | 1 |

### Critical Rules

1. **NO YouTube Playlists** — Reject any URL with `&list=` parameter
2. **Minimum 50% TIER 1** — At least half of resources must be from interactive learning platforms
3. **Topic-adaptive** — TIER 1 sources vary by topic (programming, languages, chess, etc.)
4. **Validate before presenting** — Always run the validator on generated syllabi

### Testing URL Validation

```bash
# Check a single URL
python3 scripts/validate_urls.py --check "https://exercism.org/tracks/python"

# Validate a full syllabus
python3 scripts/validate_urls.py --http --file syllabus.json

# Or via stdin
cat syllabus.json | python3 scripts/validate_urls.py --http
```

### Common Issues & Fixes

**Problem:** YouTube playlist URLs (like `youtube.com/watch?v=XXX&list=YYY`)
- **Fix:** Remove `&list=` and everything after it
- **Better:** Replace with TIER 1 interactive resource

**Problem:** Generic URLs (like `/tutorials` or `/courses` without specific lesson)
- **Fix:** Find the specific lesson/exercise URL from search results

**Problem:** Not enough TIER 1 resources in a module
- **Fix:** Add more interactive platform resources (exercises, lessons, practice)

**Problem:** Validator doesn't recognize a good TIER 1 source
- **Fix:** Update `TIER_PATTERNS` in `scripts/validate_urls.py` with the new pattern

### Topic-Specific TIER 1 Sources

| Topic | Preferred TIER 1 Sources |
|-------|-------------------------|
| Programming | exercism.org, codecademy.com, leetcode.com/studyplan/* |
| Languages | duolingo.com, babbel.com, busuu.com |
| Chess | chess.com/lessons/*, lichess.org/learn/* |
| Math/Science | khanacademy.org/*, brilliant.org/courses/* |
| Music | musictheory.net/lessons/*, teoria.com |

### Running Tests

```bash
# Test the validation script
python3 -m pytest scripts/test_validate_urls.py -v
```

## Submitting Changes

1. Test your changes with `/tutor init <topic>` (try different topics!)
2. Run the validator on generated syllabi
3. Ensure all modules have ≥50% TIER 1 resources
4. Submit PR with test outputs showing validation passes
