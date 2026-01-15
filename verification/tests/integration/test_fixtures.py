# /// script
# dependencies = [
#     "pytest",
# ]
# ///

import os
from pathlib import Path

def test_fixtures_structure():
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
    assert fixtures_dir.exists(), "Fixtures directory missing"
    
    scenarios = list(fixtures_dir.iterdir())
    assert len(scenarios) >= 3, "Expected at least 3 scenario categories"
    
    for scenario in scenarios:
        if not scenario.is_dir():
            continue
        for job in scenario.iterdir():
            if not job.is_dir():
                continue
            assert (job / "original.py").exists(), f"Missing original.py in {job}"
            assert (job / "refactored.py").exists(), f"Missing refactored.py in {job}"
