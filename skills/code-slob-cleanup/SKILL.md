---
name: code-slob-cleanup
description: A comprehensive skill to identify "code slob" (technical debt), refactor it into clean, idiomatic Python, and rigorously verify the changes using property-based testing. Use when the user asks for their code to be refactored, cleaned up, or to have slob/slop removed. Also use when the user asks to remove code not covered by a given test. Also use when the user asks to revert a previous cleanup.
---

# Code Slob Cleanup Skill

This skill orchestrates the entire lifecycle of cleaning up "code slob": identification, safe refactoring, verification, and application.

## References
- **Refactoring**: `references/refactor.md`
- **Prompts**: `references/prompts.md`

**Workflow Direction**: If the user requests a cleanup, follow the "Refactor" workflow. If they request a revert, skip to the "Revert" workflow. Always strictly adhere to any exclusions specified in `code-slob-cleanup.json` OR by inline comments in the source code.

## Refactor Workflow

### Phase 1: Identification & Setup
0.  **Configuration & Exclusions**: Check for a `code-slob-cleanup.json` file in the project root and look for inline comment exclusions in the source code.
    *   **Auto-Generation**: If `code-slob-cleanup.json` does not exist, create it with the following structure:
        ```json
        {
            "excludePaths": [],
            "excludeFunctions": [],
            "edits": {}
        }
        ```
    *   **Format**:
        ```json
        {
            "excludePaths": ["path/to/file.py", "folder/*"],
            "excludeFunctions": ["func_name", "path/to/file.py:func_name"],
            "edits": {
                "path/to/file.py:class_name.function_name": "commit-hash",
                "path/to/file.py:function_name": "commit-hash"
            }
        }
        ```
    *   **Action**: If it exists, read it. You MUST strictly exclude the specified paths and functions from all subsequent steps in this phase.
    *   **excludePaths**: Skip any files or folders that match these patterns (relative to project root).
    *   **excludeFunctions**: Supports literal names and glob-style pattern matching (`*`, `?`).
        *   **Global Pattern**: If it's just a name or pattern (e.g., `"internal_*"`), skip any function matching that pattern in ANY file.
        *   **Scoped Pattern**: If it contains a colon (e.g., `"src/*.py:*_helper"`), skip functions matching the function pattern only in files matching the path pattern.
        *   **Mixed**: You can mix literals and patterns (e.g., `"utils.py:legacy_*"` or `"*/api.py:validate"`).
    *   **Inline Comments**: You MUST also respect the following inline comments within the source files:
        *   **`# cs-cleanup: ignore-file`**: If this is the very first line of a file, ignore the entire file.
        *   **`# cs-cleanup: ignore-function`**: If this appears on the line immediately preceding a function definition, ignore that specific function.
        *   **`# cs-cleanup: ignore-start` / `# cs-cleanup: ignore-end`**: Ignore all code between these markers. If they wrap a function definition, ignore that function.
        *   **`# cs-cleanup: ignore`**: Ignore the specific line containing this comment.
        *   **Note**: Custom comments can follow these directives (e.g., `# cs-cleanup: ignore-function - legacy code`).
0.1 **Refactoring Scope Determination**: Analyze the user's prompt for specific targets.
    *   **Specific Targets**: If the user mentions specific functions (e.g., `process_data`), files (e.g., `utils.py`), or folders (e.g., `src/`), these are your **Target Scope**.
    *   **Implicit Scope**: If no specific targets are mentioned, the **Target Scope** is the entire repository (default: `.`).
    *   **Strict Adherence**: Your refactoring efforts MUST be strictly confined to the **Target Scope**. Do not refactor anything outside of what the user explicitly requested, even if it appears to be "slob".
1.  **Golden Test Coverage (Optional)**:
    *   **Trigger**: Run this step **ONLY IF** the user explicitly requests to remove untested code or perform a "golden test cleanup" in their prompt (e.g., "Clean up untested code using test_main.py"). Do **NOT** run this step just because a test script is mentioned or exists in the codebase; the intent to use it for code removal must be explicit.
    *   **Action**: Run the cleanup script: `uv run scripts/clean_untested.py <golden_test_script_path>`.
    *   **Outcome**: This will automatically remove any functions from the original codebase that are not executed by the golden test script. **The script will automatically respect all exclusions defined in Step 0 (JSON and inline comments).**
2.  **Discover Existing Jobs**: Check for an existing `.code-slob-tmp` directory.
    *   If it exists, and no new specific targets were requested, assume identification is complete. Read all existing `original.py` files in its subdirectories to proceed with refactoring. **Do not** re-scan the source codebase unless explicitly requested.
    *   If it does *not* exist, or if new specific targets were requested, proceed to step 3.
3.  **Hybrid Identification**:
    *   **Scope Filtering**: 
        *   If a **Target Scope** was identified in step 0.1, you MUST filter all identification to ONLY include these targets.
        *   If the user specified functions, only scan/extract those functions.
        *   If the user specified files/folders, run the identification script on the appropriate directory and filter for those specific paths.
    *   **Automated FIRST**: Run the identification script: `uv run scripts/identify.py --target-dir <TARGET_DIR>`. Use `.` as the default `TARGET_DIR` if the scope is the entire repository or the user didn't specify a scope.
    *   **Filter script output**: Manually filter the output of `identify.py` to remove any candidates that:
        1. Fall outside the **Target Scope** (if one exists).
        2. Match the exclusions (JSON or inline comments) defined in step 0.
    *   **Manual Supplement**: Only perform a manual review of the codebase AFTER seeing the script results, to catch anything the script might have missed (e.g., extremely subtle logic "slob"). Ensure you do NOT include anything that matches the exclusions or falls outside the **Target Scope**.
    *   **Heuristic vs. Reality**: Analyze the output of both methods. Note that high complexity/LOC doesn't *always* mean the code is "slob". 
    *   **Filter**: If a function is an inherently complex algorithm (e.g., advanced mathematics) where the complexity is necessary and the code is already as clean as practical, **DO NOT** refactor it. Focus on actual "slob"—code that is complex due to poor structure or neglect.
4.  **Access Workspace**: Use the temporary directory `.code-slob-tmp` in the project root. Create it if it does not exist.
5.  **Structure**: For any *newly* identified targets, create a uniquely named subdirectory (job) within `.code-slob-tmp`.
6.  **Extract**: Create or update `original.py` files for the jobs.
    *   **Filter Duplicates, Exclusions & Scope**: Ensure you only add functions that are *not* already present in the existing `original.py` for that job, are NOT excluded by the JSON or inline comment configuration in step 0, and are WITHIN the **Target Scope** defined in step 0.1.
    *   **Deterministic Only**: Only copy functions that are deterministic and suitable for property-based testing. **Do NOT** copy functions that:
        *   Use random number generation or are otherwise non-deterministic (e.g., `generate_id`, `random_string`).
    *   **Copy Content**: Copy the identified functions into the appropriate `original.py`.
    *   **Literal Copy**: Copy the code EXACTLY as it appears in the source. Do NOT add type hints, docstrings, or perform any refactoring during this step. `original.py` must be a faithful representation of the "slob" code for verification purposes.
    *   **Exclusion Respect**: When copying functions, ensure you respect block-level exclusions (`# cs-cleanup: ignore-start`/`# cs-cleanup: ignore-end`) and line-level exclusions (`# cs-cleanup: ignore`). If a function is being copied, omit any lines within it that are marked for exclusion. If a block of logic within the function is excluded, skip it.
    *   **Dependencies**: Include all necessary imports and helper classes/functions required for these functions to run in isolation.
    *   **Validity**: Ensure the final `original.py` remains valid, runnable Python code.
    *   **Restriction**: Do not copy the `main()` function into an `original.py` file.
    *   **Type Hints & Metadata (type_hints.json)**: Create a `type_hints.json` file in each job directory. This is CRITICAL for both verification and reporting.
        *   **Format**:
            ```json
            {
                "functions": {
                    "path/to/file.py:func_name": ["type1", "type2"],
                    "path/to/file.py:ClassName.method_name": ["type1"]
                },
                "modules": ["any_required_external_module"]
            }
            ```
        *   **Function Keys (REQUIRED)**: For every function and class method extracted into `original.py`, you MUST use the full path as the key: `"path/to/file.py:function_name"` or `"path/to/file.py:ClassName.method_name"`. This ensures the verification output correctly identifies functions across different files and removes the need for a separate `source_files` section.
        *   **functions (Optional Values)**: The values in the `functions` object are optional type hints. If you can confidently deduce type hints for the function arguments, include them here to help Hypothesis generate valid inputs.
        *   **modules (Optional)**: List any external pip-installable modules required by the functions that are NOT part of the standard library.

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
