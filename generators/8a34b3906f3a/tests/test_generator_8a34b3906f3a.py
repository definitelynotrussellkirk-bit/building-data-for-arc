"""Focused regressions for the repaired rotational-completion base generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK_ID = "8a34b3906f3a"
_PATH = Path(__file__).resolve().parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("_generator_8a34b3906f3a_under_test", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _complete(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    center = len(grid) // 2
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            rr, cc = r, c
            for _ in range(3):
                dr, dc = rr - center, cc - center
                rr, cc = center + dc, center - dr
                out[rr][cc] = 2
    return out


def _canonical_record():
    return Catalog(".").get(TASK_ID)["variants"][0]


def test_rule_pin_and_original_pairs_match_the_repaired_grammar():
    record = _canonical_record()
    expected = hashlib.sha256(
        " ".join(record["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected
    pairs = record["train"] + record["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert _complete(pair["input"]) == pair["output"]
        scene = GEN.analyze_scene(pair["input"])
        assert scene["size"] in (9, 11)
        assert scene["missing_quadrant"] in range(4)
        assert scene["incomplete_orbits"] >= 1
        assert scene["palette"] == [0, 2, 9]


def test_ordinary_draws_are_odd_square_marker_anchored_and_nonclipping():
    seen_missing = set()
    seen_sizes = set()
    for band in (None, "easy", "medium", "hard"):
        for seed in range(32):
            grid = GEN.generate(seed, seed * 7 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            scene = GEN.analyze_scene(grid)
            seen_missing.add(scene["missing_quadrant"])
            seen_sizes.add(scene["size"])
            assert len(grid) == len(grid[0])
            assert len(grid) % 2 == 1
            assert grid[len(grid) // 2][len(grid) // 2] == 9
            assert {cell for row in grid for cell in row} == {0, 2, 9}
            completed = _complete(grid)
            assert completed != grid
            assert all(0 <= r < len(grid) and 0 <= c < len(grid)
                       for r, row in enumerate(completed) for c, _ in enumerate(row))
    assert seen_missing == {0, 1, 2, 3}
    assert min(seen_sizes) == 9
    assert max(seen_sizes) >= 21


def test_exact_axes_cover_minimum_maximum_boundary_and_complete_orbits():
    cases = [
        dict(grid_size=9, n_orbits=3, missing_quadrant=0,
             n_complete_orbits=0, profile="interior"),
        dict(grid_size=9, n_orbits=12, missing_quadrant=3,
             n_complete_orbits=2, profile="boundary"),
        dict(grid_size=29, n_orbits=12, missing_quadrant=2,
             n_complete_orbits=1, profile="mixed"),
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(700 + index, 900 + index, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        scene = GEN.analyze_scene(grid)
        assert scene["size"] == overrides["grid_size"]
        assert scene["orbit_count"] == overrides["n_orbits"]
        assert scene["missing_quadrant"] == overrides["missing_quadrant"]
        assert scene["complete_orbits"] == overrides["n_complete_orbits"]
        if overrides["profile"] in {"boundary", "mixed"}:
            assert scene["touches_boundary"]
        if overrides["grid_size"] == 29:
            assert scene["red_bbox_height"] >= 25
            assert scene["red_bbox_width"] >= 25


def test_invalid_calls_reject_unknown_even_and_coercive_controls():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="extreme")
    with pytest.raises((TypeError, ValueError), match="grid_size"):
        GEN.generate(1, 2, grid_size=10)
    with pytest.raises((TypeError, ValueError), match="grid_size"):
        GEN.generate(1, 2, grid_size=9.0)
    with pytest.raises((TypeError, ValueError), match="missing_quadrant"):
        GEN.generate(1, 2, missing_quadrant=True)
    with pytest.raises(ValueError, match="n_complete_orbits"):
        GEN.generate(1, 2, n_orbits=3, n_complete_orbits=3)
    with pytest.raises((TypeError, ValueError), match="profile"):
        GEN.generate(1, 2, profile=7)


def test_self_check_rejects_the_retained_audit_impostors_and_crossed_missing_sectors():
    valid = GEN.generate(
        11, 17, grid_size=11, n_orbits=4, missing_quadrant=0,
        n_complete_orbits=0, profile="interior"
    )
    even = [row[:-1] for row in valid[:-1]]
    no_marker = copy.deepcopy(valid)
    center = len(valid) // 2
    no_marker[center][center] = 0
    wrong_color = copy.deepcopy(valid)
    wrong_color[0][0] = 4
    complete = _complete(valid)
    all_red = [[2] * 9 for _ in range(9)]
    all_red[4][4] = 9

    # Fill one omitted point, then remove a different orbit member from another
    # quadrant: every orbit still has three members, but there is no common
    # missing sector.
    crossed = copy.deepcopy(valid)
    scene = GEN.analyze_scene(valid)
    first = scene["orbits"][0]
    second = scene["orbits"][1]
    crossed[first["missing"][0]][first["missing"][1]] = 2
    victim = second["present"][0]
    crossed[victim[0]][victim[1]] = 0

    for grid in (even, no_marker, wrong_color, complete, all_red, crossed):
        assert GEN.self_check(grid)
