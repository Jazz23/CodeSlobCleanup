# Slob Detection: Static Analysis Infrastructure

## Current Focus
Establish the core infrastructure for calculating Python code metrics to identify "Code Slob" candidates.

1.  **Metric Calculation Core**
    *   [x] Implement `calculate_complexity` using `radon` to visit AST blocks.
    *   [x] Implement `calculate_loc` to measure Logical Lines of Code (LLOC).
    *   [x] Implement `calculate_halstead` to measure code effort.
    *   [x] Implement `calculate_slob_score` using a heuristic (Complexity, LLOC).

2.  **Unit Testing**
    *   [x] Create `test_metrics.py` with test cases for simple and nested logic.
    *   [x] Verify `test_cyclomatic_complexity` triggers correctly for nested functions.
    *   [x] Verify `test_function_length` flags long functions.
    *   [x] Verify `test_slob_score_heuristic` ranks "slobbier" code higher.

3.  **Orchestration & Reporting**
    *   [x] Implement `scan_directory` in `orchestrator.py` to recursively find `.py` files.
    *   [x] Integrate `metrics.py` into the orchestrator.
    *   [x] Implement JSON report generation (`scan_report.json`).
    *   [x] Build CLI interface for `--target-dir` input.

4.  **Integration Testing**
    *   [x] Create `test_scanner_orchestrator.py` to verify end-to-end scanning.
    *   [x] Run scanner against a fixture directory and assert JSON output schema.
