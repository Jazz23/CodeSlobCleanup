# Code Slob Detection: Phase 3 (Semantic & Reporting)

## Current Focus
Enhance the slob detection tool with semantic analysis (design debt) and provide automated, high-level summaries for large-scale codebase audits.

1.  **Semantic Metrics Integration**
    *   Implement `semantic.py` to detect global variables and private class sprawl.
    *   Develop heuristics for "Semantic Relevance" (comparing naming to file purpose).
    *   Integrate semantic penalties into the core Slob Score in `identify.py`.

2.  **Qualitative Interpretation**
    *   Create `slob_interpretations.txt` documenting the exact mathematical formulas.
    *   provide a detailed breakdown of Complexity (ΣC²), LLOC (ΣL/5), and Semantic Penalties for targeted repositories.
    *   Illustrate "Penalty Amplification" using real-world examples (e.g., `hagent`'s global variables).

3.  **Automated Reporting Engine**
    *   Expand `github_test_summary.csv` to include semantic metrics and repository-wide totals.
    *   Deep-scan repositories (`flask`, `requests`, `python-dotenv`, `hagent`, `code-smells`) to populate the global summary.
    *   Implement `update_summary.py` to automate the entire scan-to-report workflow with zero manual input.

4.  **Verification & Documentation**
    *   Create `walkthrough.md` documenting the feature set and impact on project scripts.
    *   Verify and fix pathing logic in the orchestration tools to handle varied execution environments.
    *   Finalize `commands_to_run.txt` with simplified CLI usage for the automated summary tool.
