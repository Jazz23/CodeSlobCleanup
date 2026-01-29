# Slob Detection: Static Analysis Phase 2 (Orchestration)

## Current Focus
Develop the orchestration layer to scan directories, report results, and verify the end-to-end flow.

1.  **Orchestration System**
    *   [x] Implement `scan_directory` in `orchestrator.py` to recursively find `.py` files using `pathlib`.
    *   [x] Integrate `metrics.py` (from Phase 1) to process each file.
    *   [x] Handle exclusions (e.g., `venv`, `tests`, `__pycache__`).

2.  **Reporting Engine**
    *   [x] Implement JSON report generation (`scan_report.json`) with the following schema:
        ```json
        {
          "files_scanned": 15,
          "slob_candidates": [
            {
              "file": "legacy/utils.py",
              "function": "process_all_items",
              "line": 42,
              "metrics": { "complexity": 15, "loc": 85, "slob_score": 65 },
              "high_severity": true
            }
          ]
        }
        ```
    *   [x] Build CLI interface for usage: `uv run scan_slob.py --target ./src --output report.json`.

3.  **Integration Testing**
    *   [x] Create `test_scanner_orchestrator.py` to verify end-to-end scanning.
    *   [x] Test case: Scan a temporary directory with one "clean" and one "slob" file.
    *   [x] Assert that the "slob" file appears in `slob_candidates`.

4.  **End-to-End Verification**
    *   [x] Run scanner against a fixture directory and assert JSON output schema validity.
    *   [x] Verify performance: Scan should complete in < 2 seconds for small codebases (< 100 files).
