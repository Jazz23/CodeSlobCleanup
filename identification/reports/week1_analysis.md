# Week 1: Ground Truth & Benchmarking Analysis

## 1. Executive Summary
The baseline static analysis successfully distinguishes between "Clean" and "Slob" code in the curated dataset. However, the current composite `slob_score` formula heavily biases towards Cyclomatic Complexity, resulting in low scores for low-complexity but high-verbosity code (monolithic functions). These were only detected due to specific LLOC thresholds, not the score itself.

## 2. Dataset
We established a ground truth dataset in `identification/data/dataset_manifest.json`:
*   **Clean**: `test-clean-modular` (Short, focused functions).
*   **Slob-Complexity**: `test-slob-complexity` (Deep nesting, high branching).
*   **Slob-LLOC**: `test-slob-lloc` (Long, sequential, verbose logic).

## 3. Results Analysis

### Sensitivity & Precision
| Category | File | Metric | Detected? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Clean** | `math_utils.py` | Score: < 10 | **No** (Correct) | No false positives. |
| **Slob-Complexity** | `nested_logic.py` | Score: 174.2 | **Yes** | Complexity (13) dominates the score ($13^2 = 169$). |
| **Slob-LLOC** | `verbose_script.py` | Score: 36.2 | **Yes*** | *Detected only by `LOC > 50` threshold.* Score was below threshold (50). |

### Formula Evaluation
Current Formula: `Score = (Complexity^2) + (LLOC / 5)`

*   **Complexity Influence**: Exponential ($x^2$). A small increase in complexity drastically raises the score.
*   **LLOC Influence**: Linear and dampened ($x/5$). A function needs 250 LLOC to reach a score of 50 (assuming Complexity=0).
*   **Issue**: `verbose_script.py` had 101 LLOC but only contributed ~20 points to the score.

## 4. Recommendations for Week 2
1.  **Formula Tuning**:
    *   increase LLOC weight or use a non-linear scaler for LLOC (e.g., `(LLOC / 20)^2`).
    *   Consider a "Max" strategy: `Max(ComplexityScore, LLOCScore)` instead of summing, to flag code that is bad in *either* dimension.
2.  **Scanner Hygiene**:
    *   Exclude `.code-slob-tmp` directories from the scan.
3.  **Reporting**:
    *   Explicitly state *why* a candidate was flagged (Score vs Threshold).
