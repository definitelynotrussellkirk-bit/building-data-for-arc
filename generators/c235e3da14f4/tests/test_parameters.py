"""Focused contract tests for the c235e3da14f4 parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "c235e3da14f4"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _family():
    path = HOME / "family.py"
    name = "_test_c235_parametric_family"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("content_hash") == TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]["program_solution"]


def test_canonical_program_is_exact_and_settings_fail_closed():
    family = _family()
    assert family.program({"size_rule": "smallest"}) == _canonical_program()
    assert family.program({"size_rule": "largest"}) != _canonical_program()
    for bad in ({}, {"size_rule": "middle"}, {"size_rule": "smallest", "x": 1}, None):
        with pytest.raises(ValueError):
            family.program(bad)


def test_generation_is_matched_prefix_stable_distinct_and_copy_isolated():
    family = _family()
    small = family.generate(17, {"size_rule": "smallest"}, 2, 1)
    full_small = family.generate(17, {"size_rule": "smallest"}, 6, 4)
    full_large = family.generate(17, {"size_rule": "largest"}, 6, 4)

    assert small["train"] == full_small["train"][:2]
    assert small["test"] == full_small["test"][:1]
    assert [p["input"] for p in full_small["train"] + full_small["test"]] == [
        p["input"] for p in full_large["train"] + full_large["test"]
    ]
    serialized = [json.dumps(p["input"]) for p in full_small["train"] + full_small["test"]]
    assert len(serialized) == len(set(serialized)) == 10

    full_small["train"][0]["input"][0][0] = 9
    assert family.generate(17, {"size_rule": "smallest"}, 6, 4)["train"][0]["input"][0][0] != 9


@pytest.mark.parametrize("seed", [0, 17, 211])
def test_first_two_demos_identify_each_setting_and_refute_declared_rivals(seed):
    family = _family()
    inputs = family.episode_inputs(seed)["train"][:2]
    for selected in family.MODES:
        expected = [family.solve(grid, selected) for grid in inputs]
        survivors = [
            mode for mode in family.MODES
            if [family.solve(grid, mode) for grid in inputs] == expected
        ]
        assert survivors == [selected]
        assert all(
            [family.rival_outputs(grid, selected)[rival] for grid in inputs] != expected
            for rival in family.RIVALS
        )


def test_public_turn_reveals_one_masked_query_and_no_private_metadata():
    family = _family()
    episode = family.generate(3, {"size_rule": "largest"}, 3, 4)
    for query_index in range(4):
        public = family.public_turn(episode, query_index)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert public["test"][0]["input"] == episode["test"][query_index]["input"]
        text = json.dumps(public, sort_keys=True)
        assert "program_solution" not in text
        assert "size_rule" not in text


def test_stress_query_is_substantive_and_wrong_intermediate_changes_crop():
    family = _family()
    grid = family.episode_inputs(17)["test"][3]
    assert [len(grid), len(grid[0])] == [30, 30]
    foreground = sum(value != 2 for row in grid for value in row)
    assert foreground >= 120
    assert any(value != 2 for value in grid[0] + grid[-1]) or any(
        row[0] != 2 or row[-1] != 2 for row in grid
    )

    smallest = family.dependency_intermediate(grid, "smallest")
    largest = family.dependency_intermediate(grid, "largest")
    sizes = [row["size"] for row in smallest["ordered_objects"]]
    assert smallest["selected_size"] == min(sizes)
    assert largest["selected_size"] == max(sizes)
    assert smallest["selected_bbox"] != largest["selected_bbox"]
    assert family.solve(grid, "smallest") != family.solve(grid, "largest")
