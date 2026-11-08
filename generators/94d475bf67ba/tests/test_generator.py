"""Focused regressions for the repaired nested-frame ownership sampler."""
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
from reference_probe import (  # noqa: E402
    canonical_pairs,
    expected_output,
    frame_specs,
    load_generator,
    maximum_color_output,
    observed_axes,
    outermost_output,
    racket_outputs,
    two_levels_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_RULE_HASH = "beb1b900ffc7"
EXPECTED_PROFILES = (
    (11, 11, 2),
    (12, 12, 3),
    (10, 13, 2),
    (12, 14, 3),
)


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}"
)
def test_canonical_pairs_are_in_grammar_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert expected_output(pair["input"]) == pair["output"]


def test_rule_identity_and_advertised_axes_are_exact():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_frames"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 10, "grid_w": 10, "n_frames": 2},
        {"grid_h": 10, "grid_w": 10, "n_frames": 3},
        {"grid_h": 18, "grid_w": 18, "n_frames": 2},
        {"grid_h": 18, "grid_w": 18, "n_frames": 3},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(194, 7, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 19),
        ("grid_w", 9),
        ("grid_w", 19),
        ("n_frames", 1),
        ("n_frames", 4),
        ("grid_h", True),
        ("grid_w", 12.0),
        ("n_frames", "3"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_four_slot_schedule_has_exact_profiles_and_deep_three_frame_controls(band):
    for index in range(16):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(700 + index, index, difficulty=band)
        assert tuple(observed_axes(grid).values()) == EXPECTED_PROFILES[index % 4]
        operative = frame_specs(grid, operative_only=True)
        assert len(operative) == (3 if index % 2 else 2)
        assert expected_output(grid) != grid
        assert expected_output(grid) != outermost_output(grid)
        if index % 2:
            assert expected_output(grid) != two_levels_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_sliding_four_demo_window_and_query_rotation_refutes_all_rivals(band):
    for start in range(4):
        pairs = []
        for index in range(start, start + 5):
            grid = gen.generate(8123, index, difficulty=band)
            pairs.append({"input": grid, "output": expected_output(grid)})
        for query_index in range(5):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_two_level_shortcut_fits_every_canonical_pair_but_generated_depth_refutes_it():
    pairs = canonical_pairs()
    assert all(two_levels_output(pair["input"]) == pair["output"] for pair in pairs)
    for index in (1, 3):
        grid = gen.generate(91, index)
        assert expected_output(grid) != two_levels_output(grid)
        assert gen.SEMANTIC_WITNESSES["third_operative_frame"](grid)
        assert gen.SEMANTIC_RIVALS["two_levels_only"](grid) == two_levels_output(grid)


def test_numeric_color_is_not_a_semantic_role_in_each_schedule_cycle():
    disagreements = []
    for index in range(4):
        grid = gen.generate(188, index)
        disagreements.append(expected_output(grid) != maximum_color_output(grid))
        assert gen.SEMANTIC_RIVALS["maximum_color_owner"](grid) == maximum_color_output(grid)
    assert sum(disagreements) >= 2


@pytest.mark.parametrize(
    "mutation",
    ["erase_border", "extra_component", "extra_color", "break_nesting"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 1)
    frames = frame_specs(grid)
    if mutation == "erase_border":
        top, left, _, _ = frames[0]["box"]
        grid[top][left] = 0
    elif mutation == "extra_component":
        color = frames[-1]["color"]
        existing = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        candidates = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0
            and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in existing)
        ]
        r, c = candidates[0]
        grid[r][c] = color
    elif mutation == "extra_color":
        grid[0][0] = next(color for color in range(1, 10) if color not in {f["color"] for f in frames})
    elif mutation == "break_nesting":
        inner = frames[-1]
        top, left, bottom, right = inner["box"]
        color = inner["color"]
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if grid[r][c] == color:
                    grid[r][c] = 0
        # Recreate an exact frame outside the outer frame.
        for c in range(0, 3):
            grid[0][c] = color
            grid[2][c] = color
        for r in range(0, 3):
            grid[r][0] = color
            grid[r][2] = color
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_validator_and_oracle_do_not_mutate_inputs():
    grid = gen.generate(19, 3)
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert expected_output(grid) != grid
    assert grid == original


def test_default_distribution_varies_layouts_and_palette_roles():
    layouts = set()
    palettes = set()
    for seed in range(80):
        grid = gen.generate(5000 + seed, seed % 4)
        layouts.add(tuple(item["box"] for item in frame_specs(grid)))
        palettes.add(tuple(item["color"] for item in frame_specs(grid)))
    assert len(layouts) >= 12
    assert len(palettes) >= 30


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,3,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_reference_matches_canonical_and_generated_grids_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(319 + index, index) for index in range(16))
    assert racket_outputs(grids) == [expected_output(grid) for grid in grids]
