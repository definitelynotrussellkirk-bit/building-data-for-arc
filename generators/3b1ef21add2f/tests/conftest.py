"""Portable subject and canonical fixtures for library and staged task tests."""
import importlib.util
from pathlib import Path
import sys

import pytest


# In a staged runtime reviewer_support is at the root. For direct library
# collection, locate its public source by walking ancestors, never by depth.
try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        support = ancestor / "shared" / "runtime"
        if (support / "reviewer_support.py").is_file():
            sys.path.insert(0, str(support))
            break
    from reviewer_support import canonical_pairs, find_root


TASK_ID = "3b1ef21add2f"
ROOT = find_root(__file__)


# Public task_tests uses pytest's importlib mode. Load the task-local oracle
# under a unique name so it neither depends on cwd nor collides with other tasks.
_oracle_spec = importlib.util.spec_from_file_location(
    "oracle_3b1ef21add2f", Path(__file__).with_name("oracle.py"))
_oracle_module = importlib.util.module_from_spec(_oracle_spec)
sys.modules[_oracle_spec.name] = _oracle_module
_oracle_spec.loader.exec_module(_oracle_module)


@pytest.fixture(scope="session")
def library_root():
    return ROOT


@pytest.fixture(scope="session")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT)


@pytest.fixture(scope="session")
def generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    assert source is not None, f"Selected generator is absent under {ROOT}"
    spec = importlib.util.spec_from_file_location("selected_3b1ef21add2f", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
