# Scripts Reference

The **Code Slob Cleanup** project relies on several key Python scripts to automate the identification, verification, and cleaning of code. All scripts are ran using `uv run`.

## `scripts/identify.py`

This script is the entry point for finding "code slob" in your repository.

- **Usage**: `uv run scripts/identify.py --target-dir <directory>`
- **Functionality**: 
    - Scans the target directory for Python files.
    - Calculates static metrics (Cyclomatic Complexity, LOC) for each function.
    - Outputs a report of candidate functions for refactoring.
    - Respects exclusions defined in `code-slob-cleanup.json` and inline comments.

## `scripts/orchestrator.py`

This script manages the verification process within the `.code-slob-tmp/` workspace.

- **Usage**: `uv run scripts/orchestrator.py .code-slob-tmp`
- **Functionality**:
    - Discovers all refactoring "jobs" in the temporary directory.
    - Executes `scripts/verify.py` for each job.
    - Collects and aggregates results (Pass/Fail/Skip).
    - Benchmarks performance of Original vs Refactored code.
    - Summarizes the overall verification status.

## `scripts/clean_untested.py`

This script allows you to remove code that is not covered by a specific "golden" test suite.

- **Usage**: `uv run scripts/clean_untested.py <test_script_path>`
- **Functionality**:
    - Runs the provided test script under `coverage`.
    - Identifies all functions in the codebase that were NOT executed during the test.
    - Automatically removes these functions from the source code.
    - **CAUTION**: Use this script with care, as it will permanently delete code that it deems "unreachable" according to your test suite. It respects exclusions in `code-slob-cleanup.json` and inline comments.

## Other Utility Scripts

- **`scripts/verify.py`**: The core script for running Hypothesis-based property testing on a single function (called by `orchestrator.py`).
- **`scripts/metrics.py`**: Provides the static analysis tools (like Radon) used by `identify.py`.
- **`scripts/semantic.py`**: Identifies global variables, classes that should have their own files, and functions that should be private.
- **`scripts/common.py`**: Shared utilities and configuration for the entire toolchain.
