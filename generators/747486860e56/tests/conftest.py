"""Load this task from either its own library or a copied public runtime."""
from pathlib import Path
import importlib.util
import sys

import pytest


# Locate only an ancestor of this test, never a sibling checkout or cwd.
for ancestor in Path(__file__).resolve().parents:
    candidates = (ancestor, ancestor / "shared" / "runtime")
    helper_home = next((p for p in candidates if (p / "reviewer_support.py").is_file()), None)
    if helper_home is not None:
        sys.path.insert(0, str(helper_home))
        break
else:
    raise ImportError("This test requires the portable reviewer_support helper")

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
runtime_home = ROOT / "shared" / "runtime"
if runtime_home.is_dir():
    sys.path.insert(0, str(runtime_home))


@pytest.fixture(scope="session")
def generator():
    candidates = (
        ROOT / "generators" / "747486860e56" / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / "747486860e56" / "generator.py",
    )
    selected = next((p for p in candidates if p.is_file()), None)
    if selected is None:
        raise FileNotFoundError("Selected task generator not found in this test's root")
    spec = importlib.util.spec_from_file_location("reviewed_747486860e56", selected)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def pairs():
    return canonical_pairs("747486860e56", root=ROOT)
