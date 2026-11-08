"""Task-local regression tests for 1bc816e1eb99.

The geometry oracle and rivals live in workspace/reference_probe.py and do not
call generator implementation helpers.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    component_stats,
    intended_output,
    load_generator,
    observed,
    rival_area_threshold,
    rival_bbox_not_full,
    rival_large_bbox,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PAIRS = canonical_pairs()


def test_authority_pin_and_minimal_observable_contract():
    assert gen.RULE_HASH == "0c3f64fb33c3"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_components"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


@pytest.mark.parametrize("bad_seed", [True, 1.5, "1"])
def test_public_entry_points_reject_non_integer_seed(bad_seed):
    for call in (
        lambda: gen.generate(bad_seed, 0),
        lambda: gen.schedule_profile(bad_seed, 0),
    ):
        with pytest.raises(TypeError, match="seed must be an integer"):
            call()


@pytest.mark.parametrize("bad_index", [True, 1.5, "1"])
def test_public_entry_points_reject_non_integer_sample_index(bad_index):
    for call in (
        lambda: gen.generate(0, bad_index),
        lambda: gen.schedule_profile(0, bad_index),
    ):
        with pytest.raises(TypeError, match="sample_index must be an integer"):
            call()


def test_public_entry_points_reject_negative_sample_index():
    for call in (
        lambda: gen.generate(0, -1),
        lambda: gen.schedule_profile(0, -1),
    ):
        with pytest.raises(ValueError, match="sample_index must be nonnegative"):
            call()


@pytest.mark.parametrize(
    "pair",
    CANONICAL_PAIRS,
    ids=[f"{len(pair['input'])}x{len(pair['input'][0])}-{i}" for i, pair in enumerate(CANONICAL_PAIRS)],
)
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_axes_are_realized_in_every_band(band):
    options = {"grid_h": 15, "grid_w": 18, "n_components": 4}
    grid = gen.generate(71, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 10}, {"grid_h": 16}, {"grid_w": 11}, {"grid_w": 19},
        {"n_components": 1}, {"n_components": 5}, {"grid_h": True},
        {"grid_w": 12.5}, {"n_components": "3"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_linked_profiles_produce_real_counterexamples(band):
    grids = [gen.generate(910, index, difficulty=band) for index in range(4)]
    profiles = [gen.schedule_profile(910, index, band) for index in range(4)]
    assert set(profiles) == set(gen.SCHEDULE_PROFILES)
    by_profile = dict(zip(profiles, grids))

    canonical = by_profile["canonical"]
    assert gen.strict_canonical_like(canonical) == []

    size_witness = by_profile["small_frame_large_solid"]
    assert gen.SEMANTIC_WITNESSES["small_frame_large_solid"](size_witness)
    assert rival_large_bbox(size_witness) != intended_output(size_witness)

    concave = by_profile["concave_zero_hole"]
    assert gen.SEMANTIC_WITNESSES["concave_zero_hole"](concave)
    assert rival_bbox_not_full(concave) != intended_output(concave)

    same_area = by_profile["same_area_opposite_topology"]
    assert gen.SEMANTIC_WITNESSES["same_area_opposite_topology"](same_area)
    assert rival_area_threshold(same_area) != intended_output(same_area)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_four_example_window_is_identifiable(band):
    for start in range(4):
        pairs = []
        for offset in range(5):
            grid = gen.generate(2001, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_declared_canonical_shortcuts_really_fit_public_pairs_and_are_refuted():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
    for index in range(4):
        grid = gen.generate(3009, index)
        truth = intended_output(grid)
        if gen.schedule_profile(3009, index) != "canonical":
            assert any(rival(grid) != truth for rival in gen.CANONICAL_SHORTCUTS.values())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_valid_and_varied(band):
    unique = set()
    edge_cases = 0
    branch_cases = 0
    for index in range(128):
        grid = gen.generate(5000 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(5000 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert intended_output(grid) != grid
        stats = component_stats(grid)
        edge_cases += any(stat["touches_edge"] for stat in stats)
        branch_cases += {stat["holes"] for stat in stats} >= {0, 1}
        unique.add(tuple(tuple(row) for row in grid))
    assert len(unique) >= 110
    assert edge_cases >= 20
    assert branch_cases >= 50


def test_validator_rejects_malformed_and_structural_impostors():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(11)]]
    for grid in malformed:
        assert gen.self_check(grid)

    foreign = [[0] * 12 for _ in range(11)]
    foreign[0][0] = 6
    foreign[2][2] = foreign[2][3] = foreign[3][2] = foreign[3][3] = 4
    assert gen.self_check(foreign)

    one_component = [[0] * 12 for _ in range(11)]
    for r in range(2, 4):
        for c in range(2, 5):
            one_component[r][c] = 4
    assert gen.self_check(one_component)

    two_holes = [[0] * 12 for _ in range(11)]
    pattern = [
        [1, 1, 1, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    for rr, row in enumerate(pattern):
        for cc, value in enumerate(row):
            if value:
                two_holes[1 + rr][1 + cc] = 4
    for r in range(7, 9):
        for c in range(8, 10):
            two_holes[r][c] = 4
    assert gen.self_check(two_holes)
