# Scripts Reference

The **Code Slob Cleanup** project relies on several key Python scripts to automate the identification, verification, and cleaning of code. All scripts are ran using `uv run`.

## `skills/code-slob-cleanup/scripts/identify.py`

This script is the entry point for finding "code slob" in your repository. It supports both automatic factor inference and targeted identification.

- **Usage**: `uv run skills/code-slob-cleanup/scripts/identify.py <directory> [flags]`
- **Flags**:
    - `--global-variables`: Detect non-constant global variables.
    - `--complexity`: Analyze cyclomatic complexity.
    - `--lloc`: Analyze Logical Lines of Code (LLOC).
    - `--public-private`: Identify public members that could be private.
    - `--duplication`: Discover functionally identical code blocks using AST normalization.
    - `--file-count <N>`: Rank and display the top N files most affected by code slob.
- **Functionality**: 
    - Scans the target directory for Python files and calculates core metrics.
    - Automatically determines prominent slob factors if no flags are provided.
    - Aggregates slob scores at the repository level for high-level quality tracking.
    - Detects cross-file duplication and cross-reference issues.
    - Respects exclusions defined in `code-slob-cleanup.json` and inline comments.

## `skills/code-slob-cleanup/scripts/orchestrator.py`

This script manages the verification process within the `.code-slob-tmp/` workspace.

- **Usage**: `uv run skills/code-slob-cleanup/scripts/orchestrator.py .code-slob-tmp`
- **Functionality**:
    - Discovers all refactoring "jobs" in the temporary directory.
    - Executes `scripts/verify.py` for each job.
    - Collects and aggregates results (Pass/Fail/Skip).
    - Benchmarks performance of Original vs Refactored code.
    - Summarizes the overall verification status.

## `skills/code-slob-cleanup/scripts/clean_untested.py`

This script allows you to remove code that is not covered by a specific "golden" test suite.

- **Usage**: `uv run skills/code-slob-cleanup/scripts/clean_untested.py <test_script_path>`
- **Functionality**:
    - Runs the provided test script under `coverage`.
    - Identifies all functions in the codebase that were NOT executed during the test.
    - Automatically removes these functions from the source code.
    - **CAUTION**: Use this script with care, as it will permanently delete code that it deems "unreachable" according to your test suite. It respects exclusions in `code-slob-cleanup.json` and inline comments.

## Other Utility Scripts

- **`skills/code-slob-cleanup/scripts/verify.py`**: The core script for running Hypothesis-based property testing on a single function (called by `orchestrator.py`).
- **`skills/code-slob-cleanup/scripts/metrics.py`**: Provides the static analysis tools (like Radon) used by `identify.py`.
- **`skills/code-slob-cleanup/scripts/semantic.py`**: Identifies global variables, classes that should have their own files, and functions that should be private.
- **`skills/code-slob-cleanup/scripts/common.py`**: Shared utilities and configuration for the entire toolchain.
