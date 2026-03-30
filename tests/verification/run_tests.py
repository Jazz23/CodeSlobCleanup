#!/usr/bin/env python3
# /// script
# dependencies = [
#     "pytest",
#     "pytest-cov",
#     "hypothesis",
#     "numpy",
#     "matplotlib",
# ]
# ///
"""
Run all verification unit tests with 100% coverage enforcement.

Usage:
    python tests/verification/run_tests.py
    python tests/verification/run_tests.py -v
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills" / "code-slob-cleanup" / "scripts"
)
TESTS_DIR = Path(__file__).resolve().parent


VERIFICATION_SCRIPTS = ["orchestrator.py", "verify.py", "common.py", "benchmark.py"]

# Non-verification scripts in the same directory to omit from coverage
OMIT_SCRIPTS = [
    "clean_untested.py", "duplication.py", "exclusions.py",
    "identify.py", "metrics.py", "semantic.py",
]


if __name__ == "__main__":
    extra_args = sys.argv[1:]
    omit_args = ",".join(str(SCRIPTS_DIR / s) for s in OMIT_SCRIPTS)
    cmd = [
        sys.executable, "-m", "pytest",
        str(TESTS_DIR),
        f"--cov={SCRIPTS_DIR}",
        f"--cov-config={TESTS_DIR / '.coveragerc'}",
        "--cov-report=term-missing",
        "--cov-fail-under=100",
        "-v",
        "--tb=short",
        *extra_args,
    ]
    result = subprocess.run(cmd, cwd=str(TESTS_DIR))
    sys.exit(result.returncode)
