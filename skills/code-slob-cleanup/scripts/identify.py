# /// script
# dependencies = [
#     "radon",
# ]
# ///

import os
import sys
import json
import argparse
import ast
import re
from pathlib import Path
from collections import defaultdict

# Ensure we can import local modules
sys.path.append(str(Path(__file__).parent))

import metrics
import semantic
import exclusions

class CrossReferenceAnalyzer:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.definitions = defaultdict(set)
        self.files_content = {}
        self.used_outside = defaultdict(set)
        
    def add_file(self, file_path, content, func_metrics):
        # Track all public entities (classes, functions, methods) defined in the file
        public_names = {m["name"] for m in func_metrics if not m["is_private"]}
        self.definitions[file_path] = public_names
        self.files_content[file_path] = content
        
    def analyze(self):
        # Map potential module paths to their file paths
        module_to_file = {}
        for fpath in self.definitions.keys():
            rel = fpath.relative_to(self.target_dir)
            parts = list(rel.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts.pop()
            if not parts:
                continue
            
            # Allow multiple module resolution paths based on potential python paths
            for i in range(len(parts)):
                mod_name = ".".join(parts[i:])
                module_to_file[mod_name] = fpath
                
        # Parse all files to discover cross-references
        for fpath, content in self.files_content.items():
            try:
                tree = ast.parse(content)
            except Exception:
                continue
                
            imported_modules = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod_name = node.module
                    if node.level > 0:
                        # Handle relative imports
                        rel_parts = list(fpath.relative_to(self.target_dir).parts)[:-1]
                        for _ in range(node.level - 1):
                            if rel_parts: rel_parts.pop()
                        if mod_name:
                            full_mod = ".".join(rel_parts + mod_name.split("."))
                        else:
                            full_mod = ".".join(rel_parts)
                    else:
                        full_mod = mod_name
                    
                    target_file = module_to_file.get(full_mod)
                    if target_file and target_file != fpath:
                        imported_modules.add(target_file)
                        for alias in node.names:
                            if alias.name == "*":
                                self.used_outside[target_file].update(self.definitions[target_file])
                            elif alias.name in self.definitions[target_file]:
                                self.used_outside[target_file].add(alias.name)
                                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        target_file = module_to_file.get(alias.name)
                        if target_file and target_file != fpath:
                            import_alias = alias.asname or alias.name.split('.')[-1]
                            for subnode in ast.walk(tree):
                                if isinstance(subnode, ast.Attribute) and isinstance(subnode.value, ast.Name):
                                    if subnode.value.id == import_alias:
                                        if subnode.attr in self.definitions[target_file]:
                                            self.used_outside[target_file].add(subnode.attr)

            # For ast.ImportFrom, we already handled it by adding the names directly to self.used_outside
            # So we don't need a fallback rough text search anymore, making it more accurate and preventing cross-contamination of duplicate names.

def scan_directory(target_dir: Path):
    slob_candidates = []
    files_scanned = 0
    
    # Load configuration
    config = exclusions.load_config(target_dir)
    
    # Directories to exclude
    exclude_dirs = {".git", "venv", ".venv", "__pycache__", "tests", ".pytest_cache", ".gemini", ".code-slob-tmp"}
    
    # --- Pass 1: Collect Data ---
    file_data = []
    analyzer = CrossReferenceAnalyzer(target_dir)
    
    for root, dirs, files in os.walk(target_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py"):
                files_scanned += 1
                file_path = Path(root) / file
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    inline_excl = exclusions.get_inline_exclusions(str(file_path))
                    func_metrics = metrics.get_function_metrics(content)
                    
                    analyzer.add_file(file_path, content, func_metrics)
                    
                    semantic_score = semantic.get_semantic_slob_score(str(file_path), content)
                    semantic_info = semantic.evaluate_semantic_relevance(str(file_path), content)
                    global_vars = semantic.detect_global_variables(content)
                    
                    file_data.append({
                        "file_path": file_path,
                        "content": content,
                        "inline_excl": inline_excl,
                        "func_metrics": func_metrics,
                        "semantic_score": semantic_score,
                        "semantic_info": semantic_info,
                        "global_vars": global_vars
                    })
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    
    # --- Analyze Cross-References ---
    analyzer.analyze()
    
    # --- Pass 2: Determine Slob Candidates ---
    for data in file_data:
        file_path = data["file_path"]
        func_metrics = data["func_metrics"]
        semantic_score = data["semantic_score"]
        semantic_info = data["semantic_info"]
        global_vars = data["global_vars"]
        inline_excl = data["inline_excl"]
        
        for m in func_metrics:
            if exclusions.is_excluded(str(file_path), m["name"], m["line"], m["end_line"], config, str(target_dir), inline_excl):
                continue
                
            # Check if it's a public entity that is never used outside its defining file
            is_public_unused_outside = False
            is_dunder = m["name"].startswith('__') and m["name"].endswith('__')
            
            # Note: "main" is a common entrypoint, so we don't force it to be private.
            if not m["is_private"] and not is_dunder and m["name"] != "main":
                if m["name"] not in analyzer.used_outside.get(file_path, set()):
                    is_public_unused_outside = True
            
            # Determine overall slob severity
            total_score = m["score"] + semantic_score
            is_high_severity = m["complexity"] > 10 or m["loc"] > 50 or total_score > 100 or is_public_unused_outside
            
            if is_public_unused_outside:
                # Add a large penalty so it's prioritized for cleanup
                total_score += 150 

            slob_candidates.append({
                "file": str(file_path.relative_to(target_dir)),
                "function": m["name"],
                "line": m["line"],
                "type": m["type"],
                "is_private": m["is_private"],
                "is_public_unused_outside": is_public_unused_outside,
                "metrics": {
                    "complexity": m["complexity"],
                    "loc": m["loc"],
                    "slob_score": m["score"],
                    "semantic_penalty": semantic_score,
                    "total_score": round(total_score, 2)
                },
                "semantic_info": {
                    "relevance": semantic_info["relevance_score"],
                    "global_vars_count": len(global_vars),
                    "global_vars": global_vars
                },
                "high_severity": is_high_severity
            })

    return files_scanned, slob_candidates

def get_slob_classification(score):
    if score < 100:
        return "Low Slob"
    elif score <= 500:
        return "Moderate Slob"
    else:
        return "High Slob"

def main():
    parser = argparse.ArgumentParser(description="Scan directory for Code Slob.")
    parser.add_argument("target_dir", type=str, help="Directory to scan")
    parser.add_argument("--output", type=str, help="Output report file (optional JSON)")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    files_scanned, slob_candidates = scan_directory(target_dir)
    
    # Sort by score descending
    slob_candidates.sort(key=lambda x: x["metrics"]["total_score"], reverse=True)
    
    # Print summary
    print(f"--- Identification Summary ---")
    print(f"Files Scanned: {files_scanned}")
    print(f"Functions/Classes Found: {len(slob_candidates)}")
    print(f"Slob Candidates: {len([c for c in slob_candidates if c['high_severity']])}")
    print("------------------------------")
    
    for cand in slob_candidates:
        if cand["high_severity"]:
            score = cand["metrics"]["total_score"]
            classification = get_slob_classification(score)
            
            label = "[SLOB]"
            if cand.get("is_public_unused_outside"):
                label = "[SHOULD BE PRIVATE]"
            else:
                if cand["type"] == "Class":
                    label = "[PUBLIC CLASS]" if not cand["is_private"] else "[PRIVATE CLASS]"
                elif cand["type"] == "Method":
                    label = "[METHOD]"
                elif cand["type"] == "Function":
                    label = "[FUNCTION]"

            print(f"{label.ljust(20)} {cand['file']}::{cand['function']} (Line {cand['line']})")
            print(f"         Total Score: {score} ({classification}) (Complexity: {cand['metrics']['complexity']}, LOC: {cand['metrics']['loc']}, Semantic Penalty: {cand['metrics']['semantic_penalty']})")
            
            if cand.get("is_public_unused_outside"):
                print(f"         Reason: Public {cand['type'].lower()} is not used outside this file and should be private.")
                
            if cand["semantic_info"]["global_vars"]:
                globals_str = ", ".join([f"{g['name']} (Line {g['line']})" for g in cand["semantic_info"]["global_vars"]])
                print(f"         Globals Found: {len(cand['semantic_info']['global_vars'])}")
                print(f"         Globals Location: {globals_str}")
            if cand["semantic_info"]["relevance"] < 1.0:
                print(f"         Relevance: {cand['semantic_info']['relevance']}")
    
    if args.output:
        report = {
            "files_scanned": files_scanned,
            "slob_candidates": slob_candidates
        }
        report_path = Path(args.output)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report written to {report_path}")

if __name__ == "__main__":
    main()
