"""Task-local regression tests for 4a279b104523."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    above_only_rival,
    canonical_pairs,
    geometry_output,
    grid_center_rival,
    load_generator,
    observed,
    pinned_profile_seed,
    racket_outputs,
    rule_hash,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == rule_hash()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_every_canonical_input_and_geometry(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_canonical_out_of_bounds_reflection_is_clipped_not_rejected():
    pair = canonical_pairs()[1]
    grid = deepcopy(pair["input"])
    axis = observed(grid)["axis_row"]
    clipped = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8) and not 0 <= 2 * axis - r < len(grid)
    ]
    assert clipped == [(5, 4, 5)]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.rule_mirror(grid) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("side", ["above", "below", "both"])
def test_exact_overrides_are_observable_in_every_band(band, side):
    requested = {"grid_h": 5, "grid_w": 4, "n_cells": 8, "source_side": side}
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    got = gen.observe_overrides(grid)
    for key, value in requested.items():
        assert got[key] == value
        assert observed(grid)[key] == value


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4),
        ("grid_h", 15),
        ("grid_w", 3),
        ("grid_w", 12),
        ("n_cells", 1),
        ("n_cells", 9),
        ("source_side", "left"),
        ("grid_h", True),
        ("grid_w", "5"),
        ("n_cells", 2.0),
        ("source_side", 1),
    ],
)
def test_rejects_unknown_invalid_and_coerced_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_covers_both_directions_and_off_center_axes(band):
    sides = set()
    off_center = 0
    shapes = set()
    palettes = set()
    hashes = set()
    for index in range(256):
        grid = gen.generate(2100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
        obs = observed(grid)
        sides.add(obs["source_side"])
        off_center += bool(obs["off_center_axis"])
        shapes.add((obs["grid_h"], obs["grid_w"]))
        palettes.add(obs["n_content_colors"])
        hashes.add(json.dumps(grid, separators=(",", ":")))
        assert geometry_output(grid) != grid
    assert sides == {"above", "below", "both"}
    assert off_center >= 32
    assert len(shapes) >= 20
    assert {1, 2, 3} <= palettes
    assert len(hashes) == 256


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_official_20_draw_profile_schedule_has_an_exact_hit_per_band(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    profiles = set()
    for index in range(20):
        seed = pinned_profile_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert profiles & canonical_profiles


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_official_profile_schedule_has_at_least_25_percent_envelope_support(band):
    hits = 0
    for index in range(20):
        seed = pinned_profile_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += (5 <= profile[0] <= 7 and 5 <= profile[1] <= 6 and profile[2] == 4)
    assert hits >= 5


def test_declared_semantic_witnesses_refute_real_shortcuts():
    below = gen.generate(71, 3, grid_h=6, grid_w=6, n_cells=4, source_side="below")
    assert gen.SEMANTIC_WITNESSES["below_source"](below)
    assert gen.SEMANTIC_RIVALS["above_only"](below) == above_only_rival(below)
    assert gen.SEMANTIC_RIVALS["above_only"](below) != geometry_output(below)

    off_center = None
    for index in range(64):
        candidate = gen.generate(99, index, grid_h=6, grid_w=6, n_cells=4, source_side="both")
        if observed(candidate)["off_center_axis"]:
            off_center = candidate
            break
    assert off_center is not None
    assert gen.SEMANTIC_WITNESSES["off_center_axis"](off_center)
    assert gen.SEMANTIC_RIVALS["grid_center"](off_center) == grid_center_rival(off_center)
    assert gen.SEMANTIC_RIVALS["grid_center"](off_center) != geometry_output(off_center)


def test_generated_sources_have_empty_mirror_targets():
    for side in ("above", "below", "both"):
        for index in range(64):
            grid = gen.generate(900 + index, index, source_side=side, n_cells=8)
            obs = observed(grid)
            axis = obs["axis_row"]
            for r, c, _ in [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)]:
                rr = 2 * axis - r
                assert 0 <= rr < len(grid)
                assert grid[rr][c] == 0


@pytest.mark.parametrize(
    "mutation",
    ["erase_axis", "second_axis", "bad_color", "stray_eight", "conflicting_pair", "too_few_cells"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2, grid_h=6, grid_w=5, n_cells=4, source_side="above")
    axis = observed(grid)["axis_row"]
    if mutation == "erase_axis":
        grid[axis][0] = 0
    elif mutation == "second_axis":
        row = 0 if axis != 0 else len(grid) - 1
        grid[row] = [8] * len(grid[0])
    elif mutation == "bad_color":
        grid[0][0] = True
    elif mutation == "stray_eight":
        target_row = 0 if axis != 0 else len(grid) - 1
        grid[target_row][0] = 8
    elif mutation == "conflicting_pair":
        r, c, value = next((r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8))
        grid[2 * axis - r][c] = 1 if value != 1 else 2
    elif mutation == "too_few_cells":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value not in (0, 8):
                    grid[r][c] = 0
        grid[max(0, axis - 1)][0] = 3
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator(sys.argv[2]).generate(31,8,difficulty='hard')))"
    )
    results = []
    for seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace"), str(Path(gen.__file__).resolve())],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(319, index, source_side=("above", "below", "both")[index % 3])
        for index in range(24)
    ]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]


def _lesson_pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(9))
def test_every_three_demo_schedule_refutes_declared_rivals(band, start):
    """Every real runner window must identify the rule before seeing the query."""
    seed = 800_000 + start
    grids = [
        gen.generate(seed, start + offset, difficulty=band)
        for offset in range(gen.EXAMPLES_NEEDED + 1)
    ]
    expected_sides = [
        gen.SCHEDULE_PROFILES[(start + offset) % len(gen.SCHEDULE_PROFILES)]
        for offset in range(gen.EXAMPLES_NEEDED + 1)
    ]
    assert [gen.observe_overrides(grid)["source_side"] for grid in grids] == expected_sides
    assert any(observed(grid)["off_center_axis"] for grid in grids[: gen.EXAMPLES_NEEDED])

    pairs = [_lesson_pair(grid) for grid in grids]
    assert gen.lesson_identifiable(
        pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
    ) == []


def test_regression_for_census_grid_center_ambiguity():
    """The exact lesson that exposed the center-axis shortcut is now identifiable."""
    seed = 2_317_293_193
    start = 39
    pairs = [
        _lesson_pair(gen.generate(seed, start + offset, difficulty="medium"))
        for offset in range(gen.EXAMPLES_NEEDED + 1)
    ]
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
