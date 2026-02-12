import json
import argparse
import sys
from pathlib import Path

def print_histogram(scores, title="Slob Score Distribution"):
    if not scores:
        print("No scores to visualize.")
        return

    min_score = min(scores)
    max_score = max(scores)
    
    print(f"\n=== {title} ===")
    print(f"Count: {len(scores)}")
    print(f"Min: {min_score:.2f} | Max: {max_score:.2f}")
    
    # Create bins
    bins = [0, 20, 40, 60, 80, 100, float('inf')]
    labels = ["0-20", "20-40", "40-60", "60-80", "80-100", "100+"]
    counts = [0] * len(labels)
    
    for s in scores:
        for i, val in enumerate(bins[:-1]):
            upper = bins[i+1]
            if s >= val and s < upper:
                counts[i] += 1
                break
    
    # Print bars
    print("-" * 40)
    max_count = max(counts) if counts else 1
    scale = 30.0 / max_count if max_count > 0 else 1
    
    for i, label in enumerate(labels):
        count = counts[i]
        bar = "#" * int(count * scale)
        print(f"{label:<8} | {bar} ({count})")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Visualize Slob Scores.")
    parser.add_argument("--report", type=str, required=True, help="Path to scan_report.json")
    
    args = parser.parse_args()
    report_path = Path(args.report).resolve()
    
    if not report_path.exists():
        print(f"Error: Report file {report_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
            
        candidates = data.get("slob_candidates", [])
        scores = [c["metrics"]["slob_score"] for c in candidates]
        
        print_histogram(scores)
        
    except Exception as e:
        print(f"Error processing report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
