# /// script
# dependencies = [
#     "pytest",
#     "pytest-xdist",
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import shutil
import subprocess
from pathlib import Path
import json
import pytest
import os
import sys

# Define paths
TESTS_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
VERIFICATION_ROOT = TESTS_DIR.parent
PROJECT_ROOT = VERIFICATION_ROOT.parent
ORCHESTRATOR_PATH = PROJECT_ROOT / "skills/code-slob-cleanup/scripts/orchestrator.py"

@pytest.mark.parametrize("scenario", ["scenario_valid", "scenario_untyped_complex", "scenario_private_methods"])
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
    env["HYPOTHESIS_MAX_EXAMPLES"] = "10"

    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    if result.returncode != 0:
        # If scenario_private_methods fails overall, it might be due to a specific failure 
        # that we expect (like public_api failing).
        if scenario == "scenario_private_methods":
            assert result.returncode == 1
        else:
            print("\n--- STDOUT ---\n", result.stdout)
            print("\n--- STDERR ---\n", result.stderr)
            assert result.returncode == 0
    else:
        assert result.returncode == 0
    
    # Check stdout for [PASS] for all jobs in the scenario
    for job in tmp_path.iterdir():
        if not job.is_dir(): continue
        if scenario == "scenario_private_methods":
             # We expect some to pass and some to fail in this specific scenario
             assert f"[PASS] {job.name}" in result.stdout or f"[FAIL] {job.name}" in result.stdout
        else:
            assert f"[PASS] {job.name}" in result.stdout
            assert "Speedup:" in result.stdout

def test_private_methods_auto_pass(tmp_path):
    """Specifically verifies that private methods are automatically passed."""
    # 1. Setup
    scenario = "scenario_private_methods"
    source = FIXTURES_DIR / scenario
    for job in source.iterdir():
        if not job.is_dir(): continue
        shutil.copytree(job, tmp_path / job.name)
        
    # 2. Action
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "1"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "5"
    
    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    # 3. Assertions
    # Private method in class should PASS automatically
    assert "[PASS] PrivateMethodClass._private_calc" in result.stdout
    assert "Private method automatically passed" in result.stdout
    # Top-level private function should PASS automatically
    assert "[PASS] _top_level_private" in result.stdout
    assert "Private function automatically passed" in result.stdout
    
    # Public components should still be verified
    assert "[FAIL] PrivateMethodClass.public_api" in result.stdout
    assert "[PASS] public_func" in result.stdout

    # Should exit with code 1 because of the FAILure in public_api
    assert result.returncode == 1

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
    env["HYPOTHESIS_MAX_EXAMPLES"] = "10"
    
    merged_config = {}
    source = FIXTURES_DIR / "scenario_broken"
    # for job_dir in source.iterdir():
    #     if not job_dir.is_dir(): continue
    #     config_file = job_dir / "verification_config.json"
    #     if config_file.exists():
    #         with open(config_file, "r") as f:
    #             merged_config.update(json.load(f))
    
    # config_json = json.dumps(merged_config)

    
    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    # 3. Assertions
    assert result.returncode == 1
    
    # Check stdout for FAIL
    for job in tmp_path.iterdir():
        if not job.is_dir(): continue
        assert f"[FAIL] {job.name}" in result.stdout
        # Verify clean failure report
        assert "[FAIL] custom_power" in result.stdout
        assert "ERROR Details:" in result.stdout
        assert "AssertionError" in result.stdout

def test_skill_hybrid_skips(tmp_path):
    """Tests that hybrid scenario correctly reports SKIP for difficult cases, FAIL for bugs, and PASS for valid ones (including via config)."""
    # 1. Setup
    scenario = "scenario_hybrid"
    source = FIXTURES_DIR / scenario
    for job in source.iterdir():
        if not job.is_dir(): continue
        shutil.copytree(job, tmp_path / job.name)
        
    # 2. Action: Run orchestrator WITH config (to test unknown_types_job support)
    env = os.environ.copy()
    env["BENCHMARK_RUNS"] = "1"
    env["HYPOTHESIS_MAX_EXAMPLES"] = "50"
    
    # Detect and merge configs from fixtures
    # merged_config = {}
    # for job_dir in source.iterdir():
    #     if not job_dir.is_dir(): continue
    #     config_file = job_dir / "verification_config.json"
    #     if config_file.exists():
    #         with open(config_file, "r") as f:
    #             merged_config.update(json.load(f))
    
    # config_json = json.dumps(merged_config)
    
    
    cmd = [
        sys.executable, str(ORCHESTRATOR_PATH),
        str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=VERIFICATION_ROOT, env=env)
    
    print("\n--- STDOUT ---\n", result.stdout)
    print("\n--- STDERR ---\n", result.stderr)

    # 3. Assertions
    
    # skip_job
    # skip_me_timeout should SKIP due to timeout
    assert "[SKIP] skip_me_timeout (Timeout)" in result.stdout
    # skip_me_types should SKIP due to resolution failure
    assert "[SKIP] skip_me_types" in result.stdout
    
    # fail_job
    assert "[FAIL] fail_job" in result.stdout
    assert "[FAIL] mul" in result.stdout
    assert "[FAIL] negate" in result.stdout
    
    # pass_job
    assert "[PASS] pass_job" in result.stdout
    assert "[PASS] add" in result.stdout
    assert "[PASS] sub" in result.stdout
    
    # unknown_types_job replaced by mixed_bag (Should PASS because config provided types)
    assert "[PASS] mixed_bag" in result.stdout
    assert "[PASS] homogeneous_bag" in result.stdout
    
    # Should exit with code 1 because of the FAILures
    assert result.returncode == 1