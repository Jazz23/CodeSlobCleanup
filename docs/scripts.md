# Scripts Reference

The **Code Slob Cleanup** project relies on several key Python scripts to automate the identification, verification, and cleaning of code. All scripts are ran using `uv run`.

## `skills/code-slob-cleanup/scripts/identify.py`

This script is the entry point for finding "code slob" in your repository. It supports both automatic factor inference and targeted aggregation.

- **Usage**: `uv run skills/code-slob-cleanup/scripts/identify.py --target-dir <directory> [flags]`
- **Inferred Flags Mode**:
    - If run without feature flags (e.g., `uv run scripts/identify.py --target-dir codebases/test1`), the script identifies the most prominent slob factors and outputs a suggested command (e.g., `Inferred Flags for Repository: --global-variables`).
- **Targeted Aggregation Mode**:
    - When specific flags are provided, the script outputs a consolidated summary:
        - Total Repository Slob Score.
        - Total count of the specific metric (e.g., total global variables).
        - Top 3 Files most affected by that specific factor, with their individual scores.
- **Flags**:
    - `--global-variables`: Aggregate detection of non-constant global variables.
    - `--complexity`: Aggregate cyclomatic complexity analysis.
    - `--lloc`: Aggregate Logical Lines of Code (LLOC) analysis.
    - `--public-private`: Aggregate analysis of public members that could be private.
- **Functionality**: 
    - Scans the target directory for Python files and calculates core metrics.
    - Automatically determines prominent slob factors if no flags are provided.
    - Aggregates slob scores at the repository level for targeted reporting.
    - Ranks files by their contribution to specific slob factors.
    - Respects exclusions defined in `code-slob-cleanup.json` and inline comments.

## `skills/code-slob-cleanup/scripts/benchmark.py`

- **Usage**: `uv run skills/code-slob-cleanup/scripts/benchmark.py <original_file> <refactored_file> [flags]`
- **Functionality**:
    - Automatically generates diverse test inputs using Hypothesis strategies.
    - Executes both original and refactored code across generated input sets.
    - Measures and compares execution times to identifies performance regressions or improvements.
    - Supports benchmarking for both standalone functions and class methods.
    - Generates visual performance plots to illustrate speedup or throughput changes.

## `skills/code-slob-cleanup/scripts/update_summary.py`

- **Usage**: `uv run skills/code-slob-cleanup/scripts/update_summary.py --repo <name> --summary-file <path> [flags]`
- **Functionality**:
    - Aggregated metrics across multiple repositories into a single CSV tracking file.
    - Automatically classifies repositories into "Low", "Moderate", or "High" slob categories.
    - Identifies the "Top Slob Factor" for each repository based on heuristic analysis.
    - Generates a qualitative rationale explaining the primary driver of a repository's slob score.
    - Maintains a cumulative history of scanning results across the entire codebases directory.

## `skills/code-slob-cleanup/scripts/duplication.py`

- **Usage**: (Called internally by `identify.py` or `update_summary.py`)
- **Functionality**:
    - Parses Python source code into AST (Abstract Syntax Tree) representations.
    - Normalizes code by stripping docstrings, comments, and renaming local variables to catch functional clones.
    - Generates unique SHA-256 hashes for normalized code blocks to identify identical logic.
    - Groups slob candidates by their code hash to detect cross-file duplication.
    - Annotates candidates with references to their duplicate "twins" for easier cleanup.

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
