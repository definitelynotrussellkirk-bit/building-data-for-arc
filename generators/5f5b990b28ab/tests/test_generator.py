"""Task-local regressions for bbox-area frame ranking semantics."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    components,
    load_generator,
    observed_profile,
    oracle_output,
    perimeter_order_rival,
    racket_outputs,
    scan_order_rival,
    width_order_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_canonical_contract():
    assert gen.RULE_HASH == "d23e43212061"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)
    assert all(oracle_output(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile",
    [
        "canonical_nested3",
        "nested2",
        "nested4",
        "area_stress3",
        "area_stress4",
    ],
)
def test_scene_profile_override_is_exact_and_observable(profile, band):
    grid = gen.generate(31, 7, difficulty=band, scene_profile=profile)
    assert gen.self_check(grid) == []
    assert observed_profile(grid) == profile
    assert gen.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("scene_profile", "single_frame"),
        ("scene_profile", 3),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_default_schedule_repeats_decisive_stress_roles():
    expected = {
        "canonical_nested3",
        "nested2",
        "area_stress3",
        "area_stress4",
    }
    for start in range(12):
        profiles = [gen.schedule_profile(99, start + step, "medium") for step in range(5)]
        assert expected <= set(profiles)
        assert sum(name.startswith("area_stress") for name in profiles) >= 2


@pytest.mark.parametrize("profile", ["area_stress3", "area_stress4"])
def test_area_stress_is_a_counterexample_to_plausible_canonical_shortcuts(profile):
    for sample_index in range(16):
        grid = gen.generate(800 + sample_index, sample_index, scene_profile=profile)
        expected = oracle_output(grid)
        assert scan_order_rival(grid) != expected
        assert perimeter_order_rival(grid) != expected
        assert width_order_rival(grid) != expected
        assert gen.SEMANTIC_WITNESSES["bbox_area_not_scan_order"](grid)
        assert gen.SEMANTIC_WITNESSES["bbox_area_not_perimeter"](grid)
        assert gen.SEMANTIC_WITNESSES["bbox_area_not_width"](grid)


def test_every_five_pair_rotation_remains_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for step in range(5):
                grid = gen.generate(9_000 + start, start + step, difficulty=band)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_distribution_is_deterministic_and_materially_diverse():
    grids = []
    profiles = set()
    shapes = set()
    for index in range(160):
        grid = gen.generate(1_000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert grid == gen.generate(
            1_000 + index,
            index,
            difficulty=("easy", "medium", "hard")[index % 3],
        )
        assert gen.self_check(grid) == []
        grids.append(grid)
        profiles.add(observed_profile(grid))
        shapes.add((len(grid), len(grid[0])))
    assert len({repr(grid) for grid in grids}) >= 150
    assert profiles == set(gen.SCENE_PROFILES)
    assert len(shapes) >= 12


@pytest.mark.parametrize(
    "mutation",
    ["foreign_colour", "merge_components", "erase_edge", "duplicate_area", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = deepcopy(gen.generate(44, 3, scene_profile="area_stress4"))
    if mutation == "foreign_colour":
        grid[0][0] = 1
    elif mutation == "merge_components":
        objects = components(grid)
        left, right = min(
            ((a, b) for i, a in enumerate(objects) for b in objects[i + 1 :]),
            key=lambda pair: min(
                abs(r1 - r2) + abs(c1 - c2)
                for r1, c1 in pair[0]
                for r2, c2 in pair[1]
            ),
        )
        start, end = min(
            ((a, b) for a in left for b in right),
            key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
        )
        row, col = start
        while row != end[0]:
            row += 1 if end[0] > row else -1
            grid[row][col] = 8
        while col != end[1]:
            col += 1 if end[1] > col else -1
            grid[row][col] = 8
    elif mutation == "erase_edge":
        for row, values in enumerate(grid):
            try:
                col = values.index(8)
            except ValueError:
                continue
            grid[row][col] = 0
            break
    elif mutation == "duplicate_area":
        # A broad semantic mutation: replace the valid scene with two equal 3x3 frames.
        grid = [[0] * 13 for _ in range(13)]
        for r0, c0 in ((1, 1), (7, 7)):
            for col in range(c0, c0 + 3):
                grid[r0][col] = grid[r0 + 2][col] = 8
            for row in range(r0, r0 + 3):
                grid[row][c0] = grid[row][c0 + 2] = 8
    elif mutation == "ragged":
        grid[-1].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 8]], [[True] * 13 for _ in range(13)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_generator_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(500, index) for index in range(20))
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]
