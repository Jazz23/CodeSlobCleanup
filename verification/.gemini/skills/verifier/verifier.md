# Verifier Skill Instructions

This skill allows the agent to verify the behavioral equivalence of refactored Python code against its original version and benchmark performance changes.

## When to Use
- After a Refactor Agent has produced refactored code, or when the user asks for verification and provides a directory.
- When you need to ensure that logic remains identical between two versions of a file.
- When you want to verify that refactoring did not introduce performance regressions.

## Caveats
- Do not read the contents of the scripts in this skill.

## Instructions
1.  **Analyze Source:** For each job, read the `original.py` file to gather necessary type information for the function parameters.
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
uv run python scripts/orchestrator.py --target-dir <PATH_TO_JOBS_DIR> --config <JSON_STRING>
```

### Verification Config
Verification config guides type inference for untyped functions. Use **Qualified Names** (`Class.method_name`) for methods inside classes to avoid ambiguity.

**Universal JSON string format (Preferred):**
`'{"function_name":["int","str"],"MyClass.method_name":["list","dict"]}'`