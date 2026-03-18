import ast
import hashlib

class FunctionalNormalizer(ast.NodeTransformer):
    def __init__(self):
        self.var_map = {}
        self.var_count = 0

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Param)):
            # We only rename names that are likely local variables or parameters
            # This is a bit risky but good enough for a heuristic
            if node.id not in self.var_map:
                self.var_map[node.id] = f"var_{self.var_count}"
                self.var_count += 1
            return ast.copy_location(ast.Name(id=self.var_map[node.id], ctx=node.ctx), node)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Rename function to a constant for hashing
        return ast.copy_location(
            ast.FunctionDef(
                name="normalized_func",
                args=self.visit(node.args),
                body=[self.visit(step) for step in node.body],
                decorator_list=[self.visit(dec) for dec in node.decorator_list],
                returns=self.visit(node.returns) if node.returns else None,
                type_comment=node.type_comment
            ),
            node
        )

    def visit_AsyncFunctionDef(self, node):
        # Rename async function to a constant for hashing
        return ast.copy_location(
            ast.AsyncFunctionDef(
                name="normalized_func",
                args=self.visit(node.args),
                body=[self.visit(step) for step in node.body],
                decorator_list=[self.visit(dec) for dec in node.decorator_list],
                returns=self.visit(node.returns) if node.returns else None,
                type_comment=node.type_comment
            ),
            node
        )

    def visit_ClassDef(self, node):
        # Rename class to a constant for hashing
        return ast.copy_location(
            ast.ClassDef(
                name="NormalizedClass",
                bases=[self.visit(base) for base in node.bases],
                keywords=[self.visit(kw) for kw in node.keywords],
                body=[self.visit(step) for step in node.body],
                decorator_list=[self.visit(dec) for dec in node.decorator_list]
            ),
            node
        )

    def visit_arg(self, node):
        if node.arg not in self.var_map:
            self.var_map[node.arg] = f"var_{self.var_count}"
            self.var_count += 1
        return ast.copy_location(ast.arg(arg=self.var_map[node.arg], annotation=self.visit(node.annotation) if node.annotation else None, type_comment=node.type_comment), node)

def normalize_code(code: str) -> str:
    """
    Normalizes Python code by parsing it into an AST, stripping docs/comments,
    and renaming identifiers to placeholders to catch functional clones.
    """
    try:
        tree = ast.parse(code)
        
        # Remove docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                    node.body.pop(0)
        
        # Rename identifiers for functional clone detection
        tree = FunctionalNormalizer().visit(tree)
                    
        return ast.unparse(tree).strip()
    except Exception:
        return code.strip()

def get_code_hash(code: str) -> str:
    """
    Returns a SHA-256 hash of the normalized code.
    """
    normalized = normalize_code(code)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def find_duplicates(candidates):
    """
    Groups candidates by their code hash and identifies duplicates.
    Expects each candidate to have a 'raw_code' field.
    """
    hash_map = {}
    
    for cand in candidates:
        if "raw_code" not in cand:
            continue
            
        c_hash = get_code_hash(cand["raw_code"])
        cand["code_hash"] = c_hash
        
        if c_hash not in hash_map:
            hash_map[c_hash] = []
        hash_map[c_hash].append(cand)
        
    # Mark duplicates in candidates
    for c_hash, group in hash_map.items():
        if len(group) > 1:
            for cand in group:
                cand["is_duplicate"] = True
                # Store references to copies for reporting
                cand["duplicate_locations"] = [
                    f"{c['file']}::{c['function']} (Line {c['line']})"
                    for c in group if c != cand
                ]
        else:
            for cand in group:
                cand["is_duplicate"] = False
                cand["duplicate_locations"] = []
                
    return candidates

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Utility for detecting duplicate code blocks using AST normalization.")
    parser.parse_args()
