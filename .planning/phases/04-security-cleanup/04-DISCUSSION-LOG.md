# Phase 4: Security Cleanup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-13
**Phase:** 04-security-cleanup
**Areas discussed:** Purge tool, Branch scope, Pre-purge backup, Remote sync

---

## Gray Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Purge tool | git filter-repo vs BFG vs git filter-branch | ✓ (via recommendation) |
| Branch scope | All branches vs master only | ✓ (via recommendation) |
| Pre-purge backup | git bundle backup before rewriting | ✓ (via recommendation) |
| Remote sync | When and how to force-push to origin | ✓ |

**User's initial question:** "Which one is recommended? Are all 4 necessary? I want to push to remote, but not yet to master. Or is it recommended?"

---

## Purge Tool

| Option | Description | Selected |
|--------|-------------|----------|
| git filter-repo | Modern, Git-recommended, handles --all in one pass | ✓ |
| BFG Repo Cleaner | Fast but requires Java | |
| git filter-branch | Deprecated, slow | |

**User's choice:** git filter-repo (accepted recommendation)
**Notes:** No real alternative — tool choice was effectively settled by recommendation.

---

## Branch Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All branches (--all) | Rewrites every branch and tag in one pass | ✓ |
| master only | Leaves feature branches carrying the blob | |

**User's choice:** All branches (accepted recommendation)
**Notes:** Skipping any branch leaves the blob recoverable from that ref.

---

## Pre-Purge Backup

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — git bundle --all | Full recovery point before destructive rewrite | ✓ |
| No backup | Faster but no recovery path | |

**User's choice:** Yes (accepted recommendation)
**Notes:** Backup stored outside the repo directory to prevent accidental commit.

---

## Remote Sync

| Option | Description | Selected |
|--------|-------------|----------|
| Option A — Merge first, then purge everything | Merge gsd-experiment → master, then rewrite all + force-push all | ✓ |
| Option B — Purge local + remote non-master now, master later | Partially clean; origin/master still carries blob | |
| Option C — Purge and push all branches including master now | Immediate full cleanup without merge prerequisite | |

**User's choice:** Option A
**Notes:** User wanted to push to remote but not master; discussion clarified that for complete security, all branches including master must be rewritten. Option A satisfies this while preserving a clean merge workflow.

---

## Claude's Discretion

- Whether to delete stale remote feature branches after purge (cosmetic, not required for SEC-03)
- Whether to add `.gitattributes` belt-and-suspenders entry for `learning.db`

## Deferred Ideas

- GitHub Support GC request for immediate remote garbage collection (low-risk for private repo)
- Stale remote branch cleanup (cosmetic, separate from security requirement)
