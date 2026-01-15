# /// script
# dependencies = [
#     "pytest",
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import pytest
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    # Add project root to sys.path
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    
    # Run pytest on the integration tests
    ret = pytest.main(["-s", "verification/tests/integration/"])
    sys.exit(ret)
