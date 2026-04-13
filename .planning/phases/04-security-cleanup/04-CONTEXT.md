# Phase 4: Security Cleanup - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Purge `learning.db` from every commit across all git history — local and all remote branches — so no recoverable blob exists anywhere. This is a destructive, one-way operation that rewrites git history.

Requirement: SEC-03

</domain>

<decisions>
## Implementation Decisions

### Purge Tool
- **D-11:** Use `git filter-repo` — the tool recommended by Git itself. BFG requires Java; `git filter-branch` is deprecated and slow. `git filter-repo` handles the full rewrite in one pass.

### Branch Scope
- **D-12:** Rewrite ALL branches (`--all` flag). The 3 commits carrying `learning.db` appear across local and remote branches. Skipping any branch leaves the blob recoverable from that ref.

### Pre-Purge Backup
- **D-13:** Create a full bundle backup before rewriting: `git bundle create backup-before-purge.bundle --all`. Stored locally (not committed). Gives a complete recovery point if something goes wrong.

### Remote Sync Strategy
- **D-14:** **Option A — Merge first, then purge everything.** Merge `gsd-experiment` into `master` locally before running the purge. Then rewrite all history and force-push ALL branches to `origin`. One clean operation, complete security fix.
- **D-15:** After force-push, GitHub may cache old objects briefly before their garbage collector runs. For a private repo this is low-risk. GitHub Support can be contacted to force-GC if immediate cleanup is required.

### Sequence
The plan for 04-01 must follow this order:
1. Ensure `gsd-experiment` is merged into `master`
2. Create git bundle backup
3. Run `git filter-repo --path learning.db --invert-paths`
4. Verify success criteria locally
5. Force-push ALL refs to `origin` (`git push --force --all origin`)
6. Force-push all tags (`git push --force --tags origin`)
7. Run local `git gc --prune=now` to remove dangling objects

### Claude's Discretion
- Whether to also delete old remote feature branches (feature/trusted-sources-syllabus, fix/cron-silent-no-path, etc.) after the purge — stale branches add noise but removal is optional
- Whether to add `.gitattributes` with `learning.db filter=` to prevent future accidental commits (belt-and-suspenders beyond `.gitignore`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Security Requirement
- `.planning/REQUIREMENTS.md` §SEC-03 — "learning.db is purged from all git history (no recoverable blob)"
- `.planning/PROJECT.md` Key Decisions table — "Purge learning.db from git history" decision + rationale

### Current State
- Three commits carrying the blob: `dd3918f`, `f2ff73d`, `ffa02d7` (verified via `git log --all --diff-filter=A -- learning.db`)
- Remote: `origin` on GitHub — carries the same history; force-push required after rewrite
- `.gitignore` already lists `learning.db` — prevents future commits but didn't catch past ones

### Success Criteria (from ROADMAP.md)
1. `git log --all --diff-filter=A -- learning.db` returns no results
2. `git rev-list --all -- learning.db | xargs git grep -l` returns no results (no blob contains the file)

### Tool Reference
- `git filter-repo` — https://github.com/newren/git-filter-repo (install via `pip install git-filter-repo` or system package)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this phase is pure git history rewriting, no code changes

### Established Patterns
- `.gitignore` already has `learning.db` listed — the safety net for future commits is in place
- All previous phase commits are on `gsd-experiment` branch; merge to `master` is the prerequisite

### Integration Points
- After force-push, any collaborator clones would need to re-clone (single-user project, not a concern here)
- `gsd-experiment` branch must be merged into `master` before the purge runs — this is a prerequisite step within the plan

</code_context>

<specifics>
## Specific Ideas

- The merge of `gsd-experiment` → `master` is a prerequisite step that the planner should include as Step 1 of the plan (not a separate task)
- The backup bundle (`backup-before-purge.bundle`) should be stored outside the repo directory to avoid any risk of accidental commit

</specifics>

<deferred>
## Deferred Ideas

- GitHub Support GC request — only needed if immediate remote cleanup is critical. Low-risk for a private repo; skip unless the user needs it.
- Deleting stale remote feature branches — cosmetic cleanup, not required for SEC-03

</deferred>

---
*Phase: 04-security-cleanup*
*Context gathered: 2026-04-13*
