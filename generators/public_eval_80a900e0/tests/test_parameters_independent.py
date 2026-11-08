"""Independent geometry oracle and a frozen plausible-rule bank.

These helpers were authored from original examples and the family contract
before implementation inspection. They use a rectangle-search algorithm.
"""
import copy
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


oracle = load(HERE / "parameter_rivals.py", "independent_beam_rivals")
cases = load(HERE / "parameter_cases.py", "independent_beam_cases")
adapter = load(TASK_HOME / "workspace/parametric/adapter.py", "independent_beam_adapter")


@pytest.mark.parametrize("name,grid", cases.cases(), ids=lambda item: item if isinstance(item,str) else None)
@pytest.mark.parametrize("beam", ["walls", "solid"])
def test_independent_hand_geometry(name, grid, beam):
    original = copy.deepcopy(grid)
    expected = oracle.solve(grid, beam)
    actual = adapter.mirror(grid, {"beam": beam})
    assert actual == expected, name
    assert grid == original
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value != 1:
                assert actual[r][c] == value


@pytest.mark.parametrize("seed", [0,17])
@pytest.mark.parametrize("beam", ["walls", "solid"])
def test_generated_lessons_against_frozen_rule_bank(seed, beam):
    episode = adapter.generate(seed, {"beam":beam}, 3, 4)
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == oracle.solve(pair["input"],beam)
    for name, _, _ in oracle.RIVALS:
        fits = all(oracle.rival_output(name,p["input"],beam) == p["output"]
                   for p in episode["train"])
        if fits:
            assert all(oracle.rival_output(name,p["input"],beam) == p["output"]
                       for p in episode["test"]), name
