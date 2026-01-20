# /// script
# dependencies = [
#     "pytest",
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import os
import json
import subprocess
import sys
from pathlib import Path
import pytest

def test_orchestrator_flow(tmp_path):
    # Setup mock job
    job_dir = tmp_path / "test_job"
    job_dir.mkdir()
    (job_dir / "original.py").write_text("def add(a, b): return a + b")
    (job_dir / "refactored.py").write_text("def add(a, b): return a + b")
    
    # Path to orchestrator
    verification_root = Path(__file__).resolve().parent.parent.parent
    orchestrator_path = verification_root / "src" / "orchestrator.py"
    
    # Run orchestrator
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "1"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "5"
    
    cmd = [
        sys.executable, str(orchestrator_path),
        "--target-dir", str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    assert result.returncode == 0
    # Check stdout for success message and function name
    assert "[PASS] test_job" in result.stdout
    assert "[PASS] add" in result.stdout
    assert "Speedup:" in result.stdout
    
    # Check for Global Summary
    assert "Global Performance Summary" in result.stdout
    assert "Average Speedup:" in result.stdout
    assert "Best Speedup:" in result.stdout
    assert "Worst Speedup:" in result.stdout

def test_orchestrator_fail_flow(tmp_path):
    # Setup mock failing job
    job_dir = tmp_path / "fail_job"
    job_dir.mkdir()
    (job_dir / "original.py").write_text("def sub(a, b): return a - b")
    (job_dir / "refactored.py").write_text("def sub(a, b): return a + b") # Wrong!
    
    # Path to orchestrator
    verification_root = Path(__file__).resolve().parent.parent.parent
    orchestrator_path = verification_root / "src" / "orchestrator.py"
    
    cmd = [
        sys.executable, str(orchestrator_path),
        "--target-dir", str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 1
    assert "[FAIL] fail_job" in result.stdout
    assert "[FAIL] sub" in result.stdout
    assert "ERROR Details:" in result.stdout