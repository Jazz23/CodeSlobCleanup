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

## Tone & Communication
*   **Never push to GitHub unless the user explicitly tells you to do so.**
*   **No Redundant Confirmations**: Do not verbally state "I will not push without consent" in responses. Adhere to the policy silently as per core mandates.

- Anytime the word "skill" is mentioned, if you haven't already please web_fetch this documentation: https://geminicli.com/docs/cli/skills/

- Whenever the user says "modify the skill", they are talking about an agent skill located in `skills/code-slob-cleanup`.