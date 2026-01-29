# /// script
# dependencies = [
#     "pytest",
# ]
# ///

import os
import json
import subprocess
import sys
from pathlib import Path
import pytest

def test_scanner_orchestrator_flow(tmp_path):
    # Setup mock project
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # 1. Create a "clean" file
    (project_dir / "clean.py").write_text("def add(a, b): return a + b")
    
    # 2. Create a "slob" file (very complex)
    slob_code = """
def super_complex_logic(a, b, c, d, e):
    res = 0
    if a:
        if b:
            for i in range(10):
                if i > 5:
                    for j in range(10):
                        if j % 2 == 0:
                            if c:
                                res += 1
                            else:
                                res -= 1
                        elif d:
                            if e:
                                res *= 2
    else:
        for k in range(100):
            if k == 50:
                return k
    return res
"""
    (project_dir / "slob.py").write_text(slob_code)
    
    # 3. Create an excluded directory with a slob file
    exclude_dir = project_dir / "venv"
    exclude_dir.mkdir()
    (exclude_dir / "bad.py").write_text("def deep():" + "    if True:" * 15 + " pass")

    # Path to orchestrator
    ident_root = Path(__file__).resolve().parents[2] 
    orchestrator_path = ident_root / ".gemini" / "skills" / "scanner" / "scripts" / "orchestrator.py"
    
    # Run orchestrator
    cmd = [
        "uv", "run", str(orchestrator_path),
        "--target-dir", str(project_dir)
    ]
    
    # We expect it to succeed
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    # Check if report was created
    report_path = project_dir / "scan_report.json"
    assert report_path.exists()
    
    # Validate Report Content
    with open(report_path) as f:
        data = json.load(f)
        
    assert "slob_candidates" in data
    assert data["files_scanned"] == 2 # clean.py and slob.py (bad.py in venv is excluded)
    
    candidates = data["slob_candidates"]
    
    # Find entry for slob.py
    slob_entry = next((c for c in candidates if "slob.py" in c["file"]), None)
    
    assert slob_entry is not None
    assert slob_entry["function"] == "super_complex_logic"
    assert "metrics" in slob_entry
    assert slob_entry["metrics"]["complexity"] > 1
    assert slob_entry["high_severity"] is True
    
    # clean.py should NOT be in slob_candidates because it's not severe enough
    clean_entry = next((c for c in candidates if "clean.py" in c["file"]), None)
    assert clean_entry is None
    
    # venv/bad.py should NOT be in slob_candidates because venv is excluded
    bad_entry = next((c for c in candidates if "bad.py" in c["file"]), None)
    assert bad_entry is None

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
