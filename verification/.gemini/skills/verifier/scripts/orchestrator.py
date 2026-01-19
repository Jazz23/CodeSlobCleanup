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

try:
    # Import common to configure sys.pycache_prefix
    import common
except ImportError:
    pass

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
        status = None
        raw = ""
        
        if line.startswith("[PASS] "):
            status = "PASS"
            raw = line[7:].strip()
        elif line.startswith("[SKIP] "):
            status = "SKIP"
            raw = line[7:].strip()
        elif line.startswith("[FAIL] "):
            status = "FAIL"
            raw = line[7:].strip()
        elif current_fail:
            current_fail["logs"].append(line)
            continue
            
        if status:
            # Extract duration using regex
            duration = None
            # Match (1.2345s) or (0.0000s)
            match = re.search(r"\(([\d\.]+)s\)", raw)
            name = raw
            
            if match:
                duration = match.group(1) + "s"
                # Remove duration from name, keeping clean spacing
                name = raw.replace(match.group(0), "").strip()
                # Normalize spaces (replace double spaces with single)
                name = re.sub(r'\s+', ' ', name)
            
            # If name is empty (unlikely), revert to raw
            if not name:
                name = raw

            res = {"name": name, "status": status, "logs": "" if status != "FAIL" else [], "duration": duration}
            results[name] = res
            
            if status == "FAIL":
                current_fail = res
            else:
                current_fail = None
            
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
        elif line.startswith("[SKIP] "):
             # Benchmarking also skips
             continue
    return speedups

def process_job(job_dir, verification_root, scripts_dir, config_str="{}"):
    """Processes a single job directory."""
    orig_file = job_dir / "original.py"
    ref_file = job_dir / "refactored.py"
    
    if not (orig_file.exists() and ref_file.exists()):
        return None

    # 1. Verification & 2. Benchmark (Parallel)
    verify_cmd = ["uv", "run", str(scripts_dir / "verify.py"), str(orig_file), str(ref_file), "--config", config_str]
    bench_cmd = ["uv", "run", str(scripts_dir / "benchmark.py"), str(orig_file), str(ref_file), "--config", config_str]

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_verify = executor.submit(run_command, verify_cmd, verification_root)
        future_bench = executor.submit(run_command, bench_cmd, verification_root)
        
        ret, out, err = future_verify.result()
        ret_b, out_b, err_b = future_bench.result()
    
    functions = parse_verify_output(out + err)
    speedups = parse_benchmark_output(out_b + err_b)
    
    for name, speedup in speedups.items():
        if name in functions:
            functions[name]["speedup"] = speedup
    
    # Job status is FAIL if any function failed (AssertionError)
    # If a function SKIPPED, the job can still PASS (but those functions won't show as PASS)
    status = "PASS" if ret == 0 else "FAIL"
    
    return {
        "job_name": job_dir.name,
        "status": status,
        "functions": list(functions.values())
    }

def main():
    parser = argparse.ArgumentParser(description="Verifier Skill Orchestrator")
    parser.add_argument("--target-dir", required=True, help="Directory containing job subfolders")
    parser.add_argument("--config", default="{}", help="JSON config string (default: '{}')")
    args = parser.parse_args()

    # Validate JSON config immediately
    try:
        json.loads(args.config)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON configuration provided: {e}")
        sys.exit(1)
    
    input_dir = Path(args.target_dir).resolve()
    if not input_dir.exists(): sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent
    verification_root = scripts_dir.parent.parent.parent.parent

    jobs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    results = []
    # Since child processes (verify.py/benchmark.py) now run in parallel internally,
    # we reduce the job-level parallelism to avoid oversubscribing the system.
    max_workers = max(1, (os.cpu_count() or 4) // 2)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
            extras = []
            if "duration" in func and func['duration']:
                extras.append(f"{func['duration']}")
            if "speedup" in func:
                extras.append(f"Speedup: {func['speedup']}")
            
            extra_str = f" ({', '.join(extras)})" if extras else ""
            
            if func['status'] == "FAIL":
                any_failed = True
                print(f"  [FAIL] {func['name']}{extra_str}")
                print(f"    ERROR Details:")
                for line in func['logs'].splitlines():
                    print(f"      {line}")
            elif func['status'] == "SKIP":
                print(f"  [SKIP] {func['name']}{extra_str}")
            else:
                print(f"  [PASS] {func['name']}{extra_str}")
                
    if any_failed:
        sys.exit(1)

if __name__ == '__main__':
    main()
