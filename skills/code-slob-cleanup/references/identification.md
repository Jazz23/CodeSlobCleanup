# Identification & Setup

This reference document outlines the mandatory steps for identifying "code slob" and setting up the refactoring workspace.

## 0. Configuration & Exclusions
Check for a `code-slob-cleanup.json` file in the project root and look for inline comment exclusions in the source code.
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

## 0.1 Refactoring Scope Determination
Analyze the user's prompt for specific targets.
*   **Specific Targets**: If the user mentions specific functions (e.g., `process_data`), files (e.g., `utils.py`), or folders (e.g., `src/`), these are your **Target Scope**.
*   **Implicit Scope**: If no specific targets are mentioned, the **Target Scope** is the entire repository (default: `.`).
*   **Strict Adherence**: Your refactoring efforts MUST be strictly confined to the **Target Scope**. Do not refactor anything outside of what the user explicitly requested, even if it appears to be "slob".

## 0.2 Identifier Scoping
Analyze the user's prompt for specific slob identifiers and file count.
*   **Available Identifiers**: 
    - (a) `global-variables`
    - (b) `public-members` (should be private)
    - (c) `cyclomatic-complexity`
    - (d) `loc`
*   **Action**: 
    1. Check if the user has explicitly mentioned specific identifiers (e.g., "clean up global variables") OR provided the letter-based format (e.g., "abd 5") in their original prompt.
    2. If identifiers OR a file count are present, record these as the **Identifier Scope** and **SKIP** the interaction below.
*   **Mandatory Interaction**: If **BOTH** identifiers and file count are omitted from the prompt, you MUST ask the user using the following EXACT format:
    > Do you want to:
    > a. Remove global variables
    > b. Make unnecessary public classes/functions private
    > c. Lower cyclomatic complexity
    > d. Lower line count per function
    > 
    > And for how many files?
    > 
    > Simply type the letters of the identifiers you want to use, along with the file count. E.g. "abd 5".
*   **Response Parsing**:
    - `a` -> `--global-variables`
    - `b` -> `--public-private`
    - `c` -> `--complexity`
    - `d` -> `--lloc`
    - The number provided (if any) -> `--file-count <number>`
*   **Default**: If no identifiers are specified after the interaction, the scope includes all available identifiers.

## 1. Golden Test Coverage (Optional)
*   **Trigger**: Run this step **ONLY IF** the user explicitly requests to remove untested code or perform a "golden test cleanup" in their prompt (e.g., "Clean up untested code using test_main.py"). Do **NOT** run this step just because a test script is mentioned or exists in the codebase; the intent to use it for code removal must be explicit.
*   **Action**: Run the cleanup script: `uv run scripts/clean_untested.py <golden_test_script_path>`.
*   **Outcome**: This will automatically remove any functions from the original codebase that are not executed by the golden test script. **The script will automatically respect all exclusions defined in Step 0 (JSON and inline comments).**

## 2. Discover Existing Jobs
Check for an existing `.code-slob-tmp` directory.
*   If it exists, and no new specific targets were requested, assume identification is complete. Read all existing `original.py` files in its subdirectories to proceed with refactoring. **Do not** re-scan the source codebase unless explicitly requested.
*   If it does *not* exist, or if new specific targets were requested, proceed to step 3.

## 3. Hybrid Identification
*   **Scope Filtering**: 
    *   If a **Target Scope** was identified in step 0.1, you MUST filter all identification to ONLY include these targets.
    *   If the user specified functions, only scan/extract those functions.
    *   If the user specified files/folders, run the identification script on the appropriate directory and filter for those specific paths.
*   **Automated FIRST**: Run the identification script: `uv run scripts/identify.py <TARGET_DIR> [flags]`. 
    *   Use `.` as the default `TARGET_DIR` if the scope is the entire repository or the user didn't specify a scope.
    *   **Mandatory Flags**: You MUST provide the appropriate flags based on the **Identifier Scope** (Step 0.2):
        *   `--global-variables`: For global variables.
        *   `--complexity`: For cyclomatic complexity.
        *   `--lloc`: For logical lines of code.
        *   `--public-private`: For public/private member analysis.
        *   `--file-count <N>`: To limit output to the top N "slobbiest" files.
        *   **Default**: If no **Identifier Scope** is specified, provide ALL identifier flags to perform a comprehensive scan.
        *   **Filter script output**: Manually filter the output of `identify.py` to remove any candidates that:
    1. Fall outside the **Target Scope** (if one exists).
    2. Match the exclusions (JSON or inline comments) defined in step 0.
*   **Manual Supplement**: Only perform a manual review of the codebase AFTER seeing the script results, to catch anything the script might have missed (e.g., extremely subtle logic "slob"). Ensure you do NOT include anything that matches the exclusions or falls outside the **Target Scope**. If an **Identifier Scope** exists, only look for candidates matching those types.
*   **Heuristic vs. Reality**: Analyze the output of both methods. Note that high complexity/LOC doesn't *always* mean the code is "slob". 
*   **Filter**: If a function is an inherently complex algorithm (e.g., advanced mathematics) where the complexity is necessary and the code is already as clean as practical, **DO NOT** refactor it. Focus on actual "slob"—code that is complex due to poor structure or neglect.

## 4. Access Workspace
Use the temporary directory `.code-slob-tmp` in the project root. Create it if it does not exist.

## 5. Structure
For any *newly* identified targets, create a uniquely named subdirectory (job) within `.code-slob-tmp`.

## 6. Extract
Create or update `original.py` files for the jobs.
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
    *   **functions (Optional Values)**: The values in the `functions` object are optional type hints. If you can confidently deduce type hints for the function arguments, include them here to help Hypothesis generate valid inputs. **CRITICAL**: ONLY add type hints to `type_hints.json` if the original function's parameters weren't already typed in the source code. This avoids redundant metadata if the source is already informative.
    *   **modules (Optional)**: List any external pip-installable modules required by the functions that are NOT part of the standard library.
