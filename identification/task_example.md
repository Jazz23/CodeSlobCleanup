# Slob Detection: Static Analysis Scanner

## Current Focus
Develop the static analysis foundation to objectively identify "Code Slob" candidates based on complexity and maintainability metrics.

1.  **Metric Selection & Tooling**
    *   Research and select Python static analysis libraries (e.g., standard `ast` module, `radon`, `mccabe`).
    *   Define specific thresholds for "Slob":
        *   Cyclomatic Complexity > 10?
        *   Function length > 50 lines?
        *   Argument count > 5?
        *   Nesting depth > 4?

2.  **Build the Scanner**
    *   Create a Python script (`scan_metrics.py`) that recursively traverses a target directory.
    *   Parse each Python file and extract the defined metrics for every function and class.
    *   Implement logic to flag items that breach the thresholds.

3.  **Structured Output**
    *   Ensure the scanner outputs a clean, machine-readable JSON format.
    *   Schema example:
        ```json
        [
          {
            "file": "src/utils.py",
            "function": "process_data",
            "line_start": 45,
            "metrics": { "complexity": 15, "loc": 60 },
            "reason": "High complexity"
          }
        ]
        ```

4.  **Baseline Scan**
    *   Run the scanner on a known open-source repo (or the project's own codebase).
    *   Tune thresholds to avoid excessive noise (false positives).
    