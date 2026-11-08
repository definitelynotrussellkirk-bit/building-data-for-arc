"""Portable selected-source/canonical access, bound to this test's own tree."""
from pathlib import Path
import importlib.util
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    helper_home = next((p for p in (ancestor, ancestor / "shared" / "runtime")
                        if (p / "reviewer_support.py").is_file()), None)
    if helper_home is not None:
        sys.path.insert(0, str(helper_home))
        break
else:
    raise ImportError("Portable reviewer_support missing")

from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
if (ROOT / "shared" / "runtime").is_dir():
    sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def pytest_addoption(parser):
    parser.addoption("--generator-source", default=None,
                     help="Explicit frozen source for a separately labeled baseline run")


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def generator(request):
    source = request.config.getoption("--generator-source")
    if source:
        selected = Path(source).resolve()
    else:
        selected = next(p for p in (
            ROOT / "generators" / "8738d400fb96" / "generator.py",
            ROOT / "puzzle_generators" / "per_puzzle" / "8738d400fb96" / "generator.py",
        ) if p.is_file())
    return load_file("reviewed_8738d400fb96", selected)


@pytest.fixture(scope="session")
def oracle():
    return load_file("independent_8738d400fb96", Path(__file__).with_name("oracle.py"))


@pytest.fixture(scope="session")
def pairs():
    return canonical_pairs("8738d400fb96", root=ROOT)
