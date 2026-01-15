import argparse
import os
import sys
import subprocess
import json
import time
import shutil
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(cmd, cwd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def process_job(job_dir, verification_root, scripts_dir, debug=False, config_str="{}"):
    """Processes a single job directory."""
    orig_file = job_dir / "original.py"
    ref_file = job_dir / "refactored.py"
    
    if not (orig_file.exists() and ref_file.exists()):
        return None

    start_time = time.time()
    report = {
        "job_name": job_dir.name,
        "verification": {"status": "pending", "output": ""},
        "benchmark": {"status": "pending", "output": ""}
    }
    
    # 1. Verification
    verify_cmd = [
        "uv", "run", "python", str(scripts_dir / "verify.py"), 
        str(orig_file), str(ref_file),
        "--config", config_str
    ]
    ret, out, err = run_command(verify_cmd, verification_root)
    report["verification"]["status"] = "PASS" if ret == 0 else "FAIL"
    report["verification"]["output"] = out + err
    
    # 2. Benchmark
    bench_cmd = [
        "uv", "run", "python", str(scripts_dir / "benchmark.py"), 
        str(orig_file), str(ref_file),
        "--config", config_str
    ]
    ret_b, out_b, err_b = run_command(bench_cmd, verification_root)
    report["benchmark"]["status"] = "PASS" if ret_b == 0 else "FAIL"
    report["benchmark"]["output"] = out_b + err_b
    
    # Results are stored in the report dict for formatting
    duration = time.time() - start_time
    
    # Format Output
    status_icon = "[PASS]" if report['verification']['status'] == 'PASS' else "[FAIL]"
    
    if debug:
        report_json = json.dumps(report, indent=2)
        return f"  [{job_dir.name}] Result: {report['verification']['status']} | Duration: {duration:.2f}s\n  Report:\n{report_json}"
    else:
        # Extract speedup info if available
        bench_summary = ""
        if "Speedup:" in report["benchmark"]["output"]:
            for line in report["benchmark"]["output"].splitlines():
                if "Speedup:" in line:
                    bench_summary += f" | {line.strip()}"
        
        return f"{status_icon} {job_dir.name}: Verification {report['verification']['status']}{bench_summary}"

def main():
    parser = argparse.ArgumentParser(description="Verifier Skill Orchestrator")
    parser.add_argument("--target-dir", required=True, help="Directory containing job subfolders")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument("--debug", action="store_true", help="Enable verbose output")
    parser.add_argument("--config", required=True, help="JSON config string for type inference")
    args = parser.parse_args()
    
    input_dir = Path(args.target_dir).resolve()
    if not input_dir.exists():
        print(f"Error: Target directory {input_dir} does not exist.")
        return

    # Setup Sandbox
    temp_root = Path(tempfile.gettempdir())
    sandbox_dir = temp_root / "code_slob_verifier_run"
    
    if args.debug:
        print(f"Initializing sandbox at {sandbox_dir}...")
    
    if sandbox_dir.exists():
        # Retry loop for Windows file locking issues
        for i in range(3):
            try:
                shutil.rmtree(sandbox_dir)
                break
            except Exception as e:
                if i == 2:
                    print(f"Error cleaning sandbox: {e}")
                    sys.exit(1)
                time.sleep(0.5)
            
    # Copy input to sandbox
    try:
        shutil.copytree(input_dir, sandbox_dir)
    except Exception as e:
        print(f"Error copying to sandbox: {e}")
        sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent
    # .gemini/skills/verifier/scripts -> .gemini/skills/verifier -> .gemini/skills -> .gemini -> verification
    verification_root = scripts_dir.parent.parent.parent.parent

    if args.debug:
        print(f"Scanning sandbox {sandbox_dir} for jobs...")
    
    jobs = [d for d in sandbox_dir.iterdir() if d.is_dir()]
    
    print(f"Processing {len(jobs)} jobs with {args.workers} workers...")
    
    start_total = time.time()
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_job = {executor.submit(process_job, job, verification_root, scripts_dir, args.debug, args.config): job for job in jobs}
        for future in as_completed(future_to_job):
            res = future.result()
            if res:
                results.append(res)
    
    any_failed = False
    for res in sorted(results):
        print(res)
        if "Verification FAIL" in res:
            any_failed = True
                
    total_duration = time.time() - start_total
    print(f"\nTotal execution time: {total_duration:.2f}s")
    if args.debug:
        print(f"Results available in: {sandbox_dir}")
        
    if any_failed:
        sys.exit(1)

if __name__ == '__main__':
    main()