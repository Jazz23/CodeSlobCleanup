import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "code-slob-cleanup" / "scripts"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR
