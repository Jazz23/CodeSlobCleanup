# /// script
# dependencies = [
#     "radon",
# ]
# ///

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

def calculate_slob_score(code: str, complexity: int = None, lloc: int = None) -> float:
    """
    Heuristic score to determine if code is 'slob'.
    Higher is worse.
    
    Formula: (Complexity^2) + (LLOC / 5)
    """
    if complexity is None:
        complexity = calculate_complexity(code)
    if lloc is None:
        lloc = calculate_loc(code)
    
    # Penalize complexity heavily
    score = (complexity ** 2) + (lloc / 5.0)
    return round(score, 2)

def get_function_metrics(code: str):
    """
    Extracts metrics for individual functions and classes in the code.
    """
    try:
        blocks = cc.cc_visit(code)
        lines = code.splitlines()
        
        results = []
        for block in blocks:
            # Extract block source to calculate LLOC
            # block.lineno is 1-indexed. block.endline is also available in some radon versions.
            
            start = block.lineno - 1
            end = getattr(block, 'endline', len(lines))
            block_code = "\n".join(lines[start:end])
            
            lloc = calculate_loc(block_code)
            complexity = block.complexity
            score = calculate_slob_score(block_code, complexity=complexity, lloc=lloc)
            
            # Determine block type and privacy
            block_type = "Function"
            if hasattr(block, 'letter'):
                if block.letter == 'C':
                    block_type = "Class"
                elif block.letter == 'M':
                    block_type = "Method"
            
            is_private = block.name.startswith('_') and not (block.name.startswith('__') and block.name.endswith('__'))

            results.append({
                "name": block.name,
                "line": block.lineno,
                "end_line": end,
                "complexity": complexity,
                "loc": lloc,
                "score": score,
                "type": block_type,
                "is_private": is_private
            })
        return results
    except Exception:
        return []
