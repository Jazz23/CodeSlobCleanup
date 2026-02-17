# /// script
# dependencies = [
#     "radon",
# ]
# ///

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from collections import Counter

# Ensure we can import local modules
sys.path.append(str(Path(__file__).parent))

import metrics

def scan_directory(target_dir: Path):
    slob_candidates = []
    files_scanned = 0
    
    # Directories to exclude
    exclude_dirs = {".git", "venv", ".venv", "__pycache__", "tests", ".pytest_cache", ".gemini"}
    
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
                    
                    for m in func_metrics:
                        # Determine if slob
                        # Thresholds:
                        # - Complexity > 10
                        # - Loc > 50
                        # - Slob Score > 50
                        # - Design Smells (God Class / Data Class)
                        
                        is_god_class = m.get("is_god_class", False)
                        is_data_class = m.get("is_data_class", False)
                        
                        is_high_severity = (
                            m["complexity"] > 10 or 
                            m["loc"] > 50 or 
                            m["score"] > 50 or
                            is_god_class or
                            is_data_class
                        )
                        
                        if is_high_severity:
                            slob_candidates.append({
                                "file": str(file_path.relative_to(target_dir)),
                                "function": m["name"],
                                "type": m.get("type", "unknown"),
                                "line": m["line"],
                                "metrics": {
                                    "complexity": m["complexity"],
                                    "loc": m["loc"],
                                    "method_count": m.get("method_count", 0),
                                    "is_god_class": is_god_class,
                                    "is_data_class": is_data_class,
                                    "slob_score": m["score"]
                                },
                                "high_severity": is_high_severity
                            })
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    
    return files_scanned, slob_candidates

def main():
    parser = argparse.ArgumentParser(description="Scan directory for Code Slob.")
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to scan")
    parser.add_argument("--output", type=str, default="scan_report.json", help="Output report file")
    parser.add_argument("--append-csv", type=str, help="Append summary to CSV file")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Scanning {target_dir}...")
    files_scanned, slob_candidates = scan_directory(target_dir)
    
    # Sort by score descending
    slob_candidates.sort(key=lambda x: x["metrics"]["slob_score"], reverse=True)
    
    report = {
        "files_scanned": files_scanned,
        "slob_candidates": slob_candidates
    }
    
    report_path = Path(args.output)
    if not report_path.is_absolute():
        report_path = target_dir / report_path
        
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Scan complete. Scanned {files_scanned} files.")
    print(f"Report written to {report_path}")
    print(f"Found {len(slob_candidates)} slob candidates.")

    if args.append_csv:
        total_slob_score = sum(c["metrics"]["slob_score"] for c in slob_candidates)
        
        # Determine Top Slob Factor
        factors = []
        for c in slob_candidates:
            if c["metrics"]["is_god_class"]: factors.append("God Classes")
            elif c["metrics"]["is_data_class"]: factors.append("Data Classes")
            elif c["metrics"]["complexity"] > 20: factors.append("Complex Logic")
            else: factors.append("General Maintenance")
        
        top_factor = Counter(factors).most_common(1)[0][0] if factors else "N/A"
        
        # Generate Rationale
        repo_name = target_dir.name
        if slob_candidates:
            top_c = slob_candidates[0]
            rationale = f"Scanned {files_scanned} files. Top issue: {top_c['file']}:{top_c['function']} with score {top_c['metrics']['slob_score']:.1f}."
            if top_c["metrics"]["is_god_class"]:
                rationale += f" God Class detected with {top_c['metrics']['method_count']} methods."
        else:
            rationale = f"No significant slob detected across {files_scanned} files."
            
        csv_path = Path(args.append_csv).resolve()
        file_exists = csv_path.exists()
        
        try:
            with open(csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Repository", "Total Slob Score", "Files Scanned", "Slob Candidates", "Top Slob Factor", "Rationale"])
                writer.writerow([repo_name, round(total_slob_score, 2), files_scanned, len(slob_candidates), top_factor, rationale])
            print(f"Summary appended to {csv_path}")
        except Exception as e:
            print(f"Error writing to CSV: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
