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
    *   **Mandatory PEP 723**: Never use `uv run --with <package>`. Instead, if a script is missing a dependency, modify the original script to include PEP 723 inline metadata (e.g., `# /// script \n # dependencies = ["package"] \n # ///`).
*   **Continuous Verification**: Always run the comprehensive test suite after modifying any tools, scripts, or adding new "slob" vs "clean" examples to ensure behavior remains consistent and tools function as expected.
    *   Verifier Tests: `uv run verification/tests/run_tests.py`
    *   Scanner Tests: `uv run identification/tests/run_tests.py`
*   **Current Focus**:
    *   Refining the **Scanner** heuristics and integrating Semantic Analysis.
    *   Expanding the canonical examples of "slob" vs. "clean" code.

## References
*   See `cse247b_reports_w26\codeslob\overview.md` for the full project overview.
*   See `CodeSlobCleanup\.gemini\skills\cse247b\references\codeslob.md` for skill references.

## Tone & Communication
*   **No Redundant Confirmations**: Do not verbally state "I will not push without consent" in responses. Adhere to the policy silently as per core mandates.
