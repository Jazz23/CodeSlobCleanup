# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
import sys
import shutil
import os
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run E2E tests for code-slob-cleanup.")
    parser.add_argument("folder_path", type=Path, help="Path to the source folder to test.")
    parser.add_argument("--no-cleanup", action="store_true", help="Do not delete the .temp folder after completion.")
    args = parser.parse_args()

    source_folder = args.folder_path
    if not source_folder.exists():
        print(f"Error: Source folder '{source_folder}' does not exist.")
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    temp_dir = project_root / ".temp"

    # Clean up previous run if exists
    if temp_dir.exists():
        print(f"Cleaning up existing {temp_dir}...")
        shutil.rmtree(temp_dir)

    # 1. Copy source folder to .temp
    print(f"Copying {source_folder} to {temp_dir}...")
    shutil.copytree(source_folder, temp_dir)

    # 2. Copy skills/code-slob-cleanup to .temp/.gemini/skills/code-slob-cleanup
    skill_source = project_root / "skills" / "code-slob-cleanup"
    skill_dest = temp_dir / ".gemini" / "skills" / "code-slob-cleanup"

    if not skill_source.exists():
        print(f"Error: Skill source '{skill_source}' does not exist.")
        sys.exit(1)

    print(f"Copying {skill_source} to {skill_dest}...")
    # Create parent directories
    skill_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_source, skill_dest)

    # 3. Run gemini refactoring
    print("Running gemini refactoring...")
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        print("Error: 'gemini' executable not found in PATH.")
        sys.exit(1)

    # We need to run gemini inside the .temp directory
    # The prompt instructs it to refactor the current directory (".")
    command = [
        gemini_path,
        "-p", "Refactor the code in .",
        "--model", "gemini-3-flash-preview",
        "--output-format", "stream-json",
        "--yolo"
    ]

    try:
        result = subprocess.run(
            command,
            cwd=temp_dir,
            check=False,  # We'll check returncode manually
            capture_output=False # Let it stream to stdout/stderr
        )
        if result.returncode == 0:
            print("Gemini refactoring completed successfully.")
        else:
            print(f"Gemini refactoring failed with exit code {result.returncode}.")
            sys.exit(result.returncode)
    except Exception as e:
        print(f"Failed to run gemini: {e}")
        sys.exit(1)

    # 4. Verify output
    print("Verifying output...")
    expected_output_path = source_folder / "expected_output.txt"
    if not expected_output_path.exists():
        print(f"Warning: {expected_output_path} not found. Skipping verification.")
    else:
        try:
            expected_content = expected_output_path.read_text().strip()
            
            # Run the refactored main.py
            verify_result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            actual_content = verify_result.stdout.strip()
            
            if actual_content == expected_content:
                print("Verification Passed: Output matches expected_output.txt")
            else:
                print("Verification Failed: Output does not match expected_output.txt")
                print("--- Expected ---")
                print(expected_content)
                print("--- Actual ---")
                print(actual_content)
                sys.exit(1)
                
        except subprocess.CalledProcessError as e:
             print(f"Verification Failed: Refactored code crashed.")
             print("--- Stderr ---")
             print(e.stderr)
             sys.exit(1)
        except Exception as e:
            print(f"Verification Failed: {e}")
            sys.exit(1)

    print("Setup complete.")

    if not args.no_cleanup:
        print(f"Cleaning up {temp_dir}...")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
