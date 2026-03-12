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
    
    # If user provided ANY flags via CLI, we run custom aggregation matching those flags.
    # Otherwise, we only print Inferred Flags and do not show candidates.
    user_provided_flags = args.global_variables or args.complexity or args.lloc or args.public_private
    
    if not user_provided_flags:
        # Auto-detect prominent slob factors
        total_globals = sum(len(c["semantic_info"]["global_vars"]) for c in slob_candidates)
        avg_complexity = sum(c["metrics"]["complexity"] for c in slob_candidates) / len(slob_candidates) if slob_candidates else 0
        avg_loc = sum(c["metrics"]["loc"] for c in slob_candidates) / len(slob_candidates) if slob_candidates else 0
        
        # Count classes vs private classes
        public_classes = len([c for c in slob_candidates if c["type"] == "Class" and not c["is_private"]])
        private_classes = len([c for c in slob_candidates if c["type"] == "Class" and c["is_private"]])
        
        inferred = []
        if total_globals > 0:
            inferred.append("--global-variables")
        if public_classes > private_classes or public_classes > 5:
            inferred.append("--public-private")
        if avg_complexity > 5:
            inferred.append("--complexity")
        if avg_loc > 100:
            inferred.append("--lloc")
            
        if inferred:
            print(f"Inferred Flags for Repository: {' '.join(inferred)}")
        else:
            print("Inferred Flags for Repository: None")
            
        return  # Do not output anything else if no CLI flags were given
        
    filtered_candidates = []
    
    # Custom Aggregation logic if flags are given
    if user_provided_flags:
        total_repo_score = sum(c["metrics"]["total_score"] for c in slob_candidates)
        
        if args.global_variables:
            total_globals = sum(len(c["semantic_info"]["global_vars"]) for c in slob_candidates)
            print(f"\n[GLOBAL VARIABLES]")
            print(f"Total Repository Slob Score: {total_repo_score:.2f}")
            print(f"Total Global Variables: {total_globals}")
            
            # Group by file and count globals
            file_globals = {}
            for c in slob_candidates:
                f = c["file"]
                if f not in file_globals:
                    file_globals[f] = {"globals": 0, "score": 0}
                file_globals[f]["globals"] += len(c["semantic_info"]["global_vars"])
                file_globals[f]["score"] += c["metrics"]["total_score"]
            top_3 = sorted(file_globals.items(), key=lambda x: x[1]["globals"], reverse=True)[:3]
            print("\nTop 3 Files (Most Globals):")
            for f, data in top_3:
                print(f"  - {f} (Globals: {data['globals']}, Score: {data['score']:.2f})")

        if args.complexity:
            print(f"\n[COMPLEXITY]")
            print(f"Total Repository Slob Score: {total_repo_score:.2f}")
            
            # Group by file and sum complexity
            file_complexity = {}
            for c in slob_candidates:
                f = c["file"]
                if f not in file_complexity:
                    file_complexity[f] = {"complexity": 0, "score": 0}
                file_complexity[f]["complexity"] += c["metrics"]["complexity"]
                file_complexity[f]["score"] += c["metrics"]["total_score"]
            top_3 = sorted(file_complexity.items(), key=lambda x: x[1]["complexity"], reverse=True)[:3]
            print("\nTop 3 Files (Highest Complexity):")
            for f, data in top_3:
                print(f"  - {f} (Cumulative Complexity: {data['complexity']}, Score: {data['score']:.2f})")

        if args.lloc:
            print(f"\n[LOGICAL LOC (God Classes/Funcs)]")
            print(f"Total Repository Slob Score: {total_repo_score:.2f}")
            
            # Group by file and sum LLOC
            file_lloc = {}
            for c in slob_candidates:
                f = c["file"]
                if f not in file_lloc:
                    file_lloc[f] = {"lloc": 0, "score": 0}
                file_lloc[f]["lloc"] += c["metrics"]["loc"]
                file_lloc[f]["score"] += c["metrics"]["total_score"]
            top_3 = sorted(file_lloc.items(), key=lambda x: x[1]["lloc"], reverse=True)[:3]
            print("\nTop 3 Files (Largest LOC):")
            for f, data in top_3:
                print(f"  - {f} (Cumulative LLOC: {data['lloc']}, Score: {data['score']:.2f})")

        if args.public_private:
            print(f"\n[PUBLIC TO PRIVATE]")
            print(f"Total Repository Slob Score: {total_repo_score:.2f}")
            
            # Group by file and count public classes/methods
            file_public = {}
            for c in slob_candidates:
                if not c["is_private"] and c["type"] in ["Class", "Method"]:
                    f = c["file"]
                    if f not in file_public:
                        file_public[f] = {"public_count": 0, "score": 0}
                    file_public[f]["public_count"] += 1
                    file_public[f]["score"] += c["metrics"]["total_score"]
            top_3 = sorted(file_public.items(), key=lambda x: x[1]["public_count"], reverse=True)[:3]
            print("\nTop 3 Files (Most Public Members that might be private):")
            for f, data in top_3:
                print(f"  - {f} (Public Candidates: {data['public_count']}, Score: {data['score']:.2f})")
    
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

