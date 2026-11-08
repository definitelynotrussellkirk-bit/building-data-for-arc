"""Focused regressions for the reviewed f563fafba6ac generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "f563fafba6ac"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _objects(grid):
    """Independent 4-connected object and enclosed-hole analysis."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)

            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            r1 = max(r for r, _ in cells)
            c1 = max(c for _, c in cells)
            normalized = {(r - r0, c - c0) for r, c in cells}
            shape_h = r1 - r0 + 1
            shape_w = c1 - c0 + 1
            background = {
                (r, c)
                for r in range(shape_h)
                for c in range(shape_w)
                if (r, c) not in normalized
            }
            visited_background = set()
            holes = 0
            for start in background:
                if start in visited_background:
                    continue
                component = [start]
                visited_background.add(start)
                touches_edge = (
                    start[0] in (0, shape_h - 1)
                    or start[1] in (0, shape_w - 1)
                )
                while component:
                    r, c = component.pop()
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        point = (r + dr, c + dc)
                        if point in background and point not in visited_background:
                            visited_background.add(point)
                            component.append(point)
                            touches_edge |= (
                                point[0] in (0, shape_h - 1)
                                or point[1] in (0, shape_w - 1)
                            )
                if not touches_edge:
                    holes += 1
            objects.append(
                {
                    "color": color,
                    "cells": normalized,
                    "height": shape_h,
                    "width": shape_w,
                    "holes": holes,
                    "area": len(normalized),
                    "row": r0,
                    "col": c0,
                }
            )
    return objects


def _pack(objects, key):
    ordered = sorted(objects, key=key)
    out_h = max(obj["height"] for obj in ordered)
    out_w = sum(obj["width"] for obj in ordered) + len(ordered) - 1
    output = [[0] * out_w for _ in range(out_h)]
    left = 0
    for obj in ordered:
        for row, col in obj["cells"]:
            output[row][left + col] = obj["color"]
        left += obj["width"] + 1
    return output


def _official_output(grid):
    return _pack(_objects(grid), lambda obj: (obj["holes"], obj["color"]))


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_rule_pin_canonical_acceptance_and_independent_oracle():
    assert GEN.RULE_HASH == "458549b829a3"
    assert callable(GEN.self_check)
    assert callable(GEN.observe_overrides)
    assert callable(GEN.rule_mirror)
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _official_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_in_every_band(band):
    requested = {
        "grid_h": 11,
        "grid_w": 15,
        "n_objects": 4,
        "hole_counts": [0, 1, 1, 2],
    }
    grid = GEN.generate(911, 7, difficulty=band, **requested)
    observed = GEN.observe_overrides(grid)
    assert GEN.self_check(grid) == []
    assert observed["grid_h"] == requested["grid_h"]
    assert observed["grid_w"] == requested["grid_w"]
    assert observed["n_objects"] == requested["n_objects"]
    assert observed["hole_counts"] == sorted(requested["hole_counts"])
    assert GEN.rule_mirror(grid) == _official_output(grid)
    assert len(GEN.rule_mirror(grid)) <= len(grid)
    assert len(GEN.rule_mirror(grid)[0]) <= len(grid[0])
    assert grid == GEN.generate(911, 7, difficulty=band, **requested)


@pytest.mark.parametrize(
    "override",
    [
        {"unknown_axis": 1},
        {"grid_h": 10},
        {"grid_h": 25},
        {"grid_w": 14},
        {"grid_w": 29},
        {"n_objects": 2},
        {"n_objects": 5},
        {"hole_counts": [0, 1]},
        {"hole_counts": [0, 0, 0]},
        {"hole_counts": [0, 1, 3]},
        {"grid_h": True},
        {"grid_w": 15.0},
        {"n_objects": "3"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(override):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **override)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_are_lawful_nonexpanding_and_semantically_rich(band):
    expected_witnesses = {"hole_priority", "color_tiebreak", "holes_not_area"}
    for index in range(32):
        grid = GEN.generate(12000 + index, index * 11 + 3, difficulty=band)
        assert GEN.self_check(grid) == []
        output = GEN.rule_mirror(grid)
        assert output == _official_output(grid)
        assert len(output) <= len(grid)
        assert len(output[0]) <= len(grid[0])
        assert grid == GEN.generate(12000 + index, index * 11 + 3, difficulty=band)
        fired = {
            name
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if predicate(grid)
        }
        assert fired == expected_witnesses
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != output, name


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"stable_input_ties", "area_then_color"}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_census_has_exact_canonical_support_in_every_band(band):
    canonical_profiles = {_profile(pair["input"]) for pair in PAIRS}
    generated_profiles = set()
    for index in range(20):
        seed = _pinned_seed(band, index)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        assert GEN.self_check(grid) == []
        generated_profiles.add(_profile(grid))
    assert generated_profiles & canonical_profiles, (
        band,
        generated_profiles,
        canonical_profiles,
    )


def test_three_demo_lesson_refutes_all_declared_competitors():
    grids = [GEN.generate(8123, index, difficulty="medium") for index in range(4)]
    pairs = [{"input": grid, "output": _official_output(grid)} for grid in grids]
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(11)]],
)
def test_self_check_reports_malformed_grids_without_raising(grid):
    assert GEN.self_check(grid)


def test_hard_draws_reach_the_canonical_largest_object_area():
    """The canonical two-hole object has 19 cells; hard draws must retain it."""
    for index in range(1, 12):
        if index % 4 == 0:
            continue  # canonical-profile anchors intentionally contain three objects
        grid = GEN.generate(19000 + index, index, difficulty="hard")
        assert max(obj["area"] for obj in _objects(grid)) == 19


@pytest.mark.parametrize("sample_index", [0, 1])
def test_default_paths_record_every_exact_axis(monkeypatch, sample_index):
    captured = {}
    real_gen_ctx = GEN.gen_ctx

    def tracking_gen_ctx(**kwargs):
        ctx = real_gen_ctx(**kwargs)
        captured["ctx"] = ctx
        return ctx

    monkeypatch.setattr(GEN, "gen_ctx", tracking_gen_ctx)
    grid = GEN.generate(23311, sample_index, difficulty="medium")
    draws = captured["ctx"].recorded_draws()
    observed = GEN.observe_overrides(grid)
    assert set(GEN.AXES) <= set(draws)
    assert draws["grid_h"] == observed["grid_h"]
    assert draws["grid_w"] == observed["grid_w"]
    assert draws["n_objects"] == observed["n_objects"]
    assert sorted(draws["hole_counts"]) == observed["hole_counts"]
