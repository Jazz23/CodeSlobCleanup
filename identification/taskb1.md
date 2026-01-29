# Slob Detection: Static Analysis Phase 1 (Metrics & Logic)

## Current Focus
Establish the core infrastructure for calculating Python code metrics and validating them with unit tests.

1.  **Metric Calculation Core**
    *   [x] Implement `calculate_complexity` using the `radon` library.
        *   [x] Use `radon.complexity.cc_visit` to get Cyclomatic Complexity.
        *   [x] Target Threshold: Complexity > 10.
    *   [x] Implement `calculate_loc` to measure Logical Lines of Code (LLOC).
        *   [x] Strip comments and docstrings before counting.
    *   [x] Implement `calculate_halstead` to measure code effort (vocabulary, volume, difficulty).

2.  **Slob Score Heuristic**
    *   [x] Implement `calculate_slob_score` using a composite heuristic.
    *   [x] Formula Proposal: `SlobScore = (Complexity / 10) + (LLOC / 50) + (ArgCount / 5)`.
    *   [x] Normalize score to a 0-100 scale where > 50 indicates "High Slob".

3.  **Unit Testing Framework**
    *   [x] Create `test_metrics.py` using `pytest`.
    *   [x] Include fixtures for:
        *   [x] Simple flat functions (Score < 10).
        *   [x] Deeply nested "spaghetti" logic (Score > 50).
        *   [x] Large classes with many methods.

4.  **Metric Verification**
    *   [x] Verify `test_cyclomatic_complexity` triggers correctly for nested functions.
    *   [x] Verify `test_function_length` flags long functions (e.g., > 50 lines).
    *   [x] Verify `test_slob_score_heuristic` ranks "slobbier" code higher than clean code.
