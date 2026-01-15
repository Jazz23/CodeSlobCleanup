# Implementation Plan - Automated Code Refactoring

This plan outlines the implementation of an automated feedback loop for refactoring functions that fail verification or demonstrate poor performance (speedup < 0.4x).

## Validation Checklist

- [x] All specification file paths are correct and exist
- [x] Context priming section is complete
- [x] All implementation phases are defined
- [x] Each phase follows TDD: Prime → Test → Implement → Validate
- [x] Dependencies between phases are clear (no circular dependencies)
- [x] Parallel work is properly tagged with `[parallel: true]`
- [x] Activity hints provided for specialist selection `[activity: type]`
- [x] Every phase references relevant SDD sections
- [ ] Every test references PRD acceptance criteria
- [x] Integration & E2E tests defined in final phase
- [x] Project commands match actual project setup
- [x] A developer could follow this plan independently

---

## Specification Compliance Guidelines

### How to Ensure Specification Adherence

1. **Before Each Phase**: Complete the Pre-Implementation Specification Gate
2. **During Implementation**: Reference specific SDD sections in each task
3. **After Each Task**: Run Specification Compliance checks
4. **Phase Completion**: Verify all specification requirements are met

## Metadata Reference

- `[parallel: true]` - Tasks that can run concurrently
- `[component: component-name]` - For multi-component features
- `[ref: document/section; lines: 1, 2-3]` - Links to specifications
- `[activity: type]` - Activity hint for specialist agent selection

---

## Context Priming

**Specification**:
- `GEMINI.md` - Core project mandates (PEP 723, uv run)
- `verification/.gemini/skills/verifier/verifier.md` - Current skill definition

**Key Design Decisions**:
- **Trigger Condition A**: Behavioral mismatch (AssertionError/Exception in `verify.py`).
- **Trigger Condition B**: Performance regression (Speedup < 0.4x in `benchmark.py`).
- **Mechanism**: A new script `correct_refactor.py` that utilizes LLM feedback to iterate on `refactored.py`.
- **Integration**: `orchestrator.py` will optionally invoke the correction loop.

**Implementation Context**:
- Commands to run: `uv run verification/tests/run_tests.py`
- Patterns: LLM Feedback Loop (Prompt → Error Output → Corrected Code)

---

## Implementation Phases

### Phase 1: Correction Engine (`correct_refactor.py`)

- [ ] T1.1 Prime Context
    - [ ] T1.1.1 Review `orchestrator.py` result parsing logic. `[ref: orchestrator.py]` `[activity: research]`
- [ ] T1.2 Write Tests
    - [ ] T1.2.1 Create a unit test that mocks an LLM response for a known failing function (e.g., `custom_power`) and verifies that `refactored.py` is updated. `[activity: testing]`
- [ ] T1.3 Implement
    - [ ] T1.3.1 Create `verification/.gemini/skills/verifier/scripts/correct_refactor.py`.
    - [ ] T1.3.2 Implement LLM prompt construction using: Original Code, Current Refactor, and Failure Logs/Speedup data.
    - [ ] T1.3.3 Implement file-writing logic to replace `refactored.py` with the corrected version.
- [ ] T1.4 Validate
    - [ ] T1.4.1 Run the unit test. `[activity: run-tests]`

### Phase 2: Orchestrator Integration

- [ ] T2.1 Prime Context
    - [ ] T2.1.1 Review `orchestrator.py` main loop. `[activity: research]`
- [ ] T2.2 Write Tests
    - [ ] T2.2.1 Add an integration test in `test_orchestrator.py` that passes a `--auto-refactor` flag and ensures the correction script is called on failure. `[activity: testing]`
- [ ] T2.3 Implement
    - [ ] T2.3.1 Add `--auto-refactor` flag to `orchestrator.py`.
    - [ ] T2.3.2 Add logic to check `Speedup < 0.4` and call `correct_refactor.py`.
    - [ ] T2.3.3 Add logic to check `status == "FAIL"` and call `correct_refactor.py`.
- [ ] T2.4 Validate
    - [ ] T2.4.1 Run full integration suite. `[activity: run-tests]`

### Phase 3: Skill & Documentation Update

- [ ] T3.1 Prime Context
    - [ ] T3.1.1 Review `verifier.md`.
- [ ] T3.2 Implement
    - [ ] T3.2.1 Update `verifier.md` to include instructions for using `--auto-refactor`.
- [ ] T3.3 Validate
    - [ ] T3.3.1 Verify markdown formatting and clarity. `[activity: review]`

### Phase 4: Integration & End-to-End Validation

- [ ] T4.1 [All unit tests passing]
- [ ] T4.2 [Integration tests for auto-refactor flow passing]
- [ ] T4.3 [Verify that multiple iterations can occur if the first correction still fails]
- [ ] T4.4 [Verify that PEP 723 metadata is preserved in all scripts]
- [ ] T4.5 [Final run on scenario_broken to see auto-correction in action]
