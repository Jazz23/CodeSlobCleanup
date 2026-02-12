import radon.complexity as cc
import radon.raw as raw
import radon.metrics as met
import radon.visitors as visitors

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
    
    Formula: (Complexity^2) + ((LLOC / 10)^2)
    This punishes high complexity AND high verbosity non-linearly.
    """
    if complexity is None:
        complexity = calculate_complexity(code)
    if lloc is None:
        lloc = calculate_loc(code)
    
    # Penalize complexity and length non-linearly
    score = (complexity ** 2) + ((lloc / 10.0) ** 2)
    return round(score, 2)

def get_function_metrics(code: str):
    """
    Extracts metrics for individual functions and classes in the code.
    """
    try:
        # cc_visit returns a list of Function, Class, or Method objects
        blocks = cc.cc_visit(code)
        lines = code.splitlines()
        
        results = []
        for block in blocks:
            # Extract block source to calculate LLOC
            start = block.lineno - 1
            end = getattr(block, 'endline', len(lines))
            block_code = "\n".join(lines[start:end])
            
            lloc = calculate_loc(block_code)
            complexity = block.complexity
            
            item_type = "function"
            method_count = 0
            
            # Check if it's a class
            if isinstance(block, visitors.Class):
                item_type = "class"
                method_count = len(block.methods)
            elif isinstance(block, visitors.Function):
                item_type = "function"

            # Design Smell Detectors
            is_god_class = False
            is_data_class = False
            
            if item_type == "class":
                # God Class: Too many methods or too large
                if method_count > 7 or lloc > 100:
                    is_god_class = True
                
                # Data Class: Few methods, mostly definitions (heuristic)
                # If it's a class with 0-2 methods, it might be a data bucket
                if method_count <= 2 and lloc < 50:
                    is_data_class = True

            score = calculate_slob_score(block_code, complexity=complexity, lloc=lloc)
            
            results.append({
                "name": block.name,
                "type": item_type,
                "line": block.lineno,
                "complexity": complexity,
                "loc": lloc,
                "method_count": method_count,
                "is_god_class": is_god_class,
                "is_data_class": is_data_class,
                "score": score
            })
        return results
    except Exception as e:
        import sys
        print(f"Error in get_function_metrics: {e}", file=sys.stderr)
        return []
