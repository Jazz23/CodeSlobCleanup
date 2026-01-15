# Implementation Plan: Verifier Skill

## Validation Checklist

- [ ] All specification file paths are correct and exist
- [ ] Context priming section is complete
- [ ] All implementation phases are defined
- [ ] Each phase follows TDD: Prime → Test → Implement → Validate
- [ ] Dependencies between phases are clear (no circular dependencies)
- [ ] Parallel work is properly tagged with `[parallel: true]`
- [ ] Activity hints provided for specialist selection `[activity: type]`
- [ ] Every phase references relevant SDD sections
- [ ] Every test references PRD acceptance criteria
- [ ] Integration & E2E tests defined in final phase
- [ ] Project commands match actual project setup
- [ ] A developer could follow this plan independently

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:
- User Prompt (Code Slob Cleanup - Verifier Skill) `[ref: Chat History]`
- `verification/tools/common.py` - Existing logic to adapt `[ref: verification/tools/common.py]`

**Key Design Decisions**:
- **Decoupled Architecture**: The skill must run on any directory provided via CLI (`--target-dir`), not hardcoded paths.
- **Fixture-Based Testing**: Use snapshots of "original/refactored" pairs in `tests/fixtures/` to simulate the Refactor Agent's output.
- **Orchestrator Pattern**: A master script (`orchestrator.py`) manages the workflow: scan -> verify -> report.
- **Contract**: Input directory contains job subfolders. Output is a `verification_report.json` in each job folder.

**Implementation Context**:
- **Tools**: `uv`, `pytest`.
- **Paths**:
    - Skill: `verification/.gemini/skills/verifier/`
    - Tests: `verification/tests/integration/`
    - Fixtures: `verification/tests/fixtures/`

---

## Implementation Phases

- [x] T1 Phase 1: Infrastructure & Fixtures
    *Goal: Establish the test data and directory structure needed for independent development.*

    - [x] T1.1 Prime Context
        - [x] T1.1.1 Analyze current `verification/src` structure `[ref: verification/src]`
    - [x] T1.2 Write Tests (Fixture Validation)
        - [x] T1.2.1 Create a test that verifies fixtures exist and have correct structure `[activity: testing]`
    - [x] T1.3 Implement
        - [x] T1.3.1 Create `verification/tests/fixtures/` directory structure `[activity: infra]`
        - [x] T1.3.2 Move existing examples (`complex_args.py`, etc.) from `verification/src` to `verification/tests/fixtures/scenario_valid/` `[activity: refactor]`
        - [x] T1.3.3 Create `tests/fixtures/scenario_broken/` with intentionally buggy refactoring `[activity: testing]`
    - [x] T1.4 Validate
        - [x] T1.4.1 Run fixture validation test `[activity: run-tests]`

- [x] T2 Phase 2: Orchestrator Core
    *Goal: Build the script that scans directories and delegates work to existing tools.*

    - [x] T2.1 Prime Context
        - [x] T2.1.1 Review `verification/tools/generic_verify.py` interface `[ref: verification/tools/generic_verify.py]`
    - [x] T2.2 Write Tests
        - [x] T2.2.1 Create `verification/tests/integration/test_orchestrator.py` `[activity: testing]`
        - [x] T2.2.2 Define test: `test_orchestrator_finds_jobs` (mocks file system)
        - [x] T2.2.3 Define test: `test_orchestrator_runs_verification` (mocks subprocess calls)
    - [x] T2.3 Implement
        - [x] T2.3.1 Create `verification/.gemini/skills/verifier/orchestrator.py` skeleton `[activity: backend]`
        - [x] T2.3.2 Implement CLI argument parsing (`--target-dir`) `[activity: backend]`
        - [x] T2.3.3 Implement job scanning logic (find subfolders with `original.py`/`refactored.py`) `[activity: backend]`
        - [x] T2.3.4 Implement execution logic (call `uv run ... generic_verify.py`) `[activity: backend]`
        - [x] T2.3.5 Implement reporting (write `verification_report.json`) `[activity: backend]`
    - [x] T2.4 Validate
        - [x] T2.4.1 Run `test_orchestrator.py` `[activity: run-tests]`

- [x] T3 Phase 3: Skill Definition
    *Goal: Wrap the orchestrator in the Agent Skill format.*

    - [x] T3.1 Prime Context
        - [x] T3.1.1 Review `.gemini/skills/cse247b/SKILL.md` as reference `[ref: .gemini/skills/cse247b/SKILL.md]`
    - [x] T3.2 Implement
        - [x] T3.2.1 Create `verification/.gemini/skills/verifier/SKILL.md` `[activity: docs]`
        - [x] T3.2.2 Define `<INSTRUCTIONS>` for the Agent (how to use the orchestrator) `[activity: docs]`
    - [x] T3.3 Validate
        - [x] T3.3.1 Manual check: Ensure SKILL.md paths are correct `[activity: review]`

- [x] T4 Phase 4: Integration & End-to-End Validation
    *Goal: Verify the entire flow simulates the real pipeline.*

    - [x] T4.1 Prime Context
        - [x] T4.1.1 Review "The Automated Test Suite" section from chat plan `[ref: Chat History]`
    - [x] T4.2 Write Tests
        - [x] T4.2.1 Create `verification/tests/integration/test_skill_flow.py` `[activity: testing]`
        - [x] T4.2.2 Define `test_skill_success_cases`: Copy valid fixture -> Run Orchestrator -> Assert Pass `[activity: testing]`
        - [x] T4.2.3 Define `test_skill_catches_regression`: Copy broken fixture -> Run Orchestrator -> Assert Fail `[activity: testing]`
    - [x] T4.3 Implement
        - [x] T4.3.1 Finalize `verification/tests/integration/test_skill_flow.py` implementation `[activity: testing]`
    - [x] T4.4 Validate
        - [x] T4.4.1 Run full suite: `uv run pytest verification/tests/integration/` `[activity: run-tests]`
        - [x] T4.4.2 Ensure `verification/tools` are still working (regression check) `[activity: run-tests]`

