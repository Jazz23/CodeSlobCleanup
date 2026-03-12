# Code Quality Issues ("Slobs")

## 1. Code Duplication (Clones)

AI agents are notorious for "copy-pasting" logic across different files or functions instead of creating a shared utility.

**Why it's Slob:**  
It makes the codebase harder to maintain because a bug fix in one location must be manually repeated in others.

**How to identify:**  
Tools like `pylint` (via `duplicate-code`) or `flake8-duplicates` can detect this.

---

## 2. Deep Nesting (Indentation Debt)

While high Cyclomatic Complexity often correlates with nesting, deep indentation (e.g., **4+ levels** of `if`, `for`, and `while`) is a specific readability "slob."

**Why it's Slob:**  
It creates a "pyramid" of code that is mentally taxing to track.

**How to identify:**  
You can write a small `ast` visitor to count the maximum depth of a function's syntax tree.

---

## 3. Long Parameter Lists

Functions or methods that take **more than 5 or 6 arguments**.

**Why it's Slob:**  
It often indicates that a function is doing too much or that data should be grouped into a class or `dataclass`.

**How to identify:**  
Easily detectable via `ast` by checking the length of `node.args.args`.

---

## 4. "Silent" Error Handling

The presence of `bare except:` or `except Exception: pass` blocks.

**Why it's Slob:**  
It hides bugs and makes debugging nearly impossible.

*Example note:*  
`update_summary.py` currently uses a few of these in `count_repository_wide_metrics`.

**How to identify:**  
Search for `ast.ExceptHandler` nodes with an empty body or just a `pass`.

---

## 5. Hard-coded Magic Values

Strings, numbers, or paths hard-coded directly into logic instead of using constants or configuration.

**Why it's Slob:**  
It makes the code brittle and difficult to test across different environments.

**How to identify:**  
Look for literals (strings or numbers) inside function bodies that are not assigned to a named constant at the module level.

---

## 6. Dead Code & Unused Imports

Variables assigned but never used, or imports that were added during a "thought process" but never used in the final version.

**Why it's Slob:**  
It adds "noise" and increases the cognitive load for anyone reading the file.

**How to identify:**  
Tools like `vulture` or `ruff` are excellent at finding these.

---

## 7. Comment Redundancy

Comments that simply restate what the code does.

Example:
```python
# Increments x by 1
x += 1
```

