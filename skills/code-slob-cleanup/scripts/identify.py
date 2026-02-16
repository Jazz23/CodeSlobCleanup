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

def scan_directory(target_dir: Path):
    slob_candidates = []
    files_scanned = 0
    
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
                    
                    # Get per-function metrics
                    func_metrics = metrics.get_function_metrics(content)
                    
                    # Get semantic metrics
                    semantic_score = semantic.get_semantic_slob_score(str(file_path), content)
                    semantic_info = semantic.evaluate_semantic_relevance(str(file_path), content)
                    global_vars = semantic.detect_global_variables(content)

                    for m in func_metrics:
                        # Determine if slob
                        # Thresholds
                        # Combined score includes semantic penalty
                        total_score = m["score"] + semantic_score
                        is_high_severity = m["complexity"] > 10 or m["loc"] > 50 or total_score > 100
                        
                        slob_candidates.append({
                            "file": str(file_path.relative_to(target_dir)),
                            "function": m["name"],
                            "line": m["line"],
                            "metrics": {
                                "complexity": m["complexity"],
                                "loc": m["loc"],
                                "slob_score": m["score"],
                                "semantic_penalty": semantic_score,
                                "total_score": round(total_score, 2)
                            },
                            "semantic_info": {
                                "relevance": semantic_info["relevance_score"],
                                "global_vars_count": len(global_vars)
                            },
                            "high_severity": is_high_severity
                        })
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    
    return files_scanned, slob_candidates

def main():
    parser = argparse.ArgumentParser(description="Scan directory for Code Slob.")
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to scan")
    parser.add_argument("--output", type=str, help="Output report file (optional JSON)")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    files_scanned, slob_candidates = scan_directory(target_dir)
    
    # Sort by score descending
    slob_candidates.sort(key=lambda x: x["metrics"]["slob_score"], reverse=True)
    
    # Print summary for the Agent to see
    print(f"--- Identification Summary ---")
    print(f"Files Scanned: {files_scanned}")
    print(f"Functions Found: {len(slob_candidates)}")
    print(f"Slob Candidates: {len([c for c in slob_candidates if c['high_severity']])}")
    print("------------------------------")
    
    for cand in slob_candidates:
        if cand["high_severity"]:
            print(f"[SLOB]   {cand['file']}::{cand['function']} (Line {cand['line']})")
            print(f"         Total Score: {cand['metrics']['total_score']} (Complexity: {cand['metrics']['complexity']}, LOC: {cand['metrics']['loc']}, Semantic Penalty: {cand['metrics']['semantic_penalty']})")
            if cand["semantic_info"]["global_vars_count"] > 0:
                print(f"         Globals Found: {cand['semantic_info']['global_vars_count']}")
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
