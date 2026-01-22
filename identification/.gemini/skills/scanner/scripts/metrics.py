import radon.complexity as cc
import radon.raw as raw
import radon.metrics as met

def calculate_complexity(code: str) -> int:
    """
    Calculates the average Cyclomatic Complexity of the code.
    Returns the max complexity found in any block, or 1 if simple.
    """
    try:
        blocks = cc.cc_visit(code)
        if not blocks:
            return 1
        # Return the maximum complexity found
        return max(block.complexity for block in blocks)
    except Exception:
        return 1

def calculate_loc(code: str) -> int:
    """
    Calculates the Logical Lines of Code (LLOC) - excluding comments/docs.
    """
    try:
        analysis = raw.analyze(code)
        return analysis.lloc
    except Exception:
        return len(code.splitlines())

def calculate_halstead(code: str) -> float:
    """
    Calculates Halstead volume/effort.
    """
    try:
        h = met.h_visit(code)
        return h.effort
    except Exception:
        return 0.0

def calculate_slob_score(code: str) -> float:
    """
    Heuristic score to determine if code is 'slob'.
    Higher is worse.
    
    Formula: (Complexity^2) + (LLOC / 5)
    """
    complexity = calculate_complexity(code)
    lloc = calculate_loc(code)
    
    # Penalize complexity heavily
    score = (complexity ** 2) + (lloc / 5.0)
    return round(score, 2)
