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
    candidates = []
    
    # Walk the directory
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                
                # Skip the report itself if it exists (though it's .json)
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    # Calculate metrics
                    complexity = metrics.calculate_complexity(content)
                    loc = metrics.calculate_loc(content)
                    score = metrics.calculate_slob_score(content)
                    
                    # Determine if slob
                    # Threshold: Score > 5.0
                    is_slob = score > 5.0
                    
                    candidates.append({
                        "file_path": str(file_path.relative_to(target_dir)),
                        "complexity": complexity,
                        "loc": loc,
                        "score": score,
                        "is_slob": is_slob
                    })
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)
                    
    return candidates

def main():
    parser = argparse.ArgumentParser(description="Scan directory for Code Slob.")
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to scan")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Scanning {target_dir}...")
    candidates = scan_directory(target_dir)
    
    # Sort by score descending (worst first)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    report = {
        "summary": {
            "total_files": len(candidates),
            "slob_candidates": sum(1 for c in candidates if c["is_slob"])
        },
        "candidates": candidates
    }
    
    report_path = target_dir / "scan_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Scan complete. Report written to {report_path}")
    print(f"Found {report['summary']['slob_candidates']} slob candidates.")

if __name__ == "__main__":
    main()
