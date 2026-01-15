# /// script
# dependencies = [
#     "pytest",
# ]
# ///

import os
import shutil
import pytest
from pathlib import Path
import subprocess
import sys

# Paths
TESTS_DIR = Path(__file__).resolve().parent.parent
VERIFICATION_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = VERIFICATION_ROOT / ".gemini" / "skills" / "verifier" / "scripts"
CORRECT_REFACTOR_PATH = SCRIPTS_DIR / "correct_refactor.py"

def test_correct_refactor_script(tmp_path):
    """
    Tests that correct_refactor.py can take failure logs and update a file.
    We mock the 'LLM' by having a script that just returns a fixed string
    if we were to actually call an API, but here we'll just test the 
    script's logic for processing inputs and writing outputs.
    """
    # 1. Setup
    job_dir = tmp_path / "math_job"
    job_dir.mkdir()
    
    orig_code = "def add(a, b): return a + b"
    ref_code = "def add(a, b): return a - b" # Buggy
    
    (job_dir / "original.py").write_text(orig_code)
    (job_dir / "refactored.py").write_text(ref_code)
    
    failure_logs = "AssertionError: Mismatch for input (1, 1): Original=2, Refactored=0"
    
    # We'll run the script with a special MOCK flag or just verify it creates a prompt.
    # For this test, let's assume correct_refactor.py takes:
    # --job-dir, --logs, --speedup
    
    # Since we haven't built it yet, this test will fail initially (TDD).
    
    cmd = [
        sys.executable, str(CORRECT_REFACTOR_PATH),
        "--job-dir", str(job_dir),
        "--logs", failure_logs,
        "--mock-response", "def add(a, b):\n    return a + b" # Simulating LLM fix
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    
    # Verify refactored.py was updated
    updated_ref = (job_dir / "refactored.py").read_text().strip()
    assert "return a + b" in updated_ref
    assert "return a - b" not in updated_ref
