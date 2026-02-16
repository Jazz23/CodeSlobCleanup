# Overview
"Code Slob" refers to the subtle technical debt, unnecessary verbosity, and over-complexity often introduced by AI coding agents or rapid development. While functional, "slob" code is harder to maintain and prone to future regressions. The **Code Slob Cleanup** project builds an automated toolchain—packaged as a coding agent skill—to identify, refactor, and rigorously verify Python code to remove this debt.

# How to use

- Copy the [code-slob-cleanup](https://github.com/Jazz23/CodeSlobCleanup/tree/main/skills/code-slob-cleanup) skill into your agent's `skills` folder in your repository.
- Tell your agent to "Clean up my code".

# Notes
- The agent will create a temporary directory, `.code-slob-tmp`. This will be deleted after the refactoring process; however, it may be useful to add this to your `.gitignore` just in case the agent crashes or is cancelled.

# Core Objectives
1.  **Automated Identification**: Detect refactoring targets using static analysis metrics (Cyclomatic Complexity, LoC, nesting depth) and semantic analysis via LLMs to identify redundant logic.
2.  **Safe Refactoring**: Employs your agent to perform code transformations such as function decomposition, visibility enforcement (Converting public to private), and dead code removal.
3.  **Rigorous Verification**: Ensure behavioral equivalence using **Property-Based Testing**: Leveraging **Hypothesis** to verify `Original(input) == Transformed(input)` across thousands of inputs.
4.  **Autonomous Self-Correction**: Integrate verification feedback directly into the refactoring loop, allowing the agent to "fix its own fixes" based on counter-examples found during testing.

# Architecture
The system follows an iterative loop:
*   **Scanner**: Traverses the codebase and finds code slob.
*   **Refactor Agent**: Analyzes flagged code and generates a cleaned-up version.
*   **Verifier**: An isolated orchestrator executes Hypothesis tests, and benchmarks performance.
*   **Feedback Loop**: If verification fails, the failing test cases are fed back to the Refactor Agent for a retry.
*   **Committer**: Applies the change if verification passes and performance is not regressed.

# Technologies
*   **Language**: Python 3.14+
*   **Package Management**: `uv` (PEP 723 for standalone scripts)
*   **Testing**: Hypothesis (Property-based), Pytest
*   **Benchmarking**: Matplotlib/Numpy for performance comparison