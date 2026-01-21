# Verification Module

The `verification` directory contains the tooling and infrastructure for verifying that refactored code is functionally equivalent to the original code. It uses Property-Based Testing (Hypothesis) and automated Fuzzing to detect regressions.

## Overview

The core goal is to provide a safety net for automated refactoring. Given an `original.py` and a `refactored.py`, the system:
1.  **Analyzes** both files to find common functions and classes.
2.  **Infers** input types and generates test strategies using [Hypothesis](https://hypothesis.readthedocs.io/).
3.  **Fuzzes** both implementations with thousands of inputs.
4.  **Asserts** that for every input, both implementations:
    *   Return the exact same value.
    *   Or, raise the exact same exception type.
5.  **Benchmarks** the performance to detect speedups or regressions.

## How It Works

### 1. Orchestration (`orchestrator.py`)
The `orchestrator.py` script is the entry point. It scans a target directory for "job" subfolders (each containing an `original.py` and `refactored.py`). For each job, it spawns:
*   **Verifier**: Checks correctness.
*   **Benchmark**: Checks performance.

It aggregates results and prints a report.

### 2. Verification (`verify.py`)
This script performs the actual logic checks.
*   **Smart Inference**: It attempts to guess the types of function arguments based on type hints, default values, and usage patterns.
*   **Hypothesis**: Uses the inferred types to generate edge cases (empty lists, large numbers, special characters).
*   **Naive Fuzzer**: A backup random fuzzer that throws "dumb" random data at the functions to catch crashes that structured generation might miss.
*   **Class Support**: It can verify methods by instantiating classes with valid constructor arguments and then fuzzing the methods.

### 3. Testing the Verifier
We test the verifier itself using a suite of "Fixtures" located in `verification/tests/fixtures`.
*   `scenario_valid`: Refactorings that are correct. The verifier must PASS.
*   `scenario_broken`: Refactorings with bugs. The verifier must FAIL.
*   `scenario_hybrid`: A mix of pass/fail/skip.

## Usage

To run the verifier against a directory of refactoring jobs:

```bash
uv run verification/src/orchestrator.py <PATH_TO_JOBS>
```

To run the project's test suite (which tests the verifier):

```bash
uv run verification/tests/run_tests.py
```

## Directory Structure

*   **src/**: The core tool source code.
    *   `orchestrator.py`: Main CLI runner.
    *   `verify.py`: Logic verification engine.
    *   `benchmark.py`: Performance testing.
    *   `common.py`: Shared utilities for type inference and module loading.
*   **tests/**: Tests for the verification system.
    *   `fixtures/`: Examples of valid/invalid code used to test the verifier.
    *   `integration/`: Pytest files that run the verifier against fixtures.
    *   `run_tests.py`: The test runner script.
*   **docs/**: Specifications and implementation plans.
