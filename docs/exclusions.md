# Configuration & Exclusions

You can control the behavior of the Code Slob Cleanup toolchain by using the `code-slob-cleanup.json` file in your project root, or by providing inline comments in your code.

## The `code-slob-cleanup.json` File

This file is **auto-generated** in your project root during the first run if it does not already exist. You can also create it yourself before the first run. It serves two main purposes:
1.  **Exclusions**: Specifying paths and functions to ignore during cleanup.
2.  **Edit Tracking**: Keeping a record of refactored functions to allow for easy reverts.

### Json File Format

```json
{
    "excludePaths": [
        "tests/*",
        "legacy/old_utils.py"
    ],
    "excludeFunctions": [
        "internal_*",
        "src/api.py:deprecated_handler",
        "utils.py:helper_*"
    ],
    "edits": {
        "src/utils.py:process_data": "5akekdl",
        "src/models.py:User.validate": "7d2f3a1"
    }
}
```

### `excludePaths`

A list of glob patterns relative to the project root. Any file or directory matching these patterns will be completely ignored by the scanner and the refactoring tool.

### `excludeFunctions`

A list of function names or patterns to exclude. This supports:

- **Global Literals**: `"my_func"` - Excludes any function named `my_func` in any file.
- **Global Patterns**: `"internal_*"` - Excludes any function starting with `internal_` in any file.
- **Scoped Literals**: `"src/app.py:main"` - Excludes the `main` function specifically in `src/app.py`.
- **Scoped Patterns**: `"src/*.py:*_helper"` - Excludes functions ending in `_helper` in any Python file under `src/`.

### `edits`

This dictionary is managed by the cleanup agent. Each key is an identifier for a refactored function (including its path and class name, if any), and the value is the 7-character commit hash of the parent commit (where the original code exists). This map is used by the agent when you request to **revert** a cleanup.

## Inline Comments

You can also use inline comments to ignore specific lines or blocks of code from the Code Slob Cleanup toolchain. This is useful for fine-grained control when you have deliberate "slob" that should not be refactored. You can also add custom comments after an ignore directive without affecting the functionality of the ignore.

### `cs-cleanup: ignore`

Add `# cs-cleanup: ignore` at the end of a line to prevent the scanner from flagging it.

```python
# Example: Ignoring a line
def complex_logic(a, b):
    if a > 0: # cs-cleanup: ignore
        return a + b
    return b
```

To ignore an entire function or block, place `# cs-cleanup: ignore-start` before the block and `# cs-cleanup: ignore-end` after it.

```python
# Example: Ignoring a function
# cs-cleanup: ignore-start
def intentionally_verbose_function():
    # This function is deliberately verbose for a reason
    print("Step 1")
    print("Step 2")
    # ... many more lines
    return True
# cs-cleanup: ignore-end

# Example: Ignoring a block within a function
def process_data(data):
    result = []
    # cs-cleanup: ignore-start
    for item in data:
        # This loop is intentionally expanded for performance/clarity
        temp = item * 2
        result.append(temp + 1)
    # cs-cleanup: ignore-end
    return result
```

### `cs-cleanup: ignore-file`

To ignore an entire file, add `# cs-cleanup: ignore-file` as the very first line of the file. This will prevent the Code Slob Cleanup toolchain from scanning or refactoring any part of that file.

```python
# cs-cleanup: ignore-file
# This entire file will be ignored by the Code Slob Cleanup toolchain.

def some_function():
    # ...
    pass

class SomeClass:
    # ...
    pass
```

### `cs-cleanup: ignore-function`

To ignore an entire function, add `# cs-cleanup: ignore-function` on the line immediately preceding the function definition. This will prevent the scanner from flagging any "slob" within that specific function.

```python
# Example: Ignoring a function with a single line directive
# cs-cleanup: ignore-function
def auto_generated_function(param1, param2):
    # This function is long but machine-generated, so it should be ignored.
    result = param1 * 2
    if param2 > 0:
        for i in range(param2):
            result += i
    return result
```

This ensures that the specified code sections are completely bypassed by the scanner and refactoring tools.
