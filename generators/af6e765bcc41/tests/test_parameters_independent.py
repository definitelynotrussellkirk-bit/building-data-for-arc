"""Portable independent regressions for the frozen 39-rule teaching bank.

The predictions in adjacent parameter_rivals.py do not import the adapter or
prototype.  Rivals fit labeled demonstrations before any query is inspected.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bank():
    return _load(HOME / "tests/parameter_rivals.py", "_af6e765bcc41_independent_bank")


@pytest.fixture(scope="module")
def adapter():
    return _load(HOME / "workspace/parametric/adapter.py", "_af6e765bcc41_independent_adapter")


PREVIOUS_AMBIGUITIES = [
    (0, "single_gap", ("repair_except_top",)),
    (1, "single_gap", ("repair_except_left",)),
    (6, "single_gap", ("repair_except_top",)),
    (7, "single_gap", ("repair_except_bottom",)),
    (9, "single_gap", ("repair_except_bottom", "repair_nonsquare_only")),
    (11, "single_gap", ("repair_except_left",)),
    (12, "single_gap", ("repair_except_bottom",)),
    (13, "single_gap", ("repair_except_left",)),
    (14, "single_gap", ("repair_except_top",)),
    (15, "single_gap", ("repair_except_top",)),
    (18, "single_gap", ("repair_nonsquare_only",)),
    (19, "none", ("fill_square_only",)),
    (20, "single_gap", ("repair_nonsquare_only",)),
    (28, "none", ("fill_square_only",)),
]


@pytest.mark.parametrize("seed,completion,rivals", PREVIOUS_AMBIGUITIES)
def test_demos_refute_previously_query_changing_rivals(adapter, bank, seed, completion, rivals):
    settings = {"completion": completion}
    episode = adapter.generate(seed, settings, demos=3, queries=4)
    fitted = bank.fit_demos(episode["train"], settings)
    assert not fitted["execution_errors"]
    # These remain substantive query distinctions: the sampler repair must
    # strengthen its demonstrations, rather than remove the difficult queries.
    for name in rivals:
        predict = bank.RIVAL_BY_NAME[name].predict
        assert any(predict(pair["input"], completion) != pair["output"]
                   for pair in episode["test"]), (seed, completion, name, "lost query witness")
    assert not set(rivals) & set(fitted["survivors"]), (seed, completion, fitted["survivors"])


def test_frozen_bank_has_no_query_changing_demo_survivors_in_bounded_census(adapter, bank):
    assert len(bank.RIVALS) == 39
    unresolved = []
    for seed in range(32):
        for completion in ("none", "single_gap"):
            settings = {"completion": completion}
            episode = adapter.generate(seed, settings, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == bank.model(pair["input"], settings)
            fitted = bank.fit_demos(episode["train"], settings)
            assert not fitted["execution_errors"]
            queried = bank.assess_queries(episode["test"], settings, fitted)
            assert not queried["execution_errors"]
            if queried["query_disagreeing_survivors"]:
                unresolved.append((seed, completion, queried["query_disagreeing_survivors"]))
    assert not unresolved, unresolved


@pytest.mark.parametrize("seed,completion", ((2, "none"), (1, "single_gap")))
def test_isolated_actions_refute_component_count_gate(adapter, bank, seed, completion):
    """Separate review finding; the original 39-rule bank stays unchanged."""
    settings = {"completion": completion}
    episode = adapter.generate(seed, settings, demos=3, queries=4)
    def rival(grid):
        if len(bank.components(grid)) >= 2:
            return bank.model(grid, settings)
        return bank.copy_grid(grid)
    fitted_to_demos = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
    assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), "lost isolated query witness"
    assert not fitted_to_demos, "all visible demonstrations permit an arbitrary minimum-two-orange-components gate"


def _case(bank, name):
    grid = [[0] * 13 for _ in range(11)]
    box = (2, 2, 8, 10)
    for r, c in bank.border(box):
        grid[r][c] = 7
    if name == "nested":
        for r, c in bank.border((4, 4, 6, 8)):
            grid[r][c] = 7
        grid[5][5], grid[5][6] = 3, 8
    elif name == "merged":
        grid[2][6], grid[1][6] = 0, 7
    elif name == "diagonal":
        grid[1][1] = 7
    elif name == "occupied_gap":
        grid[2][6] = 8
    elif name == "two_gaps":
        grid[2][5] = grid[2][6] = 0
    return grid


@pytest.mark.parametrize("name", ("nested", "merged", "diagonal", "occupied_gap", "two_gaps"))
def test_independent_component_support_and_preservation(adapter, bank, name):
    grid = _case(bank, name)
    original = bank.copy_grid(grid)
    for completion in ("none", "single_gap"):
        settings = {"completion": completion}
        expected = bank.intermediate_support(grid, settings)
        assert adapter.first_stage(grid, settings) == expected["middle"]
        assert adapter.mirror(grid, settings) == expected["output"]
        assert bank.first_stage(expected["middle"], settings) == expected["middle"]
        if name == "merged":
            assert not expected["fill_mask"]
            assert expected["repair_mask"] == ([(2, 6)] if completion == "single_gap" else [])
        elif name in ("occupied_gap", "two_gaps"):
            assert expected["output"] == grid
        else:
            assert expected["fill_mask"]
        if name == "nested":
            assert expected["output"][5][5:7] == [3, 8]
        assert grid == original
