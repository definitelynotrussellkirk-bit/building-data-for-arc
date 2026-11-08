"""Focused tests for the proposed pink midpoint tie prototype."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


proto = _load("ee6_parametric_prototype", PROTOTYPE)
gen = _load("ee6_selected_generator", HOME / "generator.py")


def _even_witness():
    grid = [[8 for _ in range(9)] for _ in range(9)]
    for row in range(2, 4):
        for col in range(2, 6):
            grid[row][col] = 6
    grid[2][6] = 9
    assert gen.self_check(grid) == []
    return grid


def test_default_program_is_verbatim_canonical_and_upper_changes_only_ties():
    canonical = proto.canonical_program()
    assert proto.program_for("lower") == canonical
    upper = proto.program_for("upper")
    assert upper != canonical
    assert canonical.count("(quotient (+ r1 r2) 2)") == 1
    assert canonical.count("(quotient (+ c1 c2) 2)") == 1
    assert upper.count("(quotient (+ r1 r2 1) 2)") == 1
    assert upper.count("(quotient (+ c1 c2 1) 2)") == 1


def test_python_settings_split_a_lawful_even_axis_and_default_matches_selected_rule():
    grid = _even_witness()
    lower = proto.python_apply(grid, "lower")
    upper = proto.python_apply(grid, "upper")
    assert lower == gen.rule_mirror(grid)
    assert upper == gen.CANONICAL_SHORTCUTS["pink_upper_midpoint"](grid)
    differing = [
        (row, col)
        for row in range(9)
        for col in range(9)
        if lower[row][col] != upper[row][col]
    ]
    assert differing == [(2, 3), (2, 4)]


def test_parameter_is_chosen_once_deterministically_and_both_values_are_reachable():
    choices = [proto.choose_setting(seed) for seed in range(8)]
    assert choices == [proto.choose_setting(seed) for seed in range(8)]
    assert set(choices) == set(proto.ALLOWED_VALUES)


def test_every_episode_input_is_lawful_and_distinguishes_both_settings():
    inputs = proto.episode_inputs(2301)
    assert len(inputs) == 4
    assert len({repr(grid) for grid in inputs}) == 4
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert proto.python_apply(grid, "lower") != proto.python_apply(grid, "upper")


def test_public_challenge_redacts_hidden_setting_rule_and_query_answer():
    grid = _even_witness()
    episode = {
        "meta": {
            "task_id": proto.TASK_ID,
            "prototype": True,
            "seed": 4,
            proto.PARAMETER_NAME: "lower",
            "racket_program": "secret",
        },
        "train": [{"input": deepcopy(grid), "output": proto.python_apply(grid, "lower")}],
        "test": [{"input": deepcopy(grid), "output": proto.python_apply(grid, "lower")}],
    }
    public = proto.public_challenge(episode)
    blob = repr(public)
    assert proto.PARAMETER_NAME not in blob
    assert "secret" not in blob
    assert "output" not in public["test"][0]
    assert public["train"][0]["output"] == episode["train"][0]["output"]


@pytest.mark.parametrize("setting", proto.ALLOWED_VALUES)
def test_exact_racket_program_matches_python_on_even_witness(setting):
    grid = _even_witness()
    outputs = proto.run_program(proto.program_for(setting), [grid])
    assert outputs == [proto.python_apply(grid, setting)]


def test_invalid_parameter_values_fail_loudly():
    for bad in (None, True, 0, "middle"):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(bad)
