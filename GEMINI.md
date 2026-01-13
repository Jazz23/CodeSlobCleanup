# Code Slob Cleanup Project

## Project Goal
The "Code Slob Cleanup" project aims to build an automated toolchain—packaged as a coding agent skill—to identify, refactor, and rigorously verify Python code to remove "code slob". "Code slob" refers to subtle technical debt, unnecessary verbosity, and complexity often introduced by AI coding agents or rapid development.

## Core Components
1.  **Scanner**: Detects "slob" candidates using static analysis (complexity, LoC) and semantic analysis (LLMs).
2.  **Refactor Agent**: Automatically applies transformations to clean up the code (e.g., decomposing functions, removing dead code).
3.  **Verifier**: Ensures that refactoring does not break functionality using rigorous testing:
    *   **Property-Based Testing**: Using **Hypothesis** to verify `Original(input) == Transformed(input)`.
    *   **Fuzzing**: Using **Atheris** (Google) for coverage-guided fuzzing.

## Development Context
*   **Package Management**: This project uses **`uv`** instead of `pip` for faster and more reliable dependency management.
*   **Current Focus**:
    *   Establishing the testing baseline with Hypothesis.
    *   Developing the static analysis scanner for identifying slob.
    *   Creating canonical examples of "slob" vs. "clean" code.

## References
*   See `G:\GitHub\cse247b_reports_w26\codeslob\overview.md` for the full project overview.
*   See `G:\GitHub\CodeSlobCleanup\.gemini\skills\cse247b\references\codeslob.md` for skill references.
