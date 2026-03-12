# Slob Detection: Reporting, Setup, and Roadmap 

## Current Focus
Improve reporting granularity, streamline the onboarding process through a new one-command installation, and plan for future architectural smell detection capabilities within the CodeSlob ecosystem.

1.  **Summary Report Refinement**
    *   Refactored `update_summary.py` to count "Public Classes" and "Private Classes" as two independent metric columns.
    *   Replaced the simplistic "Private Classes Exist?" toggle with explicit quantitative metrics.
    *   Regenerated the global `github_test_summary.csv` against multiple repositories (including `flask`, `requests`, `python-dotenv`, `hagent`) to validate the new visibility counts.
    *   This provides a much deeper overview of class distribution across different repositories.

2.  **One-Command Setup & Distribution**
    *   Developed `scripts/install.sh` to provide a zero-configuration, one-command installation via `curl | sh`.
    *   The installation script automatically fetches or installs `uv`, syncs the repository to a localized `~/.codeslob` directory, and ensures updates work out of the box.
    *   Generates a standalone `codeslob` binary wrapper deposited straight into the user's PATH.
    *   Updated the `README.md` and `commands_to_run.txt` to clearly document the unified setup and execution methods.

3.  **Future Slob Factors Roadmap**
    *   Created `extraslob.md` detailing future AI-introduced smells to capture on our next sprint.
    *   Cataloged issues such as: Code Duplication, Deep Nesting (Indentation Debt), and Long Parameter Lists.
    *   Added detection patterns for "Silent" Error Handling and Hard-coded Magic Values.
