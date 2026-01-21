import subprocess
import sys
import os
import shutil

def test_refactoring_agent():
    # Determine the 'refactoring' directory (parent of 'tests')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    refactoring_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Paths for fixtures and temp dir
    fixtures_path = os.path.join(refactoring_dir, "tests", "fixtures")
    temp_path = os.path.join(refactoring_dir, ".temp")
    
    # Clean up and recreate .temp
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    
    print(f"Copying fixtures from {fixtures_path} to {temp_path}...")
    shutil.copytree(fixtures_path, temp_path)

    # Prompt as requested
    prompt = "Refactor the code in the .temp"
    
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
    print(f"Target Directory (Prompt): .temp")
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
            orchestrator_target = os.path.join(temp_path, "scenario_hybrid")
            
            print(f"\nRunning Orchestrator on {orchestrator_target}...")
            orch_cmd = ["uv", "run", orchestrator_path, "--target-dir", orchestrator_target]
            
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
                
                for line in orch_result.stdout.splitlines():
                    if line.startswith("[PASS] ") or line.startswith("[FAIL] "):
                        # This is a job line
                        parts = line.split(" ", 1)
                        status = parts[0].strip("[]")
                        name = parts[1].strip()
                        current_job = name
                        jobs[current_job] = {"status": status, "functions": []}
                    elif line.strip().startswith("[PASS] ") or line.strip().startswith("[FAIL] ") or line.strip().startswith("[SKIP] "):
                        # This is a function line
                        if current_job:
                            parts = line.strip().split(" ", 1)
                            f_status = parts[0].strip("[]")
                            f_name = parts[1]
                            jobs[current_job]["functions"].append({"status": f_status, "name": f_name})

                failed_assertions = False
                for job_name, data in jobs.items():
                    if job_name.startswith("skip_"):
                        # For skip_ jobs, the job status should be PASS (no failures)
                        # and individual functions should be SKIP
                        if data["status"] == "FAIL":
                            print(f"[ASSERT FAIL] Job '{job_name}' failed but was expected to be skipped.")
                            failed_assertions = True
                        
                        for func in data["functions"]:
                            if func["status"] != "SKIP":
                                print(f"[ASSERT FAIL] Function '{func['name']}' in job '{job_name}' was '{func['status']}' but expected 'SKIP'.")
                                failed_assertions = True
                                
                    else:
                        # For normal jobs, status must be PASS
                        if data["status"] != "PASS":
                            print(f"[ASSERT FAIL] Job '{job_name}' failed.")
                            failed_assertions = True

                if failed_assertions:
                    print("\n[TEST FAILED] Some assertions failed.")
                    sys.exit(1)
                else:
                    print("\n[TEST PASSED] All job status assertions passed.")
                # ----------------------------------

            except Exception as e:
                print(f"Failed to run orchestrator: {e}")
                sys.exit(1)
            # ------------------------------

        if os.path.exists(temp_path):
            print(f"Cleaning up {temp_path}...")
            shutil.rmtree(temp_path)

        if process.returncode != 0:
            sys.exit(process.returncode)
            
    except FileNotFoundError:
        print("\n[ERROR] 'gemini' command not found. Ensure it is in your PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        process.terminate()
        sys.exit(130)

if __name__ == "__main__":
    test_refactoring_agent()
