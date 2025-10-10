# SingleFile Archiver - Agent Coordination Document

## Top TODO

- [ ] **Scaffold AGENTS.md framework with Top TODO, Definitions, and Replan sections** (≤1h)
  - **Acceptance Criteria**: Complete AGENTS.md structure with all required sections
  - **Verification**: Review document structure and section completeness

- [ ] **Create docs/stack-fingerprint.md with tech stack detection and tooling commands** (≤1h)
  - **Acceptance Criteria**: Document includes Python stack, testing/linting commands, and dependency analysis
  - **Verification**: Validate all listed commands execute successfully

- [ ] **Create FEATURE_SPEC.md for filename optimization requirements** (≤1h)
  - **Acceptance Criteria**: Comprehensive spec with problem statement, constraints, acceptance criteria
  - **Verification**: Spec covers all three requirements: length control, emoji removal, batch processing

- [ ] **Implement filename length control and emoji removal functions** (≤1h)
  - **Acceptance Criteria**: Functions handle length truncation with ellipsis and remove emoji characters
  - **Verification**: Unit tests pass and manual verification with sample filenames

## Definitions

- **FWU (Feature Work Unit)**: A single deliverable completable in ≤1 day with clear acceptance criteria
- **BRM (Blast Radius Map)**: Impact analysis of modules, interfaces, and dependencies affected by changes
- **Invariants & Contracts**: Interface/behavior constraints that must remain valid after modifications
- **Touch Budget**: Whitelist of files/directories authorized for modification with defined scope limits
- **FF (Feature Flag)**: Runtime toggle mechanism for new functionality, defaulting to disabled state
- **Kill Switch**: Emergency rollback mechanism for immediate feature disabling
- **Savepoint Tag**: Git lightweight tag following `savepoint/<yyyy-mm-dd>-<feature-slug>` pattern
- **DoR/DoD**: Definition of Ready/Done checklists for implementation gates

## Blast Radius Map (BRM)

### Affected Modules
- `src/singlefile_archiver/utils/paths.py` - Core filename processing utilities
- `src/singlefile_archiver/services/docker_service.py` - Filename generation logic
- `src/singlefile_archiver/core/archive.py` - Archive file handling

### Touch Budget
**Authorized for modification:**
- `src/singlefile_archiver/utils/paths.py` (add new functions, modify existing)
- `src/singlefile_archiver/services/docker_service.py` (update filename logic)
- `docs/` directory (create new documentation)
- `tests/` directory (add new test cases)

**Maximum scope:** ≤5 files, ≤200 lines of changes

## Invariants & Contracts

1. **Filename Safety**: All generated filenames must remain filesystem-safe across platforms
2. **URL Compatibility**: Existing URL encoding functionality must be preserved
3. **Backward Compatibility**: Existing archived files must remain accessible
4. **Docker Integration**: Container functionality must not be disrupted
5. **CLI Interface**: Command-line interface must remain stable

## Feature Flags

- `FF_FILENAME_OPTIMIZATION`: Controls new filename processing features (default: False)
- `FF_BATCH_PROCESSING`: Enables batch file renaming functionality (default: False)

## Replan

### Current Status
- ✅ Git savepoint and feature branch created
- 🔄 AGENTS.md framework scaffolding in progress
- ⏳ Stack detection and documentation pending

### Next Actions
1. Complete AGENTS.md structure
2. Detect and document technical stack
3. Create comprehensive feature specification
4. Implement core filename optimization functions

### Blockers
- None identified

### Decisions Made
- Use Feature Flags for safe rollout
- Implement in dedicated feature branch
- Maintain backward compatibility

## Run Log

- 2025-10-10 16:56:34 +1100 — created/switch branch `feat/filename-optimization` at `85dcc15`; created tag `savepoint/2025-10-10-filename-optimization`; pushed branch and tags to `origin` (https://github.com/APE-147/singlefile-archiver.git).
- 2025-10-10 17:15:22 +1100 — implemented complete filename optimization suite: emoji removal, length control, Feature Flags (FF_FILENAME_OPTIMIZATION, FF_BATCH_PROCESSING), batch processing commands, updated DockerService integration, created comprehensive documentation and test suite. Commit `16f2b51` with 7 files changed, 1329 insertions.

