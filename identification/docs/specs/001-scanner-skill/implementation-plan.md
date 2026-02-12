# Implementation Plan: Scanner Skill (Identification)

## Validation Checklist

- [ ] All specification file paths are correct and exist
- [ ] Context priming section is complete
- [ ] All implementation phases are defined
- [ ] Each phase follows TDD: Prime → Test → Implement → Validate
- [ ] Dependencies between phases are clear
- [ ] Parallel work is properly tagged with `[parallel: true]`
- [ ] Every phase references relevant SDD sections
- [ ] Project commands match actual project setup (`uv run ...`)

---

## Context Priming

*GATE: You MUST fully read all files mentioned in this section before starting any implementation.*

**Specification**:
- Project Overview `[ref: GEMINI.md]`
- Verifier Skill Plan (as reference for structure) `[ref: verification/docs/specs/001-verifier-skill/implementation-plan.md]`

**Key Design Decisions**:
- **Hybrid Detection**: 
    1. **Fast Filter (Static)**: Use AST/Metrics (Radon) to identify high-complexity candidates.
    2. **Smart Filter (Semantic)**: Use LLM (via Gemini) to confirm "slob" vs. "just complex".
- **Output Standard**: The scanner produces a `scan_report.json` listing candidates with scores.
- **Dependency Isolation**: Use `uv` for all dependencies.
- **Fixture Reuse**: Reuse `verification/tests/fixtures` where applicable, but create specific "slob detection" fixtures.

**Implementation Context**:
- **Tools**: `uv`, `pytest`, `radon`, `ast`.
- **Paths**:
    - Skill: `identification/.gemini/skills/scanner/`
    - Source: `identification/src/`
    - Tests: `identification/tests/`

---

## Implementation Phases

- [x] S1 Phase 1: Infrastructure & Static Analysis Core
    *Goal: Build the engine that can calculate complexity metrics for Python files.*

    - [x] S1.1 Prime Context
        - [x] S1.1.1 Review `verification/tests/fixtures` to identify suitable test cases `[ref: verification/tests/fixtures]`
    - [x] S1.2 Write Tests
        - [x] S1.2.1 Create `identification/tests/unit/test_metrics.py` `[activity: testing]`
        - [x] S1.2.2 Define `test_cyclomatic_complexity`: Assert highly nested code scores high.
        - [x] S1.2.3 Define `test_function_length`: Assert long functions are flagged.
    - [x] S1.3 Implement
        - [x] S1.3.1 Initialize `identification/src/scanner/metrics.py` `[activity: backend]`
        - [x] S1.3.2 Implement `calculate_metrics(file_path)` using `radon` or AST traversal `[activity: backend]`
        - [x] S1.3.3 Implement `is_slob_candidate(metrics)` heuristic logic `[activity: backend]`
    - [x] S1.4 Validate
        - [x] S1.4.1 Run unit tests: `uv run pytest identification/tests/unit/` `[activity: run-tests]`

- [ ] S2 Phase 2: Orchestrator & Reporting
    *Goal: Scan a directory and output a JSON report of candidates.*

    - [ ] S2.1 Prime Context
        - [ ] S2.1.1 Review `verification/scripts/orchestrator.py` for design consistency `[ref: verification/scripts/orchestrator.py]`
    - [ ] S2.2 Write Tests
        - [ ] S2.2.1 Create `identification/tests/integration/test_scanner_orchestrator.py` `[activity: testing]`
        - [ ] S2.2.2 Define `test_scan_directory`: Run against a fixture dir and check JSON output.
    - [ ] S2.3 Implement
        - [ ] S2.3.1 Create `identification/src/scanner/orchestrator.py` `[activity: backend]`
        - [ ] S2.3.2 Implement CLI interface (`--target-dir`) `[activity: backend]`
        - [ ] S2.3.3 Implement file walking and parallel processing `[activity: backend]`
        - [ ] S2.3.4 Implement JSON report generation `[activity: backend]`
    - [ ] S2.4 Validate
        - [ ] S2.4.1 Run integration tests `[activity: run-tests]`

- [ ] S3 Phase 3: Skill Definition
    *Goal: Wrap the scanner as a Gemini Skill.*

    - [ ] S3.1 Prime Context
        - [ ] S3.1.1 Review `.gemini/skills/cse247b/SKILL.md` `[ref: .gemini/skills/cse247b/SKILL.md]`
    - [ ] S3.2 Implement
        - [ ] S3.2.1 Create `identification/.gemini/skills/scanner/SKILL.md` `[activity: docs]`
        - [ ] S3.2.2 Define usage instructions for the Agent `[activity: docs]`
        - [ ] S3.2.3 Link to `verification` skill for the "next step" (once identified -> verify refactor) `[activity: docs]`
    - [ ] S3.3 Validate
        - [ ] S3.3.1 Manual review of SKILL.md `[activity: review]`

- [ ] S4 Phase 4: Semantic Analysis (LLM Integration) [OPTIONAL/FUTURE]
    *Goal: Add a second pass where an LLM reviews candidates to reduce false positives.*
    *(Deferred to a later sprint to focus on getting the static pipeline working first)*
