# Testing Patterns

**Analysis Date:** 2026-04-12

## Overview

This project has **minimal automated testing infrastructure**. The codebase is primarily Markdown prompt files for an LLM-based skill, with three Python utility scripts. There are no test files, no test configuration, no CI pipeline, and no coverage tools.

## Test Framework

**Automated Tests:**
- No test framework configured
- No `pytest`, `unittest`, `vitest`, or any test runner present
- No `pyproject.toml`, `setup.cfg`, `tox.ini`, or `requirements.txt` for test dependencies
- No test configuration files (no `pytest.ini`, `conftest.py`, etc.)

**Contributing docs reference pytest but no tests exist:**
`CONTRIBUTING.md` line 65 mentions:
```bash
python3 -m pytest scripts/test_validate_urls.py -v
```
But the file `scripts/test_validate_urls.py` does **not exist** in the repository. This is a documentation reference to tests that were either planned or removed.

## Test File Organization

**Current State:** No test files exist anywhere in the repository.

**Expected pattern (from CONTRIBUTING.md reference):**
- Test files would co-locate with source: `scripts/test_validate_urls.py` alongside `scripts/validate_urls.py`
- Naming: `test_{module_name}.py` (pytest convention)

## Manual Testing

The project relies entirely on manual testing. `AGENTS.md` contains a detailed testing checklist in Section 9:

### Manual Test Categories

**Init Flow** (`AGENTS.md` lines 319-323):
- `/tutor init <topic>` generates syllabus with valid JSON
- URLs verified with HEAD requests
- `/confirm` saves to SQLite and sets `active_path_id`
- `/edit <feedback>` regenerates incorporating feedback
- Duplicate init with existing active path prompts user to pause first

**Daily Task Flow** (`AGENTS.md` lines 326-332):
- Cron job at 9 AM generates and delivers a task
- No duplicate tasks on same day
- Inactive path / no active path handling
- Inactivity escalation: 2 days nudge, 3 days offer pause, 5 days auto-pause
- All modules completed triggers completion message

**Evaluation Flow** (`AGENTS.md` lines 335-344):
- `/submit <response>` triggers evaluation
- Free text within/outside 20h window handling
- Score thresholds: >= 7.0 advance, 4.0-6.9 repeat, < 4.0 decompose
- Evaluation JSON parsing
- Failed JSON parse retry behavior
- State cleanup after evaluation

**Weekly Review Flow** (`AGENTS.md` lines 347-351):
- Cron job on Sunday sends weekly report
- Metrics calculation
- Adaptation rules
- Obsidian export
- Silent exit conditions

**State Management** (`AGENTS.md` lines 354-358):
- `init_db.py` idempotency
- `migrate_db.py` version upgrade handling
- Pause/resume/skip state transitions

### URL Validation Script

The only script with a documented test approach is `validate_urls.py`. From `CONTRIBUTING.md`:

```bash
# Check a single URL
python3 scripts/validate_urls.py --check "https://exercism.org/tracks/python"

# Validate a full syllabus
python3 scripts/validate_urls.py --http --file syllabus.json

# Or via stdin
cat syllabus.json | python3 scripts/validate_urls.py --http
```

This is manual CLI testing, not automated tests.

## Test Coverage

**Automated Coverage:** 0% -- no test framework or test files exist.

**What IS tested manually:**
- The Python scripts (`init_db.py`, `migrate_db.py`, `validate_urls.py`) can be run directly
- `init_db.py` is idempotent by design (runs on every cron invocation)
- `migrate_db.py` handles edge cases (version too new, version too old, duplicate columns)
- `validate_urls.py` has three input modes (single URL, file, stdin)

**What is NOT tested at all:**
- Subskill prompt logic (all 4 subskills: `init.md`, `daily.md`, `eval.md`, `adapt.md`)
- Template rendering
- Command routing in SKILL.md
- State transitions (module lifecycle, path lifecycle)
- Cron job behavior (zero-context session handling)
- Evaluation JSON parsing and decision rules
- Inactivity escalation logic
- Spaced repetition scheduling
- The LLM evaluation quality itself

## CI/CD Integration

**No CI pipeline exists.** There are:
- No `.github/workflows/` directory
- No `.gitlab-ci.yml`
- No `Jenkinsfile`
- No `Makefile` or `justfile` with test targets
- No pre-commit hooks

## Testing Gap Analysis

### Critical Gaps (High Priority)

**Python Scripts:**
- `validate_urls.py` is the most testable component -- pure functions with clear inputs/outputs. No automated tests exist despite CONTRIBUTING.md referencing `test_validate_urls.py`.
- `init_db.py` -- no tests for table creation, idempotency, default config values
- `migrate_db.py` -- no tests for version comparison, migration application, error handling

### Structural Gaps (Medium Priority)

**Subskill Prompt Testing:**
- No way to automate testing of LLM prompt behavior
- The evaluation flow (eval.md) is the most complex and error-prone -- JSON parsing failures, edge case scoring
- Cron prompts are not validated after subskill edits (must be manually recreated)

**State Machine Testing:**
- Module status lifecycle (pending -> in_progress -> completed, with decompose branch)
- Path status lifecycle (active -> paused -> completed)
- Config key management (active_path_id, pending_task_id, etc.)

### Difficult to Test (Low Priority / Acknowledged)

**LLM Behavior:**
- Syllabus quality depends on web search results and model capability
- Evaluation scoring is subjective and model-dependent
- URL hallucination cannot be fully prevented

## Recommendations for Adding Tests

**Highest ROI -- `validate_urls.py` unit tests:**
```python
# tests/test_validate_urls.py
import pytest
from scripts.validate_urls import classify_url, validate_single

def test_reject_youtube_playlist():
    result = classify_url("https://youtube.com/watch?v=abc&list=def")
    assert result == (None, "YouTube PLAYLIST - not allowed")

def test_accept_youtube_single():
    result = classify_url("https://youtube.com/watch?v=abc123")
    assert result[0] == 3

def test_classify_tier1_exercism():
    result = classify_url("https://exercism.org/tracks/python")
    assert result[0] == 1

def test_classify_tier2_coursera():
    result = classify_url("https://coursera.org/learn/python")
    assert result[0] == 2
```

**Database script tests:**
```python
# tests/test_init_db.py
import sqlite3, tempfile, os
from scripts.init_db import init_db

def test_idempotent():
    """Running twice should not raise or duplicate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch db_path to tmpdir
        init_db()  # first run
        init_db()  # second run -- should succeed
```

**Migration tests:**
```python
# tests/test_migrate_db.py
def test_migration_from_v0_to_v1():
    """Test fresh DB gets schema_version set to 1."""
    ...

def test_skip_if_already_at_expected_version():
    """Running at current version should exit early."""
    ...
```

## Test Infrastructure Needed

To add automated testing, the project needs:

1. **Test runner:** `pytest` (already referenced in CONTRIBUTING.md)
2. **Test dependencies file:** `requirements-dev.txt` or `[dev-dependencies]` in a `pyproject.toml`
3. **Test directory:** `tests/` at project root (standard pytest convention)
4. **CI pipeline:** GitHub Actions workflow to run tests on push/PR
5. **Test fixtures:** Sample syllabus JSON, temporary DB files for migration tests

---

*Testing analysis: 2026-04-12*
