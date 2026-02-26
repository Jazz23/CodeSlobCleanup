# /// script
# dependencies = [
#     "radon",
# ]
# ///

import os
import sys
import json
import csv
import ast
import argparse
from pathlib import Path

# Ensure we can import local modules from the skills script directory
SKILLS_DIR = Path(__file__).parent
sys.path.append(str(SKILLS_DIR))

import metrics
import semantic
import identify

def count_repository_wide_metrics(target_dir):
    """Counts total files, classes and functions across the entire directory (no exclusions)."""
    total_files = 0
    total_classes = 0
    total_functions = 0
    private_classes_exist = False
    
    # We include EVERYTHING for the 'Total' metrics as per user's earlier manual requests
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                try:
                    path = os.path.join(root, file)
                    content = open(path, encoding="utf-8").read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            total_classes += 1
                            if node.name.startswith("_"):
                                private_classes_exist = True
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            total_functions += 1
                except:
                    pass
    return total_files, total_classes, total_functions, "Yes" if private_classes_exist else "No"

def analyze_top_slob(candidates):
    """Heuristically determines the top slob factor and a rationale string."""
    if not candidates:
        return "Clean", "No high-severity candidates found."
    
    high_sev = [c for c in candidates if c["high_severity"]]
    if not high_sev:
        return "Minor Debt", f"{len(candidates)} functions found, none meet high-severity thresholds."
    
    # Sort to find the worst offender
    worst = max(high_sev, key=lambda x: x["metrics"]["total_score"])
    
    # Determine Factor
    factors = []
    if worst["metrics"]["complexity"] > 15:
        factors.append("Complex Logic")
    if worst["metrics"]["loc"] > 100:
        factors.append("God Classes")
    if worst["metrics"]["semantic_penalty"] > 50:
        if len(worst["semantic_info"]["global_vars"]) > 5:
            factors.append("Global State Sprawl")
        if worst["semantic_info"]["relevance"] < 0.5:
            factors.append("Semantic Misalignment")
            
    top_factor = " & ".join(factors) if factors else "Utility Complexity"
    
    # Generate Rationale
    rationale = f"{len(high_sev)} candidates identified. Worst offender is {worst['file']}::{worst['function']} (Score: {worst['metrics']['total_score']}). "
    if "Global State Sprawl" in top_factor:
        rationale += f"Significant global variable usage detected ({len(worst['semantic_info']['global_vars'])} in one file)."
    elif "Complex Logic" in top_factor:
        rationale += f"Individual function complexity (CC={worst['metrics']['complexity']}) is the primary driver."
    elif "Semantic Misalignment" in top_factor:
        rationale += "Low semantic relevance between naming and file purpose identified."
    else:
        rationale += "Driven primarily by code verbosity and sheer block size."
        
    return top_factor, rationale

def main():
    parser = argparse.ArgumentParser(description="Automated update for github_test_summary.csv")
    parser.add_argument("--repo", type=str, nargs="+", help="Repository name(s) (e.g., 'flask' or 'flask requests'). Use 'all' to scan all in codebases/.")
    parser.add_argument("--all", action="store_true", help="Scan all repositories in the codebases directory.")
    parser.add_argument("--summary-file", type=str, required=True, help="Path to github_test_summary.csv")
    parser.add_argument("--init", action="store_true", help="Clear the summary file before adding new results.")

    args = parser.parse_args()
    
    # Use script location to find project root (CodeSlobCleanup/)
    # script is in skills/code-slob-cleanup/scripts/
    # 1: scripts, 2: code-slob-cleanup, 3: skills, 4: CodeSlobCleanup
    project_root = Path(__file__).parent.parent.parent.parent.resolve()
    codebases_root = project_root / "codebases"
    summary_file = Path(args.summary_file).resolve()

    repos_to_scan = []
    if args.all or (args.repo and "all" in args.repo):
        if not codebases_root.exists():
            print(f"Error: {codebases_root} not found.")
            sys.exit(1)
        repos_to_scan = [d.name for d in codebases_root.iterdir() if d.is_dir()]
    elif args.repo:
        repos_to_scan = args.repo
    else:
        print("Error: Must provide --repo <name> or --all.")
        sys.exit(1)

    # 7. Handle existing data
    rows = []
    header = []
    if not args.init and summary_file.exists():
        with open(summary_file, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            if header:
                rows = [row for row in reader]

    for repo_input in repos_to_scan:
        # Clean repo name in case user includes 'codebases/' or a full path
        repo_name = Path(repo_input).name
        target_dir = (codebases_root / repo_name).resolve()
        
        if not target_dir.exists():
            print(f"Skipping {repo_name}: Directory {target_dir} does not exist.")
            continue
            
        print(f"\n>>> Processing {repo_name}...")
        
        # 1. Run the scan (using identify's logic)
        files_scanned, candidates = identify.scan_directory(target_dir)
        
        # 2. Extract metrics
        total_score = sum(c["metrics"]["total_score"] for c in candidates)
        slob_candidates_count = len([c for c in candidates if c["high_severity"]])
        
        # 3. Analyze semantic aggregations for CSV columns
        seen_files = {}
        relevance_scores = []
        for cand in candidates:
            f = cand["file"]
            if f not in seen_files:
                seen_files[f] = len(cand["semantic_info"]["global_vars"])
                relevance_scores.append(cand["semantic_info"]["relevance"])
                
        total_globals = sum(seen_files.values())
        avg_relevance = round(sum(relevance_scores) / len(relevance_scores), 2) if relevance_scores else 1.0
        
        # 4. Get repo-wide baseline metrics
        total_files, total_classes, total_funcs, private_exists = count_repository_wide_metrics(target_dir)
        
        # 5. Generate qualitative data
        factor, rationale = analyze_top_slob(candidates)
        
        # 6. Prepare Row
        new_row = {
            "Repository": repo_name,
            "Total Slob Score": f"{total_score:.2f}",
            "Total Files": total_files,
            "Files Scanned": files_scanned,
            "Slob Candidates": slob_candidates_count,
            "Top Slob Factor": factor,
            "Rationale": rationale,
            "Global Variables": total_globals,
            "Private Classes Exist?": private_exists,
            "Classes Relevance": f"{avg_relevance:.2f}",
            " Total Classes": f" {total_classes}",
            " Total Functions": f" {total_funcs}"
        }

        # Remove existing entry for this repo if it exists in current rows
        rows = [r for r in rows if r["Repository"] != repo_name]
        rows.append(new_row)
        print(f"Aggregated data for {repo_name}.")

    # 8. Save/Update CSV
    # Sort rows by repository name
    rows.sort(key=lambda x: x["Repository"])
    
    with open(summary_file, mode="w", newline="") as f:
        # Update header to include all keys from the latest entries
        current_keys = set()
        for row in rows:
            current_keys.update(row.keys())
        
        # Ensure 'Repository' is first if we're building from scratch
        if not header:
            header = ["Repository", "Total Slob Score", "Total Files", "Files Scanned", "Slob Candidates", 
                     "Top Slob Factor", "Rationale", "Global Variables", "Private Classes Exist?", 
                     "Classes Relevance", " Total Classes", " Total Functions"]
        else:
            # Add any new keys that might have been added
            for key in sorted(current_keys):
                if key not in header:
                    header.append(key)
                    
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"\nSuccessfully updated {summary_file} with {len(repos_to_scan)} repositories.")

if __name__ == "__main__":
    main()
