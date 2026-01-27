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
1.  **Discover Existing Jobs**: Check for an existing `.code-slob-tmp` directory.
    *   If it exists, read all existing `original.py` files in its subdirectories to determine which functions have already been identified for refactoring.
2.  **Identify Missing Targets**: Analyze the source codebase for any additional "slob" functions or snippets that require cleanup but are *not* yet captured in the existing `original.py` files, if any.
3.  **Access Workspace**: Use the temporary directory `.code-slob-tmp` in the project root. Create it if it does not exist.
4.  **Structure**: For any *newly* identified targets, create a uniquely named subdirectory (job) within `.code-slob-tmp`.
5.  **Extract**: Create or update `original.py` files for the jobs.
    *   **Filter Duplicates**: Ensure you only add functions that are *not* already present in the existing `original.py` for that job.
    *   **Copy Content**: Copy the identified functions into the appropriate `original.py`.
    *   **Dependencies**: Include all necessary imports and helper classes/functions required for these functions to run in isolation.
    *   **Validity**: Ensure the final `original.py` remains valid, runnable Python code.
    *   **Restriction**: Do not copy the `main()` function into an `original.py` file.

### Phase 2: Refactoring
Follow the instructions in `references/refactor.md` to generate `refactored.py` for the job(s) in the temporary workspace.
*   **Context**: You are working inside `.code-slob-tmp/`.
*   **Goal**: Create `refactored.py` next to `original.py` containing the refactored versions of the extracted functions.

### Phase 3: Verification
Follow the instructions in **Section 3 of `references/refactor.md`** to verify the refactoring.
*   **Command**: `uv run scripts/orchestrator.py .code-slob-tmp`
*   **Action**: If verification fails, follow the iteration steps in `references/refactor.md` (fix `refactored.py` and retry).
    *   **Retry Limit**: You have a maximum of 3 attempts to fix and verify.
    *   **Failure Handling**: If a function still fails verification after 3 attempts, explicitly **IGNORE** the refactored code for that function. Do **NOT** introduce it back into the original codebase. Report the failure to the user.

### Phase 4: Application (Patch)
1.  **Check Result**: For each function, check if verification passed (`[PASS]`). If a function didn't pass (`[FAIL]`), ignore steps 2 and 3 for that function; otherwise, continue.
2.  **Patch**: Intelligently introduce the refactored code back into the original source file.
    *   Read the content of `refactored.py`.
    *   Use text replacement tools to replace the *original function definitions* in the source file with the corresponding refactored versions from `refactored.py`.
    *   Ensure indentation, comments, and formatting match the source file's style.
    *   Do *not* blindly overwrite the entire file. Only replace the specific functions that were refactored and verified.
3.  **Report**: Inform the user that the code has been cleaned and verified.

### Phase 5: Cleanup
1.  **Remove Workspace**: Delete the temporary directory.
    *   `rm -rf .code-slob-tmp`
