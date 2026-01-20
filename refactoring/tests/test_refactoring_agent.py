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
            sys.exit(process.returncode)
        else:
            print("\n[SUCCESS] Gemini execution completed.")
            
    except FileNotFoundError:
        print("\n[ERROR] 'gemini' command not found. Ensure it is in your PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrupted by user.")
        process.terminate()
        sys.exit(130)

if __name__ == "__main__":
    test_refactoring_agent()
