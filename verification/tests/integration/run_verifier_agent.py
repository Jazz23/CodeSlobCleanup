import argparse
import subprocess
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Run Gemini Verifier Skill on a target directory.")
    parser.add_argument("input_dir", help="Path to the directory containing code to verify.")
    args = parser.parse_args()

    # Use the input directory path exactly as provided by the user
    input_path = args.input_dir
    prompt = f"Verify the code in {input_path}"
    
    import shutil
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
    
    # Determine the 'verification' directory (2 levels up from this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    verification_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))

    print(f"Running: {' '.join(command)}")
    print(f"Target Directory: {input_path}")
    print(f"Working Directory: {verification_dir}")
    print("-" * 40)
    
    try:
        # Run the subprocess and stream output directly to the console
        process = subprocess.Popen(
            command,
            cwd=verification_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        process.wait()
        
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
    main()

