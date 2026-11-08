"""Focused contract and parametric tests for 758360aea29b."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "758360aea29b"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator(TASK, root=ROOT)


def _load(name: str):
    path = ROOT / f"generators/{TASK}/workspace/parametric/{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _colors(grid):
    return {value for row in grid for value in row if value}



def test_self_check_accepts_every_labeled_canonical_input():
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert GEN.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])

def test_invalid_calls_and_negative_textures_are_rejected():
    cases = [
        ({"unknown_axis": 1}, TypeError),
        ({"n_objects": 2.75}, ValueError),
        ({"n_objects": True}, ValueError),
        ({"grid_h": 9}, ValueError),
        ({"grid_w": 23}, ValueError),
        ({"palette_kind": "infrared"}, ValueError),
        ({"texture": "no_objects"}, ValueError),
    ]
    for overrides, error in cases:
        with pytest.raises(error):
            GEN.generate(991, 0, **overrides)
    with pytest.raises(ValueError):
        GEN.generate(True, 0)


def test_each_difficulty_has_a_canonical_profile_anchor():
    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(0, 0, difficulty=difficulty)
        observed = GEN.observe_overrides(grid)
        assert observed == {"grid_h": 10, "grid_w": 12, "n_objects": 3}
        assert len({value for row in grid for value in row}) == 4
        assert GEN.self_check(grid) == []


def test_supported_palette_overrides_are_realized_and_structurally_valid():
    for index, kind in enumerate(GEN.PALETTE_KINDS):
        grid = GEN.generate(
            2000 + index,
            index,
            difficulty="medium",
            n_objects=4,
            palette_kind=kind,
        )
        assert GEN.self_check(grid) == []
        assert _colors(grid) <= set(GEN.PALETTES[kind])
        alias = GEN.generate(
            2000 + index,
            index,
            difficulty="medium",
            n_objects=4,
            texture=kind,
        )
        assert alias == grid


def test_parametric_default_is_exact_authority_and_inputs_are_matched():
    adapter = _load("adapter")
    prototype = _load("prototype")
    default = {"comparison_mode": "pairwise_width"}
    alternate = {"comparison_mode": "pivot_distance"}
    assert adapter.program(default) == _canonical_program()

    left = adapter.generate(17, default, 3, 4)
    right = adapter.generate(17, alternate, 3, 4)
    assert len(left["train"]) == len(right["train"]) == 3
    assert len(left["test"]) == len(right["test"]) == 4
    assert [p["input"] for p in left["train"] + left["test"]] == [
        p["input"] for p in right["train"] + right["test"]
    ]
    assert left["train"][0]["output"] != right["train"][0]["output"]
    for settings, episode in ((default, left), (alternate, right)):
        survivors = [
            candidate
            for candidate in prototype.SETTINGS
            if all(
                prototype.transform(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [settings]


def test_parametric_prefix_independence_and_30x30_query():
    adapter = _load("adapter")
    settings = {"comparison_mode": "pivot_distance"}
    short = adapter.generate(99, settings, 2, 1)
    long = adapter.generate(99, settings, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    stress = long["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    assert GEN.self_check(stress["input"]) == []
    inputs = [json.dumps(pair["input"]) for pair in long["train"] + long["test"]]
    assert len(inputs) == len(set(inputs))


def test_pivot_distance_uses_tallest_rectangles_width():
    prototype = _load("prototype")
    grid = [
        [2, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4],
    ]
    assert prototype.transform(grid, {"comparison_mode": "pairwise_width"}) == [
        [1, 3, 3],
        [2, 1, 3],
        [2, 2, 1],
    ]
    assert prototype.transform(grid, {"comparison_mode": "pivot_distance"}) == [
        [1, 2, 1],
        [3, 1, 3],
        [1, 2, 1],
    ]

def test_parametric_object_extraction_keeps_touching_colors_separate():
    prototype = _load("prototype")
    grid = [[2, 3]]
    assert prototype.intermediate(grid, {"comparison_mode": "pairwise_width"}) == {
        "object_widths": [1, 1],
        "comparison_scores": [1, 1],
    }
    assert prototype.transform(grid, {"comparison_mode": "pairwise_width"}) == [
        [1, 1],
        [1, 1],
    ]

