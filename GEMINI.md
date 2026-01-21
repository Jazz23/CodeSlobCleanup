# Code Slob Cleanup Project

ALWAYS USE `uv run <python file.py>` instead of `python ...`.

## Project Goal
The "Code Slob Cleanup" project aims to build an automated toolchain—packaged as a coding agent skill—to identify, refactor, and rigorously verify Python code to remove "code slob". "Code slob" refers to subtle technical debt, unnecessary verbosity, and complexity often introduced by AI coding agents or rapid development.

## Core Components
1.  **Scanner**: Detects "slob" candidates using static analysis (complexity, LoC) and semantic analysis (LLMs).
2.  **Verifier**: Ensures that refactoring does not break functionality using rigorous testing:
    *   **Property-Based Testing**: Using **Hypothesis** to verify `Original(input) == Transformed(input)`.

## Development Context
*   **Package Management**: This project uses **`uv`** instead of `pip` for faster and more reliable dependency management.
    *   **Always** use `uv run <script.py>`.
    *   **Mandatory PEP 723**: Never use `uv run --with <package>`. Instead, if a script is missing a dependency, modify the original script to include PEP 723 inline metadata (e.g., `# /// script 
 # dependencies = ["package"] 
 # ///`).
*   **Continuous Verification**: Always run the comprehensive test suite after modifying any tools, scripts, or adding new "slob" vs "clean" examples to ensure behavior remains consistent and tools function as expected.
    *   Command: `uv run verification/tests/run_tests.py`
*   **Git & File Management**:
    *   **Assume Intentional Deletion**: Never attempt to "restore accidentally deleted scripts" or files (e.g., using `git restore`) unless explicitly asked by the user. Assume all deletions are intentional.
    *   **No __init__.py**: Do not create empty `__init__.py` files.

## References
*   See `cse247b_reports_w26\codeslob\overview.md` for the full project overview.
*   See `CodeSlobCleanup\.gemini\skills\cse247b\references\codeslob.md` for skill references.

## Tone & Communication
*   **No Redundant Confirmations**: Do not verbally state "I will not push without consent" in responses. Adhere to the policy silently as per core mandates.