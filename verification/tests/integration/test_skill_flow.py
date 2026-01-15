# /// script
# dependencies = [
#     "pytest",
# ]
# ///

import shutil
import subprocess
from pathlib import Path
import json
import pytest
import os
import tempfile
import sys

# Define paths
TESTS_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
VERIFICATION_ROOT = TESTS_DIR.parent
ORCHESTRATOR_PATH = VERIFICATION_ROOT / ".gemini" / "skills" / "verifier" / "scripts" / "orchestrator.py"

def get_sandbox_dir():
    return Path(tempfile.gettempdir()) / "code_slob_verifier_run"

@pytest.mark.parametrize("scenario", ["scenario_valid", "scenario_untyped_complex"])
def test_skill_success_cases(tmp_path, scenario):
    """Tests that valid refactorings pass verification."""
    # 1. Setup: Copy fixtures to a temp job directory
    source = FIXTURES_DIR / scenario
    for job in source.iterdir():
        if not job.is_dir(): continue
        shutil.copytree(job, tmp_path / job.name)
        
    # 2. Action: Run orchestrator
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "2"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "40"
    
    # NEW: Detect and merge configs from fixtures to pass via --config
    merged_config = {}
    for job_dir in source.iterdir():
        if not job_dir.is_dir(): continue
        config_file = job_dir / "verification_config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                merged_config.update(json.load(f))
    
    config_json = json.dumps(merged_config)
    
    # Use sys.executable to run in current environment (which has deps)
    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        "--target-dir", str(tmp_path),
        "--debug",
        "--config", config_json
    ]
    # Run from verification root so tools are found
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    # 3. Assertions
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    assert result.returncode == 0
    
    # Check stdout for [PASS] for all jobs in the scenario
    for job in tmp_path.iterdir():
        if not job.is_dir(): continue
        # Format in debug mode: "  [job_name] Result: PASS"
        assert f"[{job.name}] Result: PASS" in result.stdout

def test_skill_catches_regression(tmp_path):
    """Tests that broken refactorings are caught."""
    # 1. Setup
    source = FIXTURES_DIR / "scenario_broken"
    for job in source.iterdir():
        if not job.is_dir(): continue
        shutil.copytree(job, tmp_path / job.name)
        
    # 2. Action
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "2"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "40"
    
    # Detect and merge configs (though broken math usually doesn't have one)
    merged_config = {}
    for job_dir in source.iterdir():
        if not job_dir.is_dir(): continue
        config_file = job_dir / "verification_config.json"
        if config_file.exists():
            with open(config_file, "r") as f:
                merged_config.update(json.load(f))
    
    config_json = json.dumps(merged_config)
    
    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        "--target-dir", str(tmp_path),
        "--debug",
        "--config", config_json
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    # 3. Assertions
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    
    # Check stdout for FAIL
    for job in tmp_path.iterdir():
        if not job.is_dir(): continue
        # Format in debug mode: "  [job_name] Result: FAIL"
        assert f"[{job.name}] Result: FAIL" in result.stdout
