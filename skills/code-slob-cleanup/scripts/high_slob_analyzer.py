# /// script
# dependencies = [
#     "radon",
# ]
# ///

import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Ensure we can import local modules
sys.path.append(str(Path(__file__).parent))

import identify

def main():
    parser = argparse.ArgumentParser(description="Analyze 'High Slob' scripts and prioritize refactoring.")
    parser.add_argument("--target-dir", type=str, required=True, help="Directory to scan")
    parser.add_argument("--refactor-limit", type=float, default=5000.0, help="Cumulative score threshold for the 'Need to Refactor' section")
    
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    
    if not target_dir.exists():
        print(f"Error: Target directory {target_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
        
    print(f"\n🔍 Scanning {target_dir.name} for high-impact slob...")
    files_scanned, candidates = identify.scan_directory(target_dir)
    
    # Group by file
    file_stats = defaultdict(lambda: {"total_score": 0.0, "high_slob_count": 0, "functions": []})
    
    for cand in candidates:
        fname = cand["file"]
        score = cand["metrics"]["total_score"]
        file_stats[fname]["total_score"] += score
        file_stats[fname]["functions"].append(cand)
        if score > 500: # Threshold for 'High Slob' function
            file_stats[fname]["high_slob_count"] += 1
            
    # Identify 'High Slob' scripts (those with at least one high-slob function)
    high_slob_scripts = [f for f, stats in file_stats.items() if stats["high_slob_count"] > 0]
    high_slob_scripts.sort(key=lambda f: file_stats[f]["total_score"], reverse=True)
    
    # 1. Display Number and Names of High Slob Scripts
    print("\n" + "="*50)
    print(f"📉 HIGH SLOB SCRIPTS DETECTED: {len(high_slob_scripts)}")
    print("="*50)
    
    if not high_slob_scripts:
        print("Great news! No scripts meet the 'High Slob' threshold (> 500 per function).")
    else:
        for i, fname in enumerate(high_slob_scripts, 1):
            stats = file_stats[fname]
            print(f"{i:2}. {fname:<35} | Total Score: {stats['total_score']:>8.1f} | High-Slob Funcs: {stats['high_slob_count']}")

    # 2. "Need to Refactor" Section (Prioritize within a reasonable threshold)
    print("\n" + "="*50)
    print(f"🛠️  NEED TO REFACTOR (Priority List)")
    print(f"(Goal: Combined Score < {args.refactor_limit})")
    print("="*50)
    
    # Sort all files with any slob by total score descending
    priority_pool = sorted(file_stats.keys(), key=lambda f: file_stats[f]["total_score"], reverse=True)
    
    suggested_refactors = []
    cumulative_score = 0.0
    
    for fname in priority_pool:
        file_score = file_stats[fname]["total_score"]
        if cumulative_score + file_score <= args.refactor_limit:
            suggested_refactors.append(fname)
            cumulative_score += file_score
        elif not suggested_refactors:
            # If even the first one is over the limit, show it anyway but stop
            suggested_refactors.append(fname)
            cumulative_score += file_score
            break
        else:
            break
            
    if not suggested_refactors:
        print("No items suggested for the current refactor limit.")
    else:
        for fname in suggested_refactors:
            stats = file_stats[fname]
            # Find the worst function in this file for extra context
            worst_func = max(stats["functions"], key=lambda f: f["metrics"]["total_score"])
            print(f"👉 {fname}")
            print(f"   - File Total Score: {stats['total_score']:.1f}")
            print(f"   - Worst Offender: {worst_func['function']} (Score: {worst_func['metrics']['total_score']:.1f})")
            print("-" * 30)
            
        print(f"\n✅ Total Refactor Target Score: {cumulative_score:.1f} / {args.refactor_limit}")
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
