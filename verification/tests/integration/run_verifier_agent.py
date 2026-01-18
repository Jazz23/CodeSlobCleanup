import argparse
import subprocess
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Run Gemini Verifier Skill on a target directory.")
    parser.add_argument("input_dir", help="Path to the directory containing code to verify.")
    args = parser.parse_args()

    # Resolve absolute path for the input directory
    input_path = os.path.abspath(args.input_dir)
    prompt = f"Verify the code in {input_path}"
    
    # Construct the gemini command
    command = [
        "gemini",
        "-p", prompt,
        "--model", "gemini-3-flash-preview",
        "--output-format", "stream-json",
        "--yolo"
    ]
    
    print(f"Running: {' '.join(command)}")
    print(f"Target Directory: {input_path}")
    print("-" * 40)
    
    try:
        # Run the subprocess and stream output directly to the console
        process = subprocess.Popen(
            command,
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

