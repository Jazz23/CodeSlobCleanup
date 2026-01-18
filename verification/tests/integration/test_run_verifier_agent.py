import subprocess
import sys
import os
import shutil

def test_run_verifier_agent():
    # Determine the 'verification' directory (2 levels up from this script: verification/tests/integration)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    verification_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    # Hardcoded target path relative to verification root
    input_path = os.path.join("tests", "fixtures", "scenario_hybrid")

    prompt = f"Verify the code in {input_path}"
    
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
    print(f"Target Directory: {input_path}")
    print(f"Working Directory: {verification_dir}")
    print("-" * 40)
    
    output_lines = []
    
    try:
        # Run the subprocess, capture output, and stream it
        process = subprocess.Popen(
            command,
            cwd=verification_dir,
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
            sys.exit(process.returncode)
        else:
            print("\n[SUCCESS] Gemini execution completed.")

        # Assertions
        print("\nVerifying Output...")
        
        expected_patterns = [
            "[FAIL] fail_job",
            "[FAIL] mul",
            "[FAIL] negate",
            "[PASS] mixed_bag",
            "[PASS] mixed_bag",  # Checks for the function name as well
            "[PASS] homogeneous_bag",
            "[PASS] pass_job",
            "[PASS] add",
            "[PASS] sub",
            "[PASS] skip_job",
            "[SKIP] skip_me_types",
            "[SKIP] skip_me_timeout"
        ]
        
        missing_patterns = []
        for pattern in expected_patterns:
            if pattern not in full_output:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"[ERROR] Missing expected output patterns: {missing_patterns}")
            # Raise assertion error to fail the test if run via pytest, or exit 1 if run as script
            raise AssertionError(f"Missing expected output patterns: {missing_patterns}")
        
        print("[SUCCESS] All expected patterns found in output.")
            
    except FileNotFoundError:
        print("\n[ERROR] 'gemini' command not found. Ensure it is in your PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        process.terminate()
        sys.exit(130)

if __name__ == "__main__":
    test_run_verifier_agent()