"""Regression and semantic-contract tests for task 058ae70e4bdb."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "058ae70e4bdb"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _regions(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 8 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in DIR4:
                    rr, cc = row + drow, col + dcol
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 8
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            colors = Counter(
                grid[row][col]
                for row, col in cells
                if grid[row][col] not in (0, 8)
            )
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            rectangular = len(cells) == (
                (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
            )
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": colors,
                    "marker_count": sum(colors.values()),
                    "zeros": sum(grid[row][col] == 0 for row, col in cells),
                    "rectangular": rectangular,
                }
            )
    return result


def _oracle(grid):
    output = deepcopy(grid)
    for region in _regions(grid):
        if len(region["colors"]) == 1:
            color = next(iter(region["colors"]))
            for row, col in region["cells"]:
                output[row][col] = color
    return output


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": grid, "output": _oracle(grid)}


def test_rule_hash_and_all_canonical_pairs_are_bound_to_the_independent_oracle():
    assert GEN.RULE_HASH == "f3ddcec3d159"
    assert GEN.MIN_STRICT_FRAC == 1.0
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert _oracle(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_default_schedule_is_a_three_profile_semantic_cycle():
    expected = (
        "same_color_pair",
        "merged_two_color",
        "merged_single_color",
    )
    assert tuple(GEN.SCHEDULE_PROFILES) == expected
    for index in range(30):
        assert GEN.schedule_profile(991, index, "hard") == expected[index % 3]
        grid = GEN.generate(991, index, difficulty="hard")
        assert GEN.observe_overrides(grid) == {"scene_profile": expected[index % 3]}


@pytest.mark.parametrize("profile", [
    "canonical_mix",
    "all_fill",
    "same_color_pair",
    "two_color_stay",
    "merged_single_color",
    "merged_two_color",
])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_scene_profile_override_is_exact_observable_and_nonidentity(profile, band):
    grid = GEN.generate(1201, 73, difficulty=band, scene_profile=profile)
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}
    assert GEN.self_check(grid, difficulty=band, meta={"scene_profile": profile}) == []
    assert GEN.strict_canonical_like(grid) == []
    assert _oracle(grid) != grid
    assert GEN.rule_mirror(grid) == _oracle(grid)
    assert grid == GEN.generate(1201, 73, difficulty=band, scene_profile=profile)


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, texture="plain")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, scene_profile="no_walls")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, scene_profile=3)


def test_profile_witnesses_have_the_claimed_geometry_and_palettes():
    grids = {
        profile: GEN.generate(707, 11, difficulty="medium", scene_profile=profile)
        for profile in GEN.SCENE_PROFILES
    }
    info = {name: _regions(grid) for name, grid in grids.items()}

    canonical = info["canonical_mix"]
    assert all(region["rectangular"] for region in canonical)
    assert any(not region["colors"] for region in canonical)
    assert all(region["marker_count"] <= 1 for region in canonical)

    all_fill = info["all_fill"]
    assert all(region["rectangular"] for region in all_fill)
    assert all(len(region["colors"]) == 1 for region in all_fill)
    assert all(region["marker_count"] == 1 for region in all_fill)

    pair = info["same_color_pair"]
    assert all(region["rectangular"] for region in pair)
    assert any(len(region["colors"]) == 1 and region["marker_count"] == 2 for region in pair)

    two = info["two_color_stay"]
    assert all(region["rectangular"] for region in two)
    assert any(len(region["colors"]) == 2 for region in two)

    merged_single = info["merged_single_color"]
    assert sum(not region["rectangular"] for region in merged_single) == 1
    assert any(not region["rectangular"] and len(region["colors"]) == 1 for region in merged_single)

    merged_two = info["merged_two_color"]
    assert sum(not region["rectangular"] for region in merged_two) == 1
    assert any(not region["rectangular"] and len(region["colors"]) == 2 for region in merged_two)

    for profile, grid in grids.items():
        assert all(predicate(grid) for predicate in GEN.PROFILE_WITNESSES[profile].values())


def test_default_distribution_is_strict_diverse_replayable_and_never_identity():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        unique = set()
        profiles = Counter()
        palettes = set()
        for index in range(120):
            seed = 50_000 + 10_000 * band_index + index
            grid = GEN.generate(seed, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.rule_mirror(grid) == _oracle(grid)
            assert _oracle(grid) != grid
            assert grid == GEN.generate(seed, index, difficulty=band)
            unique.add(_frozen(grid))
            profiles[GEN.observe_overrides(grid)["scene_profile"]] += 1
            palettes.add(len({value for row in grid for value in row}))
        assert len(unique) == 120
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
        assert palettes == {5, 6}


def test_every_band_hits_all_five_exact_canonical_dimension_palette_profiles():
    expected = {
        (9, 11, 5),
        (9, 13, 5),
        (10, 12, 5),
        (10, 14, 5),
        (11, 11, 6),
    }
    for band in ("easy", "medium", "hard"):
        observed = set()
        for index in range(20):
            grid = GEN.generate(700_000 + index, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            if profile in expected:
                observed.add(profile)
        assert observed == expected


def test_every_consecutive_three_demo_window_refutes_all_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(9):
                pairs = [
                    _pair(GEN.generate(10_000 + seed, index, difficulty=band))
                    for index in range(start, start + 4)
                ]
                demos, query = pairs[:3], pairs[3]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"]
                        for pair in demos
                    ), name


def test_named_witnesses_and_rivals_are_real_counterexamples():
    grids = [GEN.generate(8800, index, difficulty="medium") for index in range(3)]
    official = [GEN.rule_mirror(grid) for grid in grids]
    assert all(any(predicate(grid) for grid in grids) for predicate in GEN.SEMANTIC_WITNESSES.values())
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != output for grid, output in zip(grids, official)), name


def test_self_check_rejects_structural_impostors_and_identity_lessons():
    valid = GEN.generate(404, 7, scene_profile="same_color_pair")

    ragged = deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in error for error in GEN.self_check(ragged))

    open_border = deepcopy(valid)
    open_border[0][1] = 0
    assert any("border" in error for error in GEN.self_check(open_border))

    no_seeds = [[0 if value != 8 else 8 for value in row] for row in valid]
    assert GEN.self_check(no_seeds)

    three_colors = deepcopy(valid)
    region = next(region for region in _regions(three_colors) if region["zeros"] >= 3)
    for (row, col), color in zip(region["cells"][:3], (1, 2, 3)):
        three_colors[row][col] = color
    assert any("two distinct" in error for error in GEN.self_check(three_colors))

    too_many_markers = deepcopy(valid)
    region = next(region for region in _regions(too_many_markers) if region["zeros"] >= 3)
    color = next(iter(_regions(too_many_markers)[0]["colors"]), 1)
    for row, col in region["cells"][:3]:
        too_many_markers[row][col] = color
    assert any("two marker" in error for error in GEN.self_check(too_many_markers))


def test_real_racket_rule_matches_independent_oracle_when_available():
    try:
        from arc_repl.racket_bridge import racket_runtime_status
        from arcpuzzles import Catalog
    except ImportError as exc:
        pytest.skip(str(exc))
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])

    grids = [pair["input"] for pair in canonical_pairs(TASK_ID, root=find_root(__file__))]
    grids += [GEN.generate(8300, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(18)]
    result = Catalog().apply(TASK_ID, grids, timeout=180)
    assert result["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in result["results"])
    assert [item["output"] for item in result["results"]] == [_oracle(grid) for grid in grids]


def test_workspace_deep_audit_is_source_bound_and_checks_actual_declarations():
    tool_path = HOME / "workspace" / "deep_audit.py"
    spec = importlib.util.spec_from_file_location("deep_audit_under_test", tool_path)
    assert spec and spec.loader
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    report = tool.audit(samples_per_profile=2, schedule_starts=6)
    assert report["status"] == "pass", report["failures"][:3]
    assert report["generator_sha256"] == tool.sha256_file(HOME / "generator.py")
    assert report["profiles_checked"] == len(GEN.SCENE_PROFILES) * 3 * 2
    assert report["lesson_rotations_checked"] == 3 * 6 * 4
    assert report["competitors"] == sorted(GEN.LESSON_COMPETITORS)
