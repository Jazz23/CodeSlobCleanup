# /// script
# dependencies = [
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import argparse
import os
import sys
import subprocess
import json
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(cmd, cwd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def parse_verify_output(output):
    """Parses the cleaned verify.py output."""
    results = {}
    lines = output.splitlines()
    current_fail = None
    
    for line in lines:
        if line.startswith("[PASS] "):
            name = line[7:].strip()
            results[name] = {"name": name, "status": "PASS", "logs": ""}
        elif line.startswith("[FAIL] "):
            name = line[7:].strip()
            current_fail = {"name": name, "status": "FAIL", "logs": []}
            results[name] = current_fail
        elif current_fail:
            current_fail["logs"].append(line)
            
    for name, res in results.items():
        if isinstance(res["logs"], list):
            res["logs"] = "\n".join(res["logs"])
            
    return results

def parse_benchmark_output(output):
    """Parses the structured benchmark.py output."""
    speedups = {}
    for line in output.splitlines():
        if line.startswith("[SPEEDUP] "):
            try:
                parts = line[10:].split(": ")
                name = parts[0].strip()
                val = parts[1].strip()
                speedups[name] = val
            except:
                continue
    return speedups

def process_job(job_dir, verification_root, scripts_dir, config_str="{}"):
    """Processes a single job directory."""
    orig_file = job_dir / "original.py"
    ref_file = job_dir / "refactored.py"
    
    if not (orig_file.exists() and ref_file.exists()):
        return None

    # 1. Verification
    verify_cmd = ["uv", "run", str(scripts_dir / "verify.py"), str(orig_file), str(ref_file), "--config", config_str]
    ret, out, err = run_command(verify_cmd, verification_root)
    
    # 2. Benchmark
    bench_cmd = ["uv", "run", str(scripts_dir / "benchmark.py"), str(orig_file), str(ref_file), "--config", config_str]
    ret_b, out_b, err_b = run_command(bench_cmd, verification_root)
    
    functions = parse_verify_output(out + err)
    speedups = parse_benchmark_output(out_b + err_b)
    
    for name, speedup in speedups.items():
        if name in functions:
            functions[name]["speedup"] = speedup
    
    status = "PASS" if ret == 0 else "FAIL"
    
    return {
        "job_name": job_dir.name,
        "status": status,
        "functions": list(functions.values())
    }

def main():
    parser = argparse.ArgumentParser(description="Verifier Skill Orchestrator")
    parser.add_argument("--target-dir", required=True, help="Directory containing job subfolders")
    parser.add_argument("--config", required=True, help="JSON config string")
    args = parser.parse_args()
    
    input_dir = Path(args.target_dir).resolve()
    if not input_dir.exists(): sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent
    verification_root = scripts_dir.parent.parent.parent.parent

    jobs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_job, job, verification_root, scripts_dir, args.config): job for job in jobs}
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)
    
    # Calculate Statistics
    all_speedups = []
    for res in results:
        for func in res['functions']:
            if 'speedup' in func and func['speedup'] != "N/A":
                try:
                    val = float(func['speedup'].rstrip('x'))
                    all_speedups.append(val)
                except:
                    pass
    
    if all_speedups:
        avg_s = sum(all_speedups) / len(all_speedups)
        best_s = max(all_speedups)
        worst_s = min(all_speedups)
        print("--- Global Performance Summary ---")
        print(f"Average Speedup: {avg_s:.2f}x")
        print(f"Best Speedup:    {best_s:.2f}x")
        print(f"Worst Speedup:   {worst_s:.2f}x")
        print("----------------------------------\n")
    
    any_failed = False
    for res in sorted(results, key=lambda x: x['job_name']):
        status_icon = "[PASS]" if res['status'] == "PASS" else "[FAIL]"
            
        print(f"{status_icon} {res['job_name']}")
        
        for func in res['functions']:
            perf = f" (Speedup: {func['speedup']})" if "speedup" in func else ""
            if func['status'] == "FAIL":
                any_failed = True
                print(f"  [FAIL] {func['name']}{perf}")
                print(f"    ERROR Details:")
                for line in func['logs'].splitlines():
                    print(f"      {line}")
            else:
                print(f"  [PASS] {func['name']}{perf}")
                
    if any_failed:
        sys.exit(1)

if __name__ == '__main__':
    main()
