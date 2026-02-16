---
name: code-slob-cleanup
description: A comprehensive skill to identify "code slob" (technical debt), refactor it into clean, idiomatic Python, and rigorously verify the changes using property-based testing. Use when the user asks for their code to be refactored, cleaned up, or to have slob/slop removed.
---

# Code Slob Cleanup Skill

This skill orchestrates the entire lifecycle of cleaning up "code slob": identification, safe refactoring, verification, and application.

## References
- **Refactoring**: `references/refactor.md`
- **Prompts**: `references/prompts.md`

## Workflow

### Phase 1: Identification & Setup
1.  **Golden Test Coverage (Optional)**:
    *   **Trigger**: Run this step **ONLY IF** the user explicitly requests to remove untested code or perform a "golden test cleanup" in their prompt (e.g., "Clean up untested code using test_main.py"). Do **NOT** run this step just because a test script is mentioned or exists in the codebase; the intent to use it for code removal must be explicit.
    *   **Action**: Run the cleanup script: `uv run scripts/clean_untested.py <golden_test_script_path>`.
    *   **Outcome**: This will automatically remove any functions from the original codebase that are not executed by the golden test script.
2.  **Discover Existing Jobs**: Check for an existing `.code-slob-tmp` directory.
    *   If it exists, assume identification is complete. Read all existing `original.py` files in its subdirectories to proceed with refactoring. **Do not** re-scan the source codebase unless explicitly requested.
    *   If it does *not* exist, proceed to step 3.
3.  **Hybrid Identification**:
    *   **Automated FIRST**: Run the identification script: `uv run scripts/identify.py --target-dir .`. Use its output as your primary source of targets.
    *   **Manual Supplement**: Only perform a manual review of the codebase AFTER seeing the script results, to catch anything the script might have missed (e.g., extremely subtle logic "slob"). Avoid reading every file if the script already covers the main candidates.
    *   **Heuristic vs. Reality**: Analyze the output of both methods. Note that high complexity/LOC doesn't *always* mean the code is "slob". 
    *   **Filter**: If a function is an inherently complex algorithm (e.g., advanced mathematics) where the complexity is necessary and the code is already as clean as practical, **DO NOT** refactor it. Focus on actual "slob"—code that is complex due to poor structure or neglect.
4.  **Access Workspace**: Use the temporary directory `.code-slob-tmp` in the project root. Create it if it does not exist.
4.  **Structure**: For any *newly* identified targets, create a uniquely named subdirectory (job) within `.code-slob-tmp`.
5.  **Extract**: Create or update `original.py` files for the jobs.
    *   **Filter Duplicates**: Ensure you only add functions that are *not* already present in the existing `original.py` for that job.
    *   **Deterministic Only**: Only copy functions that are deterministic and suitable for property-based testing. **Do NOT** copy functions that:
        *   Use random number generation or are otherwise non-deterministic (e.g., `generate_id`, `random_string`).
        *   Are inherently complex algorithms (e.g., advanced mathematics) where the complexity is necessary.
    *   **Copy Content**: Copy the identified functions into the appropriate `original.py`.
    *   **Literal Copy**: Copy the code EXACTLY as it appears in the source. Do NOT add type hints, docstrings, or perform any refactoring during this step. `original.py` must be a faithful representation of the "slob" code for verification purposes.
    *   **Dependencies**: Include all necessary imports and helper classes/functions required for these functions to run in isolation.
    *   **Validity**: Ensure the final `original.py` remains valid, runnable Python code.
    *   **Restriction**: Do not copy the `main()` function into an `original.py` file.

### Phase 2: Refactoring
Follow the instructions in `references/refactor.md` to generate `refactored.py` for the job(s) in the temporary workspace.
*   **Context**: You are working inside `.code-slob-tmp/`.
*   **Goal**: Create `refactored.py` next to `original.py` containing the refactored versions of the extracted functions.
*   **Efficiency**: Do NOT re-read `references/refactor.md` or `references/prompts.md` if you already have their content in memory from previous turns.

### Phase 3: Verification
Follow the instructions in **Section 3 of `references/refactor.md`** to verify the refactoring.
*   **Command**: `uv run scripts/orchestrator.py .code-slob-tmp`
*   **Action**: If verification fails, follow the iteration steps in `references/refactor.md` (fix `refactored.py` and retry).
    *   **Retry Limit**: You have a maximum of 3 attempts to fix and verify.
    *   **Failure Handling**: If a function still fails verification after 3 attempts, explicitly **IGNORE** the refactored code for that function. Do **NOT** introduce it back into the original codebase. Report the failure to the user.

### Phase 4: Application (Patch)
1.  **Check Result**: For each function, check if verification passed (`[PASS]`). 
    *   **CRITICAL**: ONLY apply refactored code for functions that received a `[PASS]`.
    *   **IGNORE**: If a function received `[FAIL]` OR `[SKIP]`, you MUST NOT apply the refactored version of that function to the original codebase.
2.  **Patch**: Apply the refactored code to the original source files.
    *   **Tooling**: Use the `write_file` or `replace` tools directly. **DO NOT** use shell redirects (e.g., `cat << EOF > file.py`) as these may be blocked by security policies.
    *   **Full Replacement**: If `refactored.py` represents the complete file (imports + code), overwrite the target file.
    *   **Merge**: If `refactored.py` only contains functions, use text replacement to update the target file, preserving surrounding code.
    *   **NO REDUNDANT READS**: Do NOT re-read the target file (e.g., `utils.py`) if you have already read it. Do NOT perform "final check" reads after writing. Trust your tool outputs and memory.
3.  **Run Existing Tests**: After applying the patches, identify and run any existing tests in the repository.
    *   **Discover**: Look for `tests/`, `test_*.py`, `pytest.ini`, or test commands in `README.md` / `package.json` / `pyproject.toml`.
    *   **Execute**: Run the tests using the appropriate tool (e.g., `pytest`, `uv run tests/run_tests.py`).
4.  **Fix Brittle Tests**: If existing tests fail for a function that Hypothesis verified as `[PASS]`:
    *   **Analyze**: Determine if the test is "brittle" (e.g., asserting on internal state, specific log messages, or private members that were cleanly refactored away).
    *   **Fix**: Modify the existing test so it passes with the new, cleaner code. Ensure you maintain the original intent of the test (verifying functionality) while removing the brittle dependency on the "slob" implementation.
5.  **Report**: Inform the user that the code has been cleaned, verified by Hypothesis, and that existing tests have been run (and updated if necessary).

### Phase 5: Cleanup
1.  **Remove Workspace**: Delete the temporary directory.
    *   `rm -rf .code-slob-tmp`
