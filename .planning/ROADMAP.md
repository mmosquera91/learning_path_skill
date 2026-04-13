# Roadmap: Tutor Skill Hardening

## Milestones

- **v1.0 MVP** - Phases 1-4 (shipped 2026-04-13)
- **v1.1 Usability & Upgrade Path** - Phases 5-6 (in progress)
- **v2.0 Future** - Not yet planned

## Phases

<details>
<summary>v1.0 MVP (Phases 1-4) - SHIPPED 2026-04-13</summary>

- [x] **Phase 1: Foundation** - Schema alignment, test suite, input validation, and SQL safety
- [x] **Phase 2: Code Quality** - Tier rule deduplication and context budget reduction
- [x] **Phase 3: Correctness** - Template syntax fixes, error handling, and command format corrections
- [x] **Phase 4: Security Cleanup** - Git history purge

</details>

---

### v1.1 Usability & Upgrade Path

**Milestone Goal:** Make the project usable for new adopters and safe for existing users upgrading from v1.0.

---

- [ ] **Phase 5: README Redesign** - Audit and rewrite README.md to accurately reflect current implementation
- [x] **Phase 6: Upgrade Path** - Wire migration into init flow and document upgrade path for existing users (completed 2026-04-13)

## Phase Details

### Phase 5: README Redesign
**Goal**: Audit and rewrite README.md to accurately reflect current implementation. Remove untested claims, fix setup instructions, add real example session.
**Depends on**: Nothing
**Requirements**: README-01, README-02
**Success Criteria** (what must be TRUE):
  1. README.md mentions only features that are actually implemented and tested
  2. Setup instructions match actual `hermes skills install` workflow
  3. Example session reflects actual `/tutor init` -> `/tutor daily` -> `/tutor eval` flow
  4. Command formats (e.g., `/tutor confirm`, `/tutor edit`) match actual SKILL.md
**Plans**: 1 plan
- [x] 05-01-PLAN.md — Audit README.md against source files and rewrite with all corrections

### Phase 6: Upgrade Path
**Goal**: Wire migration into init flow and document upgrade path for existing users.
**Depends on**: Phase 5
**Requirements**: MIGRATE-01, UPGRADE-01, UPGRADE-02
**Success Criteria** (what must be TRUE):
  1. `python3 scripts/migrate_db.py --check` is called in init.md Step 0 before init_db.py
  2. Existing users upgrading from v1.0 see migration run automatically on first /tutor init
  3. Upgrade path documented in README.md (what to expect, what is preserved)
  4. End-to-end test confirms schema v1 -> v2 migration preserves all data
**Plans**: 1 plan
- [x] 06-01-PLAN.md — Wire migrate --check into init, add tests, document upgrade path

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-04-13 |
| 2. Code Quality | v1.0 | 4/4 | Complete | 2026-04-13 |
| 3. Correctness | v1.0 | 4/4 | Complete | 2026-04-13 |
| 4. Security Cleanup | v1.0 | 1/1 | Complete | 2026-04-13 |
| 5. README Redesign | v1.1 | 0/1 | Not started | - |
| 6. Upgrade Path | v1.1 | 1/1 | Complete    | 2026-04-13 |
