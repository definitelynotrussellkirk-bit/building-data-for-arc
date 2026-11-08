"""Focused contract tests for the 84fd4bcdc53c bend-order family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "84fd4bcdc53c"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _family():
    path = HOME / "family.py"
    name = "_test_84fd_parametric_family"
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
    assert family.program({"bend_order": "horizontal_then_vertical"}) == _canonical_program()
    assert family.program({"bend_order": "vertical_then_horizontal"}) != _canonical_program()
    for bad in ({}, {"bend_order": "diagonal"}, {"bend_order": "horizontal_then_vertical", "x": 1}, None):
        with pytest.raises(ValueError):
            family.program(bad)


def test_generation_is_matched_prefix_stable_distinct_and_copy_isolated():
    family = _family()
    short = family.generate(17, {"bend_order": "horizontal_then_vertical"}, 2, 1)
    full_h = family.generate(17, {"bend_order": "horizontal_then_vertical"}, 6, 4)
    full_v = family.generate(17, {"bend_order": "vertical_then_horizontal"}, 6, 4)
    assert short["train"] == full_h["train"][:2]
    assert short["test"] == full_h["test"][:1]
    assert [p["input"] for p in full_h["train"] + full_h["test"]] == [
        p["input"] for p in full_v["train"] + full_v["test"]
    ]
    serialized = [json.dumps(p["input"]) for p in full_h["train"] + full_h["test"]]
    assert len(serialized) == len(set(serialized)) == 10
    full_h["train"][0]["input"][0][0] = 9
    assert family.generate(17, {"bend_order": "horizontal_then_vertical"}, 6, 4)["train"][0]["input"][0][0] != 9


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


def test_inputs_keep_distinct_endpoint_rows_and_columns_per_color():
    family = _family()
    for grid in family.episode_inputs(5)["train"] + family.episode_inputs(5)["test"]:
        for points in family.endpoint_groups(grid).values():
            assert 3 <= len(points) <= 4
            assert len({row for row, _ in points}) == len(points)
            assert len({col for _, col in points}) == len(points)


def test_public_turn_reveals_one_masked_query_and_no_private_metadata():
    family = _family()
    episode = family.generate(3, {"bend_order": "vertical_then_horizontal"}, 3, 4)
    for query_index in range(4):
        public = family.public_turn(episode, query_index)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert public["test"][0]["input"] == episode["test"][query_index]["input"]
        text = json.dumps(public, sort_keys=True)
        assert "program_solution" not in text
        assert "bend_order" not in text


def test_stress_query_is_substantive_and_wrong_trace_changes_render():
    family = _family()
    grid = family.episode_inputs(17)["test"][3]
    assert [len(grid), len(grid[0])] == [30, 30]
    assert any(value for value in grid[0] + grid[-1]) or any(row[0] or row[-1] for row in grid)
    horizontal = family.dependency_intermediate(grid, "horizontal_then_vertical")
    vertical = family.dependency_intermediate(grid, "vertical_then_horizontal")
    assert horizontal["traces"] != vertical["traces"]
    out_h = family.solve(grid, "horizontal_then_vertical")
    out_v = family.solve(grid, "vertical_then_horizontal")
    assert out_h != out_v
    assert sum(value != 0 for row in out_h for value in row) >= 150
    assert sum(value != 0 for row in out_v for value in row) >= 150
