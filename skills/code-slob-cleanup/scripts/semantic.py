import ast
import os
from typing import List, Dict, Any

def detect_global_variables(code: str) -> List[str]:
    """
    Detects top-level variable assignments that aren't constants (all caps).
    Global variables are often a sign of 'slob' in larger files.
    """
    try:
        tree = ast.parse(code)
        globals_found = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Filter out typical constants (SHOUTING_CASE)
                        if not target.id.isupper():
                            globals_found.append(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    if not node.target.id.isupper():
                        globals_found.append(node.target.id)
        return globals_found
    except Exception:
        return []

def analyze_class_structure(code: str) -> Dict[str, Any]:
    """
    Analyzes class usage, looking for:
    - Public vs Private classes.
    - Ratio of private classes.
    """
    try:
        tree = ast.parse(code)
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        
        public_classes = [c.name for c in classes if not c.name.startswith('_')]
        private_classes = [c.name for c in classes if c.name.startswith('_')]
        
        return {
            "total_classes": len(classes),
            "public_classes": public_classes,
            "private_classes": private_classes,
            "private_ratio": len(private_classes) / len(classes) if classes else 0
        }
    except Exception:
        return {"total_classes": 0, "public_classes": [], "private_classes": [], "private_ratio": 0}

def evaluate_semantic_relevance(file_path: str, code: str) -> Dict[str, Any]:
    """
    Heuristic to check if classes/functions match the filename.
    If there are many classes and they don't seem related to the file name, it's slob.
    """
    file_name = os.path.basename(file_path).replace(".py", "").lower()
    file_parts = set(file_name.split("_"))
    
    try:
        tree = ast.parse(code)
        classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        
        irrelevant_classes = []
        for cls_name in classes:
            cls_lower = cls_name.lower()
            # If no part of the filename is in the class name, it might be irrelevant
            if not any(part in cls_lower for part in file_parts):
                irrelevant_classes.append(cls_name)
        
        # A file with many classes where many are irrelevant is 'slobby'
        relevance_score = 1.0
        if classes:
            relevance_score = (len(classes) - len(irrelevant_classes)) / len(classes)
            
        return {
            "relevance_score": round(relevance_score, 2),
            "irrelevant_classes": irrelevant_classes,
            "is_potentially_misplaced": len(irrelevant_classes) > 1 and len(classes) > 3
        }
    except Exception:
        return {"relevance_score": 1.0, "irrelevant_classes": [], "is_potentially_misplaced": False}

def get_semantic_slob_score(file_path: str, code: str) -> float:
    """
    Calculates a semantic 'slob' penalty.
    """
    globals_list = detect_global_variables(code)
    class_info = analyze_class_structure(code)
    relevance = evaluate_semantic_relevance(file_path, code)
    
    penalty = 0.0
    
    # Penalty for global variables (5 points per global)
    penalty += len(globals_list) * 5.0
    
    # Penalty for too many public classes in one file (if > 3)
    if len(class_info["public_classes"]) > 3:
        penalty += (len(class_info["public_classes"]) - 3) * 10.0
        
    # Penalty for low relevance
    if relevance["relevance_score"] < 0.5:
        penalty += 30.0
        
    # Penalty for misplaced classes
    if relevance["is_potentially_misplaced"]:
        penalty += len(relevance["irrelevant_classes"]) * 10
        
    return round(penalty, 2)
