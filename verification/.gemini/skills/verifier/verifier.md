# Verifier Skill Instructions

This skill allows the agent to verify the behavioral equivalence of refactored Python code against its original version and benchmark performance changes.

## When to Use
- After a Refactor Agent has produced refactored code, or when the user asks for verification and provides a directory.
- When you need to ensure that logic remains identical between two versions of a file.
- When you want to verify that refactoring did not introduce performance regressions.

## Caveats
- Do not read the contents of the scripts in this skill.
- **Mandatory Entry Point:** Only execute `scripts/orchestrator.py` for verification and benchmarking. Do not attempt to run `verify.py`, `benchmark.py`, or any other execution scripts directly; the orchestrator handles their execution. You may run `scripts/dump_fixtures.py` to inspect available examples for type inference guidance.

## Instructions
0.  **Gather Source Code:** Always run `uv run scripts/dump_fixtures.py <PATH_TO_JOBS_DIR>` to concatenate and print all `original.py` files in the target directory. This allows you to see all code at once and decipher the necessary types for the `--config` string efficiently.
1.  **Analyze Source:** Each sub-directory within the `<PATH_TO_JOBS_DIR>` represents a single verification job and MUST contain two files: `original.py` and `refactored.py`. Use the source code gathered in the previous step to identify functions and parameters that require type configuration.
2.  **Determine Config:**
    *   If a function **already has complete Python type hints**, do NOT include it in the `--config` string (the tools will prioritize the source hints automatically).
    *   If a function is **untyped or partially typed**, determine the correct types and prepare a JSON configuration entry.
3.  **Execute:** Pass the configuration JSON string to the orchestrator via the `--config` flag.
4.  **Quoting & Escaping:** To ensure the JSON string is parsed correctly across different shells (Bash, Zsh, PowerShell):
    *   **Preferred:** Use single quotes around the JSON string and double quotes internally (`'{"key":"val"}'`). This avoids complex escaping.
    *   **Alternative:** If using double quotes for the outer wrapper, escape internal double quotes with backslashes (`"{\"key\":\"val\"}"`).
    *   **Important:** Avoid spaces within the JSON string to prevent some shells from splitting the configuration into multiple arguments.

### Running the Orchestrator
Execute the following command format:
```
uv run scripts/orchestrator.py --target-dir <PATH_TO_JOBS_DIR> --config <JSON_STRING>
```

**Automated Refactoring:**
To automatically trigger a feedback loop for failed functions or functions with poor performance (Speedup < 0.4x), add the `--auto-refactor` flag:
```
uv run scripts/orchestrator.py --target-dir <PATH_TO_JOBS_DIR> --config <JSON_STRING> --auto-refactor
```
When this flag is used, the orchestrator will invoke `correct_refactor.py` which generates a prompt for fixing the code.


### Verification Config
Verification config guides type inference for untyped functions. Use **Qualified Names** (`Class.method_name`) for methods inside classes to avoid ambiguity.

**Universal JSON string format (Preferred):**
`'{"function_name":["int","str"],"MyClass.method_name":["list","dict"]}'`