"""Source-bound regression and semantic tests for f151fbd31cb2."""
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
    larger_total_area_rival,
    load_generator,
    majority_objects_rival,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_inputs_are_accepted_and_python_mirror_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]


def test_declared_shortcuts_really_fit_every_canonical_pair():
    pairs = canonical_pairs()
    for name, rival in {
        "majority_objects": majority_objects_rival,
        "larger_total_area": larger_total_area_rival,
    }.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert name in gen.CANONICAL_SHORTCUTS
        assert name in gen.LESSON_COMPETITORS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 9, "grid_w": 11, "shape_key": 1, "color_key": 8, "n_l": 1, "n_plus": 2},
        {"grid_h": 18, "grid_w": 20, "shape_key": 4, "color_key": 2, "n_l": 2, "n_plus": 1},
        {"grid_h": 9, "grid_w": 11, "shape_key": 4, "color_key": 6, "n_l": 2, "n_plus": 2},
    ],
)
def test_every_exact_override_is_observable_in_every_band(band, options):
    grid = gen.generate(31415, 7, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(31415, 7, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_h", 19),
        ("grid_w", 10),
        ("grid_w", 21),
        ("shape_key", 2),
        ("color_key", 4),
        ("n_l", 0),
        ("n_l", 3),
        ("n_plus", 0),
        ("n_plus", 3),
        ("grid_h", True),
        ("color_key", "8"),
        ("n_l", 1.0),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad_difficulty", ["expert", 0.5, 1, True])
def test_invalid_difficulty_is_rejected(bad_difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=bad_difficulty)


def test_three_slot_schedule_refutes_both_canonical_shortcuts_in_every_window():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_majority",
        "selected_minority",
        "balanced",
    )
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 31415):
            for start in range(3):
                grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(3)]
                assert {gen.schedule_profile(seed, start + offset, band) for offset in range(3)} == set(gen.SCHEDULE_PROFILES)
                assert all(gen.self_check(grid) == [] for grid in grids)
                assert any(majority_objects_rival(grid) != rule_output(grid) for grid in grids)
                assert any(larger_total_area_rival(grid) != rule_output(grid) for grid in grids)


def test_selected_minority_profile_is_an_exact_counterexample():
    for shape_key in (1, 4):
        grid = gen.generate(73, 1, shape_key=shape_key, color_key=6)
        facts = observed(grid)
        assert facts["n_l"] == (1 if shape_key == 1 else 2)
        assert facts["n_plus"] == (1 if shape_key == 4 else 2)
        intended = rule_output(grid)
        assert majority_objects_rival(grid) != intended
        assert larger_total_area_rival(grid) != intended
        assert gen.SEMANTIC_WITNESSES["selected_family_is_minority"](grid)


def test_default_schedule_keeps_canonical_size_support_in_every_band():
    canonical_profiles = {(9, 11), (10, 12), (11, 12)}
    for band in ("easy", "medium", "hard"):
        sizes = {
            (len(gen.generate(100 + index, index, difficulty=band)), len(gen.generate(100 + index, index, difficulty=band)[0]))
            for index in range(12)
        }
        assert sizes & canonical_profiles


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_valid_diverse_and_input_pure(band):
    seen = set()
    orientations = set()
    for index in range(120):
        grid = gen.generate(900 + index, index, difficulty=band)
        original = deepcopy(grid)
        assert gen.self_check(grid) == []
        out = rule_output(grid)
        assert grid == original
        assert out != grid
        facts = observed(grid)
        seen.add((facts["grid_h"], facts["grid_w"], facts["shape_key"], facts["color_key"], facts["n_l"], facts["n_plus"]))
        # Normalized L shapes are indirectly validated by self_check; capture
        # the source bytes' broad output diversity here rather than internals.
        orientations.add(str(grid))
    assert len(seen) >= 20
    assert len(orientations) >= 100


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(9)], [[9] * 11 for _ in range(9)]],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_python_mirror_matches_real_racket_on_canonical_and_generated_inputs():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(2026, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(36))
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
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
