# Global Variable Refactoring Test Case

This codebase demonstrates a common "slob" pattern where mutable application state is stored in global variables and modified using the `global` keyword.

## The Slob
- `CONFIG`, `DATABASE_CONNECTION`, and `PROCESS_COUNT` are globals.
- Functions rely on side effects rather than encapsulation.

## The Goal
Refactor this into a `Session` or `App` class to avoid global state.
