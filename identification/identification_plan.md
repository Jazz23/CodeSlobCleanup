# Identification Aspect: 5-Week Completion Plan

## Objective
Complete the "Identification" component of the Code Slob Cleanup toolchain. This involves moving beyond basic static metrics to a robust, hybrid detection system that combines static analysis with semantic understanding (LLMs) to accurately flag "slob" code (technical debt, unnecessary verbosity, poor maintainability).

## Current Status
- **Static Analysis**: core metrics (Complexity, Halstead, LOC) and heuristic scoring are implemented (`metrics.py`).
- **Orchestration**: Directory scanning and JSON reporting are functional (`orchestrator.py`).
- **Missing**: Semantic Analysis (LLM integration), ground-truth benchmarking, heuristic tuning, and hybrid scoring.

---

## Week 1: Ground Truth & Benchmarking
**Goal**: Establish a verified dataset of "Clean" vs. "Slob" code and evaluate the current static scanner's performance.

- [ ] **Curate Dataset**: Formalize the existing `codebases/` into a labeled dataset.
    - Tag files/functions as `Clean`, `Slob-Complexity`, `Slob-Verbosity`, `Slob-Design`.
- [ ] **Baseline Scan**: Run the current `metrics.py` against the dataset.
- [ ] **Correlation Analysis**: Determine how well current metrics (`Complexity^2 + LLOC/5`) correlate with the tags.
- [ ] **Failure Analysis**: Identify false positives (clean code flagged as slob) and false negatives (slob code missed).

## Week 2: Advanced Static Analysis & Tuning
**Goal**: Refine static detection to catch design smells and improve heuristic accuracy before adding expensive AI calls.

- [ ] **Design Smells**: Implement detectors for class-level smells.
    - *God Class* (too many methods/attributes).
    - *Data Class* (only data, no behavior).
- [ ] **Heuristic Tuning**: Adjust the `calculate_slob_score` formula based on Week 1 data.
    - Calibrate weights for Complexity vs. Length.
    - Introduce penalties for nesting depth or argument count.
- [ ] **Visualization**: Create a simple visualizer (e.g., HTML or CLI histogram) to see the distribution of slob scores across a codebase.

## Week 3: Semantic Analysis (LLM Integration)
**Goal**: Implement the "Semantic" half of the scanner to catch qualitative issues (naming, clarity, intent).

- [ ] **Prompt Engineering**: Design and test prompts for "Code Cleanliness Review".
    - Focus on: Variable naming, logic clarity, excessive comments, "AI-generated verbosity".
- [ ] **Analyzer Implementation**: Create `semantic_analyzer.py`.
    - Function to send code snippets to an LLM API.
    - Parse structured output (e.g., JSON: `{ "slob_rating": 7/10, "reason": "..." }`).
- [ ] **Cost Control**: Implement strategy to only scan interesting candidates (e.g., top 20% static scores) to save tokens.

## Week 4: Hybrid Scanning & Reporting
**Goal**: Merge Static and Semantic engines into a unified "Identification" tool.

- [ ] **Integration**: Update `orchestrator.py` to use both engines.
    - Pipeline: `Scan Files` -> `Static Score` -> `Filter Candidates` -> `Semantic Verification`.
- [ ] **Unified Scoring**: Create a `HybridSlobScore`.
    - e.g., `StaticScore * 0.4 + SemanticScore * 0.6`.
- [ ] **Reporting Upgrade**: Enhance the JSON report to include LLM explanations for *why* something is slob.

## Week 5: Validation, Polish & Packaging
**Goal**: Prove the tool works in the wild and finalize the "Identification" Skill.

- [ ] **Wild Testing**: Run the full scanner on a real-world, messy open-source repository (or a legacy project).
- [ ] **Validation**: Manually review a sample of the tool's findings to confirm accuracy.
- [ ] **Documentation**: Update `README.md` and Skill documentation.
- [ ] **Performance Optimization**: Ensure scanning is fast enough (caching LLM responses, parallel processing).
