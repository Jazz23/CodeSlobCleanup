# Scanner Skill Instructions

This skill analyzes a Python codebase to identify "code slob" — code that is overly complex, lengthy, or difficult to maintain.

## STRICT CONSTRAINTS
- **SINGLE PURPOSE:** Run the scanner orchestrator.
- **NO MODIFICATIONS:** Do not modify the code being scanned.
- **TERMINATION:** Once the scan is complete and reported, stop.

## When to Use
- When asked to "find slob", "audit code", or "identify refactoring candidates".
- Before running the `transformation-verifier` or refactoring code.

## Instructions
1.  **Identify Target:** Determine the directory to scan (`<TARGET_DIR>`).
2.  **Execute:** Run the orchestrator script using `uv`.
    ```bash
    uv run identification/.gemini/skills/scanner/scripts/orchestrator.py --target-dir <TARGET_DIR>
    ```
3.  **Analyze Report:**
    - The script produces `scan_report.json` in `<TARGET_DIR>`.
    - Read this file.
    - Summarize the findings to the user:
        - Total files scanned.
        - Number of "slob" candidates found.
        - List the top candidates with their scores and reason (e.g., "Complexity: 15, LOC: 50").

## Interpreting Scores
- **Score > 5.0**: Likely Slob.
- **High Complexity**: > 10 is worrisome.
- **High LOC**: > 50 lines per function is a warning sign.
