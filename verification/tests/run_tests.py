# /// script
# dependencies = [
#     "pytest",
#     "pytest-xdist",
#     "hypothesis",
#     "matplotlib",
#     "numpy",
# ]
# ///

import sys
import os
import subprocess
from pathlib import Path

# Configure pycache to be created in the root of the active git repository
try:
    # Try to find git root
    _git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True).strip()
    _pycache_dir = os.path.join(_git_root, "__pycache__")
    os.makedirs(_pycache_dir, exist_ok=True)
    sys.pycache_prefix = _pycache_dir
    os.environ["PYTHONPYCACHEPREFIX"] = _pycache_dir
except Exception:
    pass

import pytest

if __name__ == "__main__":
    # Add project root to sys.path
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    
    # Run pytest on the integration tests
    ret = pytest.main([
        "-n", "auto", 
        "-s", 
        "verification/tests/integration/"
    ])
    sys.exit(ret)
