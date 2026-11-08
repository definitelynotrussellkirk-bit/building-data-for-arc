"""Focused native-contract and finite teaching checks for the symmetry family.

These tests exercise the task-local adapter; protected Racket qualification is
the separate authority for the executed labels.  The small Python oracle below
is independent of the prototype's mirror and sampler.
"""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "4b787be81422"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
AXES = ("left_right", "top_bottom", "rotation_180", "bbox_major_axis")


@lru_cache(maxsize=None)
def _load(stem):
    path = PARAMETRIC / f"{stem}.py"
    assert path.is_file(), f"native symmetry {stem}.py is missing"
    name = f"_test_native_symmetry_{TASK_ID}_{stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _oracle(axis, grid):
    rows = [list(row) for row in grid]
    if axis == "bbox_major_axis":
        points = [(r, c) for r, row in enumerate(rows)
                  for c, color in enumerate(row) if color != 0]
        assert points, "the admitted input grammar requires foreground"
        r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
        c0, c1 = min(c for _, c in points), max(c for _, c in points)
        axis = "left_right" if r1 - r0 > c1 - c0 else "top_bottom"
    if axis == "left_right":
        reflected = [row[::-1] for row in rows]
    elif axis == "top_bottom":
        reflected = rows[::-1]
    elif axis == "rotation_180":
        reflected = [row[::-1] for row in rows[::-1]]
    else:
        raise AssertionError(f"unknown independent-oracle axis: {axis}")
    return [[1 if rows == reflected else 7]]


def _check_grids(episode):
    for pair in episode["train"] + episode["test"]:
        for name in ("input", "output"):
            grid = pair[name]
            assert type(grid) is list and 1 <= len(grid) <= 30
            assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
            assert all(type(row) is list and len(row) == len(grid[0])
                       and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
                       for row in grid)


def test_four_settings_preserve_the_exact_canonical_default():
    prototype = _load("prototype")
    assert tuple(prototype.SYMMETRY_AXES) == AXES
    adapter = _load("adapter")
    assert adapter.program({"symmetry_axis": "left_right"}) == (
        prototype.canonical_record()["program_solution"]
    )
    programs = [adapter.program({"symmetry_axis": axis}) for axis in AXES]
    assert all(type(program) is str and program.strip() for program in programs)
    assert len(set(programs)) == len(AXES)


def test_native_promotion_contract_accepts_owner_defaults_and_count_boundaries():
    from arcpuzzles.parametric_promotion import _jobs, settings_space

    path = PARAMETRIC / "promotion.json"
    assert path.is_file(), "native promotion.json is missing"
    contract = json.loads(path.read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == f"generators/{TASK_ID}/workspace/parametric/adapter.py"
    assert contract["default"] == {"symmetry_axis": "left_right"}
    assert settings_space(contract) == [{"symmetry_axis": axis} for axis in AXES]
    for demos, queries in ((3, 1), (3, 4), (6, 1), (6, 4)):
        jobs = _jobs(contract, seed=0, count=1, demos=demos, queries=queries)
        assert jobs[0]["demos"] == demos and jobs[0]["queries"] == queries
    for demos, queries in ((2, 4), (7, 4), (3, 0), (3, 5)):
        with pytest.raises(ValueError):
            _jobs(contract, seed=0, count=1, demos=demos, queries=queries)


@pytest.mark.parametrize("axis", AXES)
def test_adapter_obeys_independent_counts_with_deterministic_novel_inputs(axis):
    adapter = _load("adapter")
    settings = {"symmetry_axis": axis}
    for demos, queries in ((3, 1), (3, 4), (6, 1), (6, 4)):
        episode = adapter.generate(0, settings, demos, queries)
        assert episode == adapter.generate(0, settings, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program(settings)
        _check_grids(episode)
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"]) for pair in pairs]
        assert len(set(keys)) == len(keys)
        assert all(pair["output"] == _oracle(axis, pair["input"]) for pair in pairs)
    assert adapter.generate(0, settings, 3, 4) != adapter.generate(17, settings, 3, 4)


@pytest.mark.parametrize("axis", AXES)
def test_three_demos_identify_each_setting_without_using_query_labels(axis):
    adapter, prototype = _load("adapter"), _load("prototype")
    for seed in (0, 17):
        episode = adapter.generate(seed, {"symmetry_axis": axis}, 3, 4)
        survivors = [rival for rival in AXES if all(
            _oracle(rival, pair["input"]) == pair["output"]
            for pair in episode["train"]
        )]
        assert survivors == [axis]
        report = prototype.teaching_report(axis, episode["train"], episode["test"])
        assert report["passed"] is True
        assert report["declared_survivors"] == [axis]
        for rival, row in report["rivals"].items():
            if row["matches_all_demonstrations"]:
                assert row["query_disagreement_indices"] == [], rival


@pytest.mark.parametrize("axis", AXES)
def test_four_queries_include_both_labels_and_substantive_30_by_30_input(axis):
    adapter = _load("adapter")
    for seed in (0, 17):
        episode = adapter.generate(seed, {"symmetry_axis": axis}, 3, 4)
        assert {pair["output"][0][0] for pair in episode["test"]} == {1, 7}
        large = [pair["input"] for pair in episode["test"]
                 if len(pair["input"]) == len(pair["input"][0]) == 30]
        assert large, "four-query lessons must exercise the lawful 30x30 boundary"
        for grid in large:
            points = [(r, c) for r, row in enumerate(grid)
                      for c, color in enumerate(row) if color != 0]
            assert 30 <= len(points) < 900
            assert max(r for r, _ in points) - min(r for r, _ in points) + 1 >= 20
            assert max(c for _, c in points) - min(c for _, c in points) + 1 >= 20


@pytest.mark.parametrize("settings", [
    None, {}, {"symmetry_axis": True}, {"symmetry_axis": 0},
    {"symmetry_axis": "diagonal"}, {"symmetry_axis": ["left_right"]},
    {"symmetry_axis": "left_right", "extra": 1}, "left_right",
])
def test_adapter_rejects_undeclared_or_mistyped_settings(settings):
    adapter = _load("adapter")
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (0.0, 3, 4), ("0", 3, 4),
    (0, True, 4), (0, 3.0, 4), (0, 2, 4), (0, 7, 4),
    (0, 3, True), (0, 3, 4.0), (0, 3, 0), (0, 3, 5),
])
def test_adapter_rejects_invalid_seed_and_count_scalars(seed, demos, queries):
    adapter = _load("adapter")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"symmetry_axis": "left_right"}, demos, queries)
