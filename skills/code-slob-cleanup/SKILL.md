---
name: code-slob-cleanup
description: A comprehensive skill to identify "code slob" (technical debt), refactor it into clean, idiomatic Python, and rigorously verify the changes using property-based testing. Use when the user asks for their code to be refactored, cleaned up, or to have slob/slop removed. Also use when the user asks to remove code not covered by a given test. Also use when the user asks to revert a previous cleanup.
---

# Code Slob Cleanup Skill

This skill orchestrates the entire lifecycle of cleaning up "code slob": identification, safe refactoring, verification, and application.

## References
- **Refactoring**: `references/refactor.md`
- **Prompts**: `references/prompts.md`
- **Identification**: `references/identification.md`

**Workflow Direction**: If the user requests a cleanup, follow the "Refactor" workflow. If they request a revert, skip to the "Revert" workflow. Always strictly adhere to any exclusions specified in `code-slob-cleanup.json` OR by inline comments in the source code.

## Refactor Workflow

### Phase 1: Identification & Setup
Follow the instructions in `references/identification.md` to identify slob candidates and set up the temporary workspace.
*   **Result**: A `.code-slob-tmp` directory exists, containing subdirectories (jobs) for each identified target, each with an `original.py` and `type_hints.json`.
*   **Efficiency**: Do NOT re-read `references/identification.md` if you already have its content in memory from previous turns.

### Phase 2: RefactoringFollow the instructions in `references/refactor.md` to generate `refactored.py` for the job(s) in the temporary workspace.
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
5.  **Record Edits**: Add an entry to the `edits` dictionary in `code-slob-cleanup.json` for each successfully refactored function.
    *   **Format**: `"identifier": "commit-hash"`.
    *   **Function Mapping**: The identifier MUST include the full file path and class name (if any).
        *   Example (top-level): `"path/to/file.py:function_name": "5akekdl"`
        *   Example (class method): `"path/to/file.py:ClassName.method_name": "5akekdl"`
    *   **Commit Hash**: Use the first 7 characters of the most recent commit (the parent commit of your changes). Use `git rev-parse --short=7 HEAD` to retrieve it.
    *   **Constraint**: ONLY log individual function refactors in the `edits` dictionary. Do NOT log classes or files.
6.  **Report**: Inform the user that the code has been cleaned, verified by Hypothesis, and that existing tests have been run (and updated if necessary).

### Phase 5: Cleanup
1.  **Remove Workspace**: Delete the temporary directory.
    *   `rm -rf .code-slob-tmp`

## Revert Workflow

**Constraint**: If no `code-slob-cleanup.json` exists, or if the `edits` dictionary is empty, inform the user that there are no recorded cleanups to revert and exit. Otherwise, follow the steps below to revert the specified cleanup(s):

1.  **Identify**: If the user asks to revert a cleanup (e.g., "Revert the cleanup for `process_data`", "Revert `src/utils.py`", or "Revert `src/logic/`"), search the `edits` dictionary in `code-slob-cleanup.json` for matches.
2.  **Scan for Matches**:
    *   **Specific Function**: Look for a direct match (e.g., `path/to/file.py:process_data`).
    *   **Class**: Search for all entries that include that class name in their identifier (e.g., `path/to/file.py:MyClass.*`).
    *   **File**: Search for all entries starting with that file's path (e.g., `path/to/file.py:*`).
    *   **Folder**: Search for all entries whose path starts with that folder (e.g., `path/to/folder/*`).
3.  **Find Hashes**: For each match, retrieve the associated 7-character commit hash (the parent commit where the original code exists).
4.  **Locate & Extract**: For each matched target:
    *   Use git to read the content of the original file at that commit (e.g., `git show <hash>:<path/to/file.py>`).
    *   Extract the original version of the function/class.
5.  **Revert**: Replace the refactored code in the current codebase with the original version extracted from git.
6.  **Update**: Remove all matching entries from the `edits` dictionary in `code-slob-cleanup.json`.
7.  **Verify**: Run existing tests to ensure the revert didn't break anything.
