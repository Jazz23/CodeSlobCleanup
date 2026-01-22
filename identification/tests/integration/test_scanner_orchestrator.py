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
    
    # 2. Create a "slob" file (complex)
    slob_code = """
def complex_logic(n):
    res = 0
    for i in range(n):
        if i % 2 == 0:
            for j in range(i):
                if j > 5:
                    res += j
                else:
                    res -= j
        else:
            res += i
    return res
"""
    (project_dir / "slob.py").write_text(slob_code)
    
    # Path to orchestrator
    # identification/tests/integration/test_scanner_orchestrator.py -> ... -> identification
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
        
    assert "candidates" in data
    assert "clean.py" in str(data) # Should be listed (maybe with low score) or not? 
    # Let's say we report everything but sort/flag them.
    
    candidates = data["candidates"]
    
    # Find entries
    clean_entry = next((c for c in candidates if "clean.py" in c["file_path"]), None)
    slob_entry = next((c for c in candidates if "slob.py" in c["file_path"]), None)
    
    assert clean_entry is not None
    assert slob_entry is not None
    
    # Assert scores
    assert slob_entry["score"] > clean_entry["score"]
    assert slob_entry["is_slob"] is True
    assert clean_entry["is_slob"] is False

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
