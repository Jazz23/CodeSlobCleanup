# /// script
# dependencies = [
#     "coverage",
# ]
# ///

import sys
import subprocess
import json
import os
from pathlib import Path
import argparse
import ast

def run_coverage(test_script_path):
    test_script_path = Path(test_script_path).resolve()
    if not test_script_path.exists():
        print(f"Error: Test script {test_script_path} not found.")
        sys.exit(1)

    work_dir = test_script_path.parent
    script_name = test_script_path.name

    # Run coverage
    print(f"Running coverage for {script_name} in {work_dir}...")
    
    try:
        subprocess.run(
            ["coverage", "run", script_name],
            cwd=work_dir,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Test execution failed:\n{e.stderr}")

    # Generate JSON report
    subprocess.run(
        ["coverage", "json", "-o", "coverage.json"],
        cwd=work_dir,
        check=True,
        capture_output=True
    )

    with open(work_dir / "coverage.json", "r") as f:
        data = json.load(f)

    # Clean up
    (work_dir / "coverage.json").unlink()
    (work_dir / ".coverage").unlink()

    return data

def get_function_ranges(file_path):
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # end_lineno is available in Python 3.8+
            functions.append({
                "name": node.name,
                "start": node.lineno,
                "end": node.end_lineno
            })
    return functions

def remove_untested_functions(file_path, coverage_info):
    if not os.path.exists(file_path):
        return
        
    executed_lines = set(coverage_info.get("executed_lines", []))
    functions = get_function_ranges(file_path)
    
    to_remove = []
    for func in functions:
        # A function is considered untested if NONE of its body lines are executed.
        # The 'def' line (func["start"]) is often marked as executed upon import.
        # We check lines from func["start"] + 1 to func["end"].
        if func["start"] == func["end"]:
            # Single line function like 'def f(): pass' - if this line is "executed",
            # it might just be the definition. This is a bit ambiguous but 
            # usually body starts after the def.
            body_lines = set() # Fallback
        else:
            body_lines = set(range(func["start"] + 1, func["end"] + 1))
            
        if body_lines and not (body_lines & executed_lines):
            to_remove.append(func)
            
    if not to_remove:
        return

    print(f"Removing {len(to_remove)} untested functions from {file_path}: {[f['name'] for f in to_remove]}")
    
    with open(file_path, "r") as f:
        lines = f.readlines()
        
    # Sort in reverse to avoid index shifting
    for func in sorted(to_remove, key=lambda x: x["start"], reverse=True):
        start_idx = func["start"] - 1
        end_idx = func["end"]
        
        # Also remove trailing blank lines
        while end_idx < len(lines) and not lines[end_idx].strip():
            end_idx += 1
            
        del lines[start_idx : end_idx]
        
    with open(file_path, "w") as f:
        f.writelines(lines)

def main():
    parser = argparse.ArgumentParser(description="Remove untested functions based on a golden test script.")
    parser.add_argument("test_script", help="Path to the golden python testing script.")
    args = parser.parse_args()

    test_script_path = Path(args.test_script).resolve()
    work_dir = test_script_path.parent
    coverage_data = run_coverage(args.test_script)
    files = coverage_data.get("files", {})
    
    for file_path, info in files.items():
        # Resolve path relative to work_dir if it's relative
        abs_file_path = Path(file_path)
        if not abs_file_path.is_absolute():
            abs_file_path = work_dir / file_path
            
        # Only process files that are not the test script itself.
        if str(abs_file_path) == str(test_script_path):
            continue
            
        remove_untested_functions(str(abs_file_path), info)

if __name__ == "__main__":
    main()