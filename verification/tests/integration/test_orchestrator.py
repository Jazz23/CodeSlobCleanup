# /// script
# dependencies = [
#     "pytest",
# ]
# ///

import os
import json
import subprocess
import tempfile
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
    orchestrator_path = verification_root / ".gemini" / "skills" / "verifier" / "scripts" / "orchestrator.py"
    
    # Run orchestrator
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "1"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "5"
    
    cmd = [
        "uv", "run", "python", str(orchestrator_path),
        "--target-dir", str(tmp_path),
        "--config", "{}"
    ]
    # We run from root so 'uv' works with verification/pyproject.toml if needed, 
    # but orchestrator expects to be able to find tools relative to verification root.
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    assert result.returncode == 0
    
    # Check stdout for success message instead of file
    assert "[PASS] test_job: Verification PASS" in result.stdout

def test_orchestrator_debug_flag(tmp_path):
    # Setup mock job
    job_dir = tmp_path / "debug_job"
    job_dir.mkdir()
    (job_dir / "original.py").write_text("def sub(a, b): return a - b")
    (job_dir / "refactored.py").write_text("def sub(a, b): return a - b")
    
    # Path to orchestrator
    verification_root = Path(__file__).resolve().parent.parent.parent
    orchestrator_path = verification_root / ".gemini" / "skills" / "verifier" / "scripts" / "orchestrator.py"
    
    cmd = [
        sys.executable, str(orchestrator_path),
        "--target-dir", str(tmp_path),
        "--debug",
        "--config", "{}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Check for debug markers in stdout
    assert "Initializing sandbox" in result.stdout
    assert "Report:" in result.stdout
    assert "verification" in result.stdout
    assert "benchmark" in result.stdout