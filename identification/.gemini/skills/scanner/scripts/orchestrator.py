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
                        # Threshold from taskb2: complexity > 10, loc > 50, or high score
                        is_high_severity = m["complexity"] > 10 or m["loc"] > 50 or m["score"] > 50
                        
                        if is_high_severity:
                            slob_candidates.append({
                                "file": str(file_path.relative_to(target_dir)),
                                "function": m["name"],
                                "line": m["line"],
                                "metrics": {
                                    "complexity": m["complexity"],
                                    "loc": m["loc"],
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

if __name__ == "__main__":
    main()
