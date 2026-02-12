## Detailed Scan Results (2026-02-12)

The following table summarizes the CodeSlob metrics across the tested repositories. The **Total Slob Score** is the sum of scores for all identified "slob" candidates.

| Repository | Total Slob Score | Files Scanned | Slob Candidates | Top Slob Factor | Rationale for Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[flask](https://github.com/pallets/flask)** | ~6,500 | 35 | 71 | **God Classes** | Highly centralized architecture. The `Flask` class alone has 35+ methods and 400+ LLOC, resulting in a single-item score of 1730. |
| **[requests](https://github.com/psf/requests)** | ~4,200 | 21 | 67 | **Complex Logic & God Classes** | Heavy reliance on individual complex functions (e.g., `_encode_files`, complexity 21) and large models like `Response` and `Session`. |
| **[python-dotenv](https://github.com/theskumar/python-dotenv)** | 471.5 | 8 | 10 | **Data Classes & Utility Complexity** | Small scope. High scores are mostly for individual utility functions (`find_dotenv`) or small "Data Classes" that hold configurations. |

### Key Slob Factors Analyzed
*   **God Classes**: Classes that aggregate too much responsibility (e.g., > 7 methods or > 100 LLOC). These significantly inflate the score due to the quadratic LLOC penalty.
*   **Data Classes**: Classes that act mostly as data containers (heuristic: <= 2 methods and < 50 LLOC). 
*   **Complexity Spikes**: Individual functions with Cyclomatic Complexity > 10. These impact the score exponentially ($Complexity^2$).
*   **File Bloat**: Multiple public classes defined in a single file instead of being modularized into separate files or packages.

---

# Slob Detection: GitHub Repository Scanning

