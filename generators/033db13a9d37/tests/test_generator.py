"""Task-local regressions for the first-nonzero parity-pattern curriculum."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_SIZES,
    canonical_pairs,
    last_nonzero_rival,
    lesson_rotation_report,
    load_generator,
    nonzero_cells,
    observed_axes,
    oracle_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_exact_axis_surface_and_canonical_support():
    assert gen.RULE_HASH == "3773168d1737"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "fg_color", "scene_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 3, "grid_w": 3, "fg_color": 1, "scene_profile": "single"},
        {"grid_h": 7, "grid_w": 13, "fg_color": 6, "scene_profile": "single"},
        {"grid_h": 18, "grid_w": 18, "fg_color": 9, "scene_profile": "decoy"},
    ],
)
def test_exact_overrides_are_total_observable_and_valid_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": options}) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options
    assert oracle_output(grid) != grid
    if options["scene_profile"] == "decoy":
        assert last_nonzero_rival(grid) != oracle_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 2),
        ("grid_h", 19),
        ("grid_w", 2),
        ("grid_w", 19),
        ("fg_color", 0),
        ("fg_color", 4),
        ("fg_color", 10),
        ("scene_profile", "unknown"),
        ("grid_h", True),
        ("grid_w", 7.0),
        ("fg_color", "6"),
        ("scene_profile", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["impossible", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_anchors_canonical_profiles_and_every_rotation_refutes_last_seed(band):
    assert tuple(gen.SCHEDULE_PROFILES) == ("decoy_witness", "canonical_anchor")
    for index in range(8):
        expected = "decoy_witness" if index % 2 == 0 else "canonical_anchor"
        assert gen.schedule_profile(73, index, difficulty=band) == expected
        grid = gen.generate(73, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert (len(nonzero_cells(grid)) == 2) == (index % 2 == 0)
        if index % 2:
            expected_size = CANONICAL_SIZES[(index // 2) % len(CANONICAL_SIZES)]
            assert (len(grid), len(grid[0])) == (expected_size, expected_size)
    report = lesson_rotation_report(gen, starts=range(32), band=band)
    assert report["status"] == "pass", report["failures"][:3]


def test_declared_last_nonzero_shortcut_fits_canonical_and_generated_witness_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["last_nonzero_seed"]
    assert shortcut is gen.SEMANTIC_RIVALS["last_nonzero_seed"]
    assert shortcut is gen.LESSON_COMPETITORS["last_nonzero_seed"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = gen.generate(91, 0, scene_profile="decoy")
    assert gen.SEMANTIC_WITNESSES["later_decoy"](grid)
    assert gen.WITNESS_RIVALS == {"later_decoy": ["last_nonzero_seed"]}
    assert shortcut(grid) == last_nonzero_rival(grid)
    assert shortcut(grid) != oracle_output(grid)


def test_lesson_identifiable_names_a_surviving_shortcut_and_accepts_a_witness():
    single = gen.generate(51, 1, scene_profile="single")
    decoy = gen.generate(51, 0, scene_profile="decoy")
    single_pair = {"input": single, "output": oracle_output(single)}
    decoy_pair = {"input": decoy, "output": oracle_output(decoy)}
    query = {"input": gen.generate(51, 3), "output": oracle_output(gen.generate(51, 3))}
    reasons = gen.lesson_identifiable([single_pair] * 3, query)
    assert any("last_nonzero_seed" in reason for reason in reasons)
    assert gen.lesson_identifiable([single_pair, decoy_pair, single_pair], query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0, 0], [0, 0]],
        [[False, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0] * 3 for _ in range(3)],
        [[1] * 3 for _ in range(3)],
        [[0, 4, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [0, 1, 0]],
        [[0, 1, 2], [0, 0, 0], [0, 3, 0]],
        [[0, 10, 0], [0, 0, 0], [0, 0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_out_of_manifold_inputs(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_deterministic_valid_and_diverse(band):
    signatures = set()
    positions = set()
    for index in range(96):
        grid = gen.generate(3100 + index, index, difficulty=band)
        assert grid == gen.generate(3100 + index, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        cells = nonzero_cells(grid)
        signatures.add((len(grid), len(grid[0]), cells[0][2], len(cells)))
        positions.add((cells[0][0], cells[0][1]))
        assert oracle_output(grid) != grid
    assert len(signatures) >= 24
    assert len(positions) >= 12


def test_oracle_and_rival_do_not_mutate_inputs():
    grid = gen.generate(29, 0, scene_profile="decoy")
    original = deepcopy(grid)
    oracle_output(grid)
    last_nonzero_rival(grid)
    assert grid == original
