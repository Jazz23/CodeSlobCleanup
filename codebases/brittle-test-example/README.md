# Brittle Test Example

This codebase contains "code slob" in `src/app.py` and has both functional and brittle tests in `tests/test_app.py`.

## Slob Candidates
1. `format_user_list`: Inefficient string concatenation and global side-effect logging.
2. `calculate_stats`: Overly complex nesting for simple average calculation.

## Running Tests
To run the tests:
```bash
pytest
```
