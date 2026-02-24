# Cleanup Workflow

The **Code Slob Cleanup** process follows a rigorous lifecycle to ensure that code is cleaned effectively and safely. The agent chooses between two main workflows based on your request.

## Workflow Selection

Before starting, the agent determines if you want to **Refactor** new code or **Revert** a previous cleanup.

---

## Workflow A: Refactor Code

### Phase 1: Identification & Setup

In this phase, the toolchain identifies potential "code slob" candidates and prepares a temporary workspace for refactoring.

1.  **Scope Determination**: The tool analyzes the user's request to determine which files or functions to target.
2.  **Configuration**: The tool reads `code-slob-cleanup.json` (**auto-generating** it if it does not exist) to strictly exclude specific paths or functions.
3.  **Golden Test Coverage (Optional)**: If requested, the `scripts/clean_untested.py` script is used to remove code that is not executed by a provided test suite.
4.  **Discovery**: The tool uses `scripts/identify.py` to find complex or verbose functions using static analysis.
5.  **Extraction**: Identified functions are extracted into a temporary directory (`.code-slob-tmp/`) along with their dependencies and type hints.

### Phase 2: Refactoring

The tool applies clean, idiomatic Python patterns to the extracted "original" code.

- **Goal**: Create a `refactored.py` version of the code that is easier to read, maintain, and more efficient.
- **Constraints**: The refactored code must maintain the exact same external behavior as the original.

### Phase 3: Verification

This is the most critical phase. The toolchain uses property-based testing to prove that `Original(input) == Refactored(input)`.

1.  **Comparison**: Both the `Original` and `Refactored` functions are executed with the same inputs using [Hypothesis](https://hypothesis.readthedocs.io/).
2.  **Validation**: If they produce different results, the verification fails.
3.  **Feedback Loop**: If verification fails, the tool will analyze the failing input and attempt to fix the refactored code, retrying up to 3 times. If it still fails, the refactored code is **discarded**, and the original code remains unchanged.

### Phase 4: Application (Patch)

Once a function passes verification, it is moved back into the main codebase.

- **Selective Application**: ONLY functions that passed verification are applied.
- **Patching**: The tool uses surgical text replacement to update the source files.
- **Test Validation**: Existing tests in the repository are run to ensure no regressions were introduced.
- **Brittle Test Fixing**: If an existing test fails because it relied on the internal implementation of the "slob" code, the tool will update the test to be more robust.
- **Record Edits**: For each successfully refactored function, an entry is added to the `edits` dictionary in `code-slob-cleanup.json`, storing the function identifier and the parent commit hash. This enables future reverts.

### Phase 5: Cleanup

The temporary workspace `.code-slob-tmp/` is deleted, leaving the codebase clean.

---

## Workflow B: Revert Cleanup

If you ask to "revert" or "undo" a cleanup, the agent follows this path:

1.  **Identify Targets**: The agent scans the `edits` map in `code-slob-cleanup.json` to find the functions, classes, files, or folders you mentioned.
2.  **Extract Original**: Using the stored commit hash and `git show`, the agent retrieves the original version of the code as it existed before the cleanup.
3.  **Restore**: The refactored code in the current codebase is replaced with the extracted original code.
4.  **Verify**: Existing tests are run to ensure the restoration is safe.
5.  **Update Map**: The matching entries are removed from the `edits` dictionary.
