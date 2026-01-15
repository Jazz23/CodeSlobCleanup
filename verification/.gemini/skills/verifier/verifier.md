# Verifier Skill Instructions

This skill allows the agent to verify the behavioral equivalence of refactored Python code against its original version and benchmark performance changes.

## When to Use
- After a Refactor Agent has produced refactored code, or when the user asks for verification and provides a directory.
- When you need to ensure that logic remains identical between two versions of a file.
- When you want to verify that refactoring did not introduce performance regressions.

## Instructions
- Each job subfolder MUST contain an `original.py` and a `refactored.py`.
- Pass a configuration JSON string to the orchestrator via the `--config` flag to guide type inference for untyped functions.
- The orchestrator will print the verification and benchmark results to stdout.

### Running the Orchestrator
Execute the following command:
```
uv run python scripts/orchestrator.py --target-dir <PATH_TO_JOBS_DIR> --config <JSON_STRING>
```

### Verification Config
Verification config guides type inference for untyped functions. Pass the configuration JSON string directly to the orchestrator via the `--config` flag.

JSON format:
```json
{
  "function_name": ["int", "str", "list"],
  "Class.method_name": ["str", "str"]
}
```
