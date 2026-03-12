# /// script
# dependencies = [
#     "radon",
# ]
# ///

import os
import sys
import json
import argparse
from pathlib import Path

# Ensure we can import local modules
sys.path.append(str(Path(__file__).parent))

import metrics
import semantic
import exclusions
import duplication

def scan_directory(target_dir: Path):
    slob_candidates = []
    files_scanned = 0
    
    # Load configuration
    config = exclusions.load_config(target_dir)
    
    # Directories to exclude
    exclude_dirs = {".git", "venv", ".venv", "__pycache__", "tests", ".pytest_cache", ".gemini", ".code-slob-tmp"}
    
    # Walk the directory
    for root, dirs, files in os.walk(target_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py"):
                files_scanned += 1
                file_path = Path(root) / file
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    # Get inline exclusions
                    inline_excl = exclusions.get_inline_exclusions(str(file_path))
                    
                    # Get per-function metrics
                    func_metrics = metrics.get_function_metrics(content)
                    
                    # Get semantic metrics
                    semantic_score = semantic.get_semantic_slob_score(str(file_path), content)
                    semantic_info = semantic.evaluate_semantic_relevance(str(file_path), content)
                    global_vars = semantic.detect_global_variables(content)

                    for m in func_metrics:
                        # Check if function is excluded
                        if exclusions.is_excluded(str(file_path), m["name"], m["line"], m["end_line"], config, str(target_dir), inline_excl):
                            continue
                            
                        # Determine if slob
                        # Thresholds
                        # Combined score includes semantic penalty
                        total_score = m["score"] + semantic_score
                        is_high_severity = m["complexity"] > 10 or m["loc"] > 50 or total_score > 100
                        
                        slob_candidates.append({
                            "file": str(file_path.relative_to(target_dir)),
                            "function": m["name"],
                            "line": m["line"],
                            "type": m["type"],
                            "is_private": m["is_private"],
                            "raw_code": m.get("raw_code", ""),
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
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    
    # Find duplicates
    slob_candidates = duplication.find_duplicates(slob_candidates)
    
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
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to scan")
    parser.add_argument("--output", type=str, help="Output report file (optional JSON)")
    
    # Feature Flags
    parser.add_argument("--global-variables", action="store_true", help="Filter for globals")
    parser.add_argument("--complexity", action="store_true", help="Filter for high complexity")
    parser.add_argument("--lloc", action="store_true", help="Filter for long logic (god functions/classes)")
    parser.add_argument("--public-private", action="store_true", help="Filter for public classes/methods that could be private")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    files_scanned, slob_candidates = scan_directory(target_dir)
    
    # Sort by score descending
    slob_candidates.sort(key=lambda x: x["metrics"]["total_score"], reverse=True)
    
    # Print summary for the Agent to see
    print(f"--- Identification Summary ---")
    print(f"Files Scanned: {files_scanned}")
    print(f"Functions Found: {len(slob_candidates)}")
    print(f"Slob Candidates: {len([c for c in slob_candidates if c['high_severity']])}")
    print("------------------------------")
    
    # If no filters were explicitly provided, try to infer them from the candidates
    filters_active = args.global_variables or args.complexity or args.lloc or args.public_private
    
    if not filters_active and slob_candidates:
        # Auto-detect prominent slob factors
        total_globals = sum(len(c["semantic_info"]["global_vars"]) for c in slob_candidates)
        avg_complexity = sum(c["metrics"]["complexity"] for c in slob_candidates) / len(slob_candidates)
        avg_loc = sum(c["metrics"]["loc"] for c in slob_candidates) / len(slob_candidates)
        
        # Count classes vs private classes
        public_classes = len([c for c in slob_candidates if c["type"] == "Class" and not c["is_private"]])
        private_classes = len([c for c in slob_candidates if c["type"] == "Class" and c["is_private"]])
        
        inferred = []
        if total_globals > 0:
            args.global_variables = True
            inferred.append("--global-variables")
        if public_classes > private_classes or public_classes > 5:
            args.public_private = True
            inferred.append("--public-private")
        if avg_complexity > 5:
            args.complexity = True
            inferred.append("--complexity")
        if avg_loc > 100:
            args.lloc = True
            inferred.append("--lloc")
            
        if inferred:
            print(f"Inferred Flags for Repository: {' '.join(inferred)}")
            filters_active = True
        else:
            print("Inferred Flags for Repository: None")
            
    filtered_candidates = []
    
    for cand in slob_candidates:
        if cand["high_severity"] or cand.get("is_duplicate"):
            # Check against filters if any are active
            if filters_active:
                matches_filter = False
                
                if args.global_variables and len(cand["semantic_info"]["global_vars"]) > 0:
                    matches_filter = True
                if args.complexity and cand["metrics"]["complexity"] > 10:
                    matches_filter = True
                if args.lloc and cand["metrics"]["loc"] > 50:
                    matches_filter = True
                if args.public_private and \
                   not cand["is_private"] and \
                   cand["type"] in ["Class", "Method"]:
                    matches_filter = True
                    
                if not matches_filter:
                    continue  # Skip this candidate because it didn't match the required filters
            
            filtered_candidates.append(cand)
            
            score = cand["metrics"]["total_score"]
            classification = get_slob_classification(score)
            
            label = "[SLOB]"
            if cand.get("is_duplicate") and not cand["high_severity"]:
                label = "[CLONE]"
            
            if cand["type"] == "Class":
                if cand.get("is_duplicate"):
                    label = "[DUPLICATE CLASS]"
                else:
                    label = "[PUBLIC CLASS]" if not cand["is_private"] else "[PRIVATE CLASS]"
            elif cand["type"] == "Method":
                label = "[METHOD]"
            elif cand["type"] == "Function":
                if not label == "[CLONE]" and not label == "[SLOB]":
                    label = "[FUNCTION]"

            print(f"{label.ljust(16)} {cand['file']}::{cand['function']} (Line {cand['line']})")
            if cand.get("is_duplicate"):
                print(f"         [DUPLICATE] Matches: {', '.join(cand['duplicate_locations'])}")
            print(f"         Total Score: {score} ({classification}) (Complexity: {cand['metrics']['complexity']}, LOC: {cand['metrics']['loc']}, Semantic Penalty: {cand['metrics']['semantic_penalty']})")
            if cand["semantic_info"]["global_vars"]:
                globals_str = ", ".join([f"{g['name']} (Line {g['line']})" for g in cand["semantic_info"]["global_vars"]])
                print(f"         Globals Found: {len(cand['semantic_info']['global_vars'])}")
                print(f"         Globals Location: {globals_str}")
            if cand["semantic_info"]["relevance"] < 1.0:
                print(f"         Relevance: {cand['semantic_info']['relevance']}")
    
    if args.output:
        report = {
            "files_scanned": files_scanned,
            "slob_candidates": filtered_candidates
        }
        report_path = Path(args.output)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report written to {report_path}")

if __name__ == "__main__":
    main()

