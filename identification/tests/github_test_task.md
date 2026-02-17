# Slob Detection: GitHub Repository Scanning

## Current Focus
Validate the static analysis scanner by running it against diverse, real-world Python codebases hosted on GitHub. This ensures the defined metrics and thresholds are accurate and generalizable.

1.  **Repository Selection & Preparation**
    *   Identify target GitHub repositories that vary in size, complexity, and age (e.g., `requests`, `flask`, `scikit-learn`).
    *   Clone the target repositories into a local `codebases/` directory for analysis.
    *   Ensure a consistent environment (e.g., specific Python version) for reproducibility.

2.  **Automated Execution**
    *   Use the scanner's orchestrator to process the cloned repositories.
    *   Command example:
        ```bash
        uv run identification/src/scanner/orchestrator.py --target-dir codebases/requests --output reports/requests_scan.json
        ```
    *   Implement batch processing scripts to scan multiple repositories sequentially.

3.  **Result Analysis & Verification**
    *   Inspect the generated JSON reports (`reports/*.json`).
    *   Compare identified "slob" candidates with manual code reviews to determine:
        *   **Precision**: Are the flagged items actually "slob"?
        *   **Recall**: Did the scanner miss any obvious "slob" patterns?
    *   Aggregate metrics across different repositories to identify common code smells.

4.  **Threshold Refinement**
    *   Adjust thresholds for Cyclomatic Complexity, LLOC, and Slob Score based on the real-world data.
    *   Identify repository-specific patterns that might require specialized rules or exclusions.
    *   Document the rationale for any changes to the core detection logic.
