"""Focused tests for the isolated episode-level motion prototype."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "3dc5b297cfa2"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("motion_prototype", PROTOTYPE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    import json

    for line in canonical_path(find_root(__file__)).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_default_setting_is_exact_canonical_program_and_choice_is_episode_stable():
    mod = _load_prototype()
    assert mod.materialize_program("top", "right") == _canonical_program()
    assert mod.choose_parameters(17) == mod.choose_parameters(17)
    assert {
        tuple(sorted(mod.choose_parameters(seed).items())) for seed in range(64)
    } == {
        (("direction", "left"), ("moving_half", "bottom")),
        (("direction", "left"), ("moving_half", "top")),
        (("direction", "right"), ("moving_half", "bottom")),
        (("direction", "right"), ("moving_half", "top")),
    }


def test_invalid_parameter_values_fail_before_episode_sampling():
    mod = _load_prototype()
    for seed in (True, -1, 1.5, "1"):
        with pytest.raises(ValueError):
            mod.choose_parameters(seed)
    for moving_half, direction in (("middle", "right"), ("top", "up"), (1, "left")):
        with pytest.raises(ValueError):
            mod.choose_parameters(1, moving_half=moving_half, direction=direction)


def test_four_settings_execute_distinct_transformations_without_mutating_input():
    mod = _load_prototype()
    grid = [
        [8] * 11,
        [8, 8, 8, 8, 0, 2, 0, 8, 8, 8, 8],
        [8, 8, 8, 8, 0, 2, 0, 8, 8, 8, 8],
        [8, 8, 8, 8, 0, 2, 0, 8, 8, 8, 8],
        [8, 8, 8, 8, 0, 2, 0, 8, 8, 8, 8],
        [8] * 11,
    ]
    original = copy.deepcopy(grid)
    outputs = {
        (half, direction): mod.python_transform(grid, half, direction)
        for half in mod.MOVING_HALVES
        for direction in mod.DIRECTIONS
    }
    assert grid == original
    assert len({repr(output) for output in outputs.values()}) == 4


def test_public_challenge_removes_hidden_setting_program_and_query_answers():
    mod = _load_prototype()
    private = {
        "seed": 9,
        "parameter": {"moving_half": "bottom", "direction": "left"},
        "program": "secret",
        "train": [{"input": [[0, 2]], "output": [[2, 0]]}],
        "test": [{"input": [[0, 3]], "output": [[3, 0]]}],
    }
    public = mod.public_challenge(private)
    assert set(public) == {"train", "test"}
    assert public["test"] == [{"input": [[0, 3]]}]
    public["train"][0]["input"][0][0] = 9
    assert private["train"][0]["input"] == [[0, 2]]
