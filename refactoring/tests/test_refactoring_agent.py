import subprocess
import sys
import os
import shutil
import argparse

def test_refactoring_agent(target_dir=None):
    # Determine the 'refactoring' directory (parent of 'tests')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    refactoring_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    is_custom = target_dir is not None
    
    # Always use .temp as the workspace to avoid modifying originals
    temp_path = os.path.join(script_dir, ".temp")
    
    # Clean up previous run to ensure a fresh start
    if os.path.exists(temp_path):
        try:
            if os.path.isdir(temp_path):
                shutil.rmtree(temp_path)
            else:
                os.remove(temp_path)
        except Exception as e:
            print(f"Warning: Could not clean up existing {temp_path}: {e}")

    if is_custom:
        source_path = os.path.abspath(target_dir)
        print(f"Copying custom target from {source_path} to {temp_path}...")
    else:
        source_path = os.path.join(refactoring_dir, "tests", "fixtures")
        print(f"Copying fixtures from {source_path} to {temp_path}...")
        
    shutil.copytree(source_path, temp_path, dirs_exist_ok=True)

    # Prompt as requested
    try:
        rel_target = os.path.relpath(temp_path, refactoring_dir)
    except ValueError:
        rel_target = temp_path
        
    prompt = f"Refactor the code in {rel_target}"
    
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        print("\n[ERROR] 'gemini' command not found in PATH.")
        sys.exit(1)

    # Construct the gemini command
    command = [
        gemini_path,
        "-p", prompt,
        "--model", "gemini-3-flash-preview",
        "--output-format", "stream-json",
        "--yolo"
    ]
    
    print(f"Running: {' '.join(command)}")
    print(f"Target Directory (Prompt): {rel_target}")
    print(f"Working Directory: {refactoring_dir}")
    print("-" * 40)
    
    output_lines = []
    
    try:
        # Run the subprocess, capture output, and stream it
        process = subprocess.Popen(
            command,
            cwd=refactoring_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1, # Line buffered
            encoding='utf-8',
            errors='replace'
        )
        
        with process.stdout:
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line)
                sys.stdout.flush()
                output_lines.append(line)
        
        process.wait()
        
        full_output = "".join(output_lines)
        
        if process.returncode != 0:
            print(f"\n[FAIL] Gemini exited with code {process.returncode}")
        else:
            print("\n[SUCCESS] Gemini execution completed.")

            # --- Orchestrator Execution ---
            orchestrator_path = os.path.abspath(os.path.join(refactoring_dir, "..", "verification", "src", "orchestrator.py"))
            
            # The target directory for the orchestrator is simply the temp path
            # (which is either the copied fixtures or the custom target dir)
            orchestrator_target = temp_path
            
            print(f"\nRunning Orchestrator on {orchestrator_target}...")
            orch_cmd = ["uv", "run", orchestrator_path, orchestrator_target]
            
            try:
                orch_result = subprocess.run(
                    orch_cmd,
                    cwd=refactoring_dir, # Run from refactoring dir, though uv run handles paths
                    capture_output=True,
                    text=True
                )
                print("--- Orchestrator Output ---")
                print(orch_result.stdout)
                if orch_result.stderr:
                    print("--- Orchestrator Stderr ---")
                    print(orch_result.stderr)
                print("---------------------------")

                # --- Output Parsing & Assertion ---
                jobs = {}
                current_job = None
                
                # Simple parsing logic assuming standard Orchestrator output format
                for line in orch_result.stdout.splitlines():
                    clean_line = line.strip()
                    if line.startswith("[PASS] ") or line.startswith("[FAIL] ") or line.startswith("[SKIP] "):
                        # This is a job line (no indentation)
                        parts = line.split(" ", 1)
                        status = parts[0].strip("[]")
                        name = parts[1].strip()
                        current_job = name
                        jobs[current_job] = {"status": status, "functions": []}
                    elif clean_line.startswith("[PASS] ") or clean_line.startswith("[FAIL] ") or clean_line.startswith("[SKIP] "):
                        # This is a function line (indented)
                        if current_job:
                            parts = clean_line.split(" ", 1)
                            f_status = parts[0].strip("[]")
                            # Remove potential extra info like (0.12s) or Speedup: ...
                            f_name_raw = parts[1]
                            # Extract just the function name (stop at first parenthesis or extra info)
                            f_name = f_name_raw.split("(")[0].strip()
                            jobs[current_job]["functions"].append({"status": f_status, "name": f_name})

                failed_assertions = False
                
                for job_name, data in jobs.items():
                    # All jobs must be either PASS or SKIP
                    if data["status"] == "FAIL":
                         print(f"[ASSERT FAIL] Job '{job_name}' failed.")
                         failed_assertions = True

                    for func in data["functions"]:
                        # All functions must be either PASS or SKIP
                        if func["status"] == "FAIL":
                            print(f"[ASSERT FAIL] Function '{func['name']}' in job '{job_name}' failed.")
                            failed_assertions = True

                if failed_assertions:
                    print("\n[TEST FAILED] Some assertions failed (detected [FAIL] status).")
                    sys.exit(1)
                elif orch_result.returncode != 0:
                     # Fallback if return code is bad but we somehow missed it in assertions
                    print("\n[TEST FAILED] Orchestrator reported failures (exit code).")
                    sys.exit(1)
                else:
                    print("\n[TEST PASSED] All jobs and functions passed or were skipped.")

            except Exception as e:
                print(f"Failed to run orchestrator: {e}")
                sys.exit(1)
            # ------------------------------

        if process.returncode != 0:
            sys.exit(process.returncode)
            
    except FileNotFoundError:
        print("\n[ERROR] 'gemini' command not found. Ensure it is in your PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        process.terminate()
        sys.exit(130)
    finally:
        if os.path.exists(temp_path):
            print(f"Cleaning up {temp_path}...")
            try:
                if os.path.isdir(temp_path):
                    shutil.rmtree(temp_path)
                else:
                    os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Failed to clean up {temp_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Refactoring Agent")
    parser.add_argument("target_dir", help="Directory to refactor")
    args = parser.parse_args()
    
    test_refactoring_agent(args.target_dir)
