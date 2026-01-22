# /// script
# dependencies = [
#     "pytest",
#     "radon",
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
    
    # Run pytest on the identification tests
    ret = pytest.main(["-v", "identification/tests/"])
    sys.exit(ret)
