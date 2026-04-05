# Contributing to learning-path skill

## URL Validation System

The most common issue with this skill is **broken URLs**, especially from YouTube. We've implemented a TIER system to ensure reliability.

### Source Tiers

| Tier | Source | Reliability | Max/Module |
|------|--------|-------------|------------|
| TIER 1 | chess.com/lessons/*, lichess.org/learn/* | ⭐⭐⭐⭐⭐ | Unlimited |
| TIER 2 | Coursera, edX, Khan Academy, official docs | ⭐⭐⭐⭐ | 2 |
| TIER 3 | YouTube (single videos ONLY) | ⭐⭐ | 1 |
| TIER 4 | Wikipedia, reference materials | ⭐⭐ | 1 |

### Critical Rules

1. **NO YouTube Playlists** — Reject any URL with `&list=` parameter
2. **Minimum 50% TIER 1** — At least half of resources must be from chess.com or lichess
3. **Validate before presenting** — Always run the validator on generated syllabi

### Testing URL Validation

```bash
# Check a single URL
python3 scripts/validate_urls.py --check "https://chess.com/lessons/pins-and-skewers"

# Validate a full syllabus
python3 scripts/validate_urls.py --http --file syllabus.json

# Or via stdin
cat syllabus.json | python3 scripts/validate_urls.py --http
```

### Common Issues & Fixes

**Problem:** YouTube playlist URLs (like `youtube.com/watch?v=XXX&list=YYY`)
- **Fix:** Remove `&list=` and everything after it
- **Better:** Replace with TIER 1 resource from chess.com/lichess

**Problem:** Generic URLs (like `chess.com/lessons` without specific lesson)
- **Fix:** Find the specific lesson URL from search results

**Problem:** Not enough TIER 1 resources in a module
- **Fix:** Add more chess.com or lichess interactive lessons

### Running Tests

```bash
# Test the validation script
python3 -m pytest scripts/test_validate_urls.py -v
```

## Submitting Changes

1. Test your changes with `/tutor init <topic>`
2. Run the validator on generated syllabi
3. Ensure all modules have ≥50% TIER 1 resources
4. Submit PR with test outputs showing validation passes
