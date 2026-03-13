# Slob Detection: Dynamic Inference and Targeted Reporting

## Current Focus
Shift from static thresholding to dynamic repository-aware factor inference, and introduce a targeted aggregation layer for specific slob types.

1.  **Dynamic Slob Factor Inference**
    *   Enhanced `identify.py` to automatically analyze repository distributions (average complexity, LOC, global variable frequency).
    *   Implemented a "zero-flag" mode where the tool suggests the most relevant feature flags based on detected architectural smells (e.g., `Inferred Flags for Repository: --global-variables`).
    *   Suppressed detailed candidate listing in default mode to prioritize high-level repository health signals and actionable "next step" commands.

2.  **Targeted Aggregation Layer**
    *   Introduced CLI flags (`--global-variables`, `--complexity`, `--lloc`, `--public-private`) to toggle specialized reporting views.
    *   Developed an aggregation engine that calculates cumulative repository-level slob scores and specific metric counts.
    *   Implemented a "Top 3 Files" ranking for each specific slob factor, providing clear targets for refactoring efforts based on their contribution to the total repo score.

3.  **Documentation & Ecosystem Alignment**
    *   Completely overhauled `docs/scripts.md` to reflect the new dual-mode (Inferred vs. Targeted) operation.
    *   Standardized command-line documentation and provided clear rationale for each collection flag.
    *   Ensured the `identify.py` script header include full PEP 723 metadata for seamless `uv run` execution across different environments.
