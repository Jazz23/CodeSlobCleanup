# /// script
# dependencies = [
#     "pytest",
#     "radon",
# ]
# ///

import pytest
import sys
from pathlib import Path

# Add scripts directory to path for import
# Current: identification/tests/unit/test_metrics.py
# Root: identification/
project_root = Path(__file__).resolve().parents[3]
metrics_path = project_root / "identification" / ".gemini" / "skills" / "scanner" / "scripts"
sys.path.append(str(metrics_path))

import metrics

SIMPLE_FUNC = """
def add(a, b):
    return a + b
"""

NESTED_FUNC = """
def complex_logic(n):
    if n > 0:
        if n % 2 == 0:
            return "even positive"
        else:
            return "odd positive"
    else:
        if n % 2 == 0:
            return "even negative"
        else:
            return "odd negative"
"""

LONG_FUNC = "def long_func():\n" + "\n".join([f"    a = {i}" for i in range(20)]) + "\n    return a"

def test_cyclomatic_complexity():
    """Verify that nested code has higher complexity."""
    simple_cc = metrics.calculate_complexity(SIMPLE_FUNC)
    nested_cc = metrics.calculate_complexity(NESTED_FUNC)
    
    assert simple_cc == 1
    assert nested_cc > 1

def test_function_length():
    """Verify detection of long functions."""
    simple_len = metrics.calculate_loc(SIMPLE_FUNC)
    long_len = metrics.calculate_loc(LONG_FUNC)
    
    assert simple_len < 5
    assert long_len > 20

def test_slob_score_heuristic():
    """Verify the scoring logic flags the nested/long code as 'slob'."""
    # Heuristic: Score = CC * 2 + LOC/10 (just an example)
    score_simple = metrics.calculate_slob_score(SIMPLE_FUNC)
    score_nested = metrics.calculate_slob_score(NESTED_FUNC)
    
    assert score_nested > score_simple

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
