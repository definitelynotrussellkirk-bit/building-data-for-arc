"""Focused contract tests for the aa14c6a9f111 anchor-area fill family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "aa14c6a9f111"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _family():
    path = HOME / "family.py"
    name = "_test_aa14c6a9f111_parametric_family"
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
    assert family.program({"render_rule": "all_outlines"}) == _canonical_program()
    assert family.program({"render_rule": "anchor_area_fill"}) != _canonical_program()
    for bad in ({}, {"render_rule": "fill"}, {"render_rule": "all_outlines", "x": 1}, None):
        with pytest.raises(ValueError):
            family.program(bad)


def test_generation_is_matched_prefix_stable_distinct_and_copy_isolated():
    family = _family()
    small = family.generate(17, {"render_rule": "all_outlines"}, 2, 1)
    full_outline = family.generate(17, {"render_rule": "all_outlines"}, 6, 4)
    full_fill = family.generate(17, {"render_rule": "anchor_area_fill"}, 6, 4)

    assert small["train"] == full_outline["train"][:2]
    assert small["test"] == full_outline["test"][:1]
    assert [p["input"] for p in full_outline["train"] + full_outline["test"]] == [
        p["input"] for p in full_fill["train"] + full_fill["test"]
    ]
    serialized = [json.dumps(p["input"]) for p in full_outline["train"] + full_outline["test"]]
    assert len(serialized) == len(set(serialized)) == 10

    full_outline["train"][0]["input"][0][0] = 9
    assert family.generate(17, {"render_rule": "all_outlines"}, 6, 4)["train"][0]["input"][0][0] != 9


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
            if rival != selected
        )


def test_public_turn_reveals_one_masked_query_and_no_private_metadata():
    family = _family()
    episode = family.generate(3, {"render_rule": "anchor_area_fill"}, 3, 4)
    for query_index in range(4):
        public = family.public_turn(episode, query_index)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert public["test"][0]["input"] == episode["test"][query_index]["input"]
        text = json.dumps(public, sort_keys=True)
        assert "program_solution" not in text
        assert "render_rule" not in text


def test_stress_query_is_substantive_and_wrong_intermediate_changes_rendering():
    family = _family()
    grid = family.episode_inputs(17)["test"][3]
    assert [len(grid), len(grid[0])] == [30, 30]
    assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid) and any(row[-1] for row in grid)

    canonical = family.solve(grid, "all_outlines")
    alternate = family.solve(grid, "anchor_area_fill")
    assert sum(value != 0 for row in canonical for value in row) >= 200
    assert sum(value != 0 for row in alternate for value in row) >= 300
    intermediate = family.dependency_intermediate(grid, "anchor_area_fill")
    assert intermediate["anchor_area"] == 900
    assert intermediate["selected_index"] == 2
    assert canonical != alternate
