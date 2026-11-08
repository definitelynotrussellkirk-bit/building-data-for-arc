"""Focused regressions for the concentric corner-ring generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import statistics
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5a01897eb8be"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    component_count,
    component_sizes,
    intended_output,
    load_generator,
    observed,
    rival_scan_order,
    rival_solid_rings,
    scan_order_is_size_order,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def test_rule_pin_and_small_exact_axis_contract():
    assert gen.RULE_HASH == "00935b1c1bf9"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "shape_count",
        "has_center",
        "background",
        "loose_shape",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _pairs())
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {
            "grid_h": 13,
            "grid_w": 17,
            "shape_count": 3,
            "has_center": False,
            "background": 4,
            "loose_shape": False,
        },
        {
            "grid_h": 18,
            "grid_w": 18,
            "shape_count": 6,
            "has_center": True,
            "background": 8,
            "loose_shape": True,
        },
        {
            "grid_h": 24,
            "grid_w": 24,
            "shape_count": 6,
            "has_center": False,
            "background": 0,
            "loose_shape": False,
        },
    ],
)
def test_every_exact_override_is_honored_and_observable(band, options):
    grid = gen.generate(171, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 12},
        {"grid_w": 16},
        {"shape_count": 2},
        {"shape_count": 7},
        {"background": -1},
        {"background": 10},
        {"grid_h": True},
        {"shape_count": 3.0},
        {"background": "4"},
        {"has_center": 1},
        {"loose_shape": "false"},
    ],
)
def test_invalid_and_unknown_overrides_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("bad_seed,bad_index", [(True, 0), (1.5, 0), (0, True), (0, -1)])
def test_seed_and_sample_index_are_strict(bad_seed, bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, bad_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_hits_all_canonical_profiles_and_semantic_branches(band):
    profiles = set()
    scheduled = set()
    backgrounds = set()
    for index in range(24):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        stats = observed(grid)
        profiles.add((stats["grid_h"], stats["grid_w"], stats["shape_count"] + 1))
        scheduled.add(gen.schedule_profile(5000 + index, index, band))
        backgrounds.add(stats["background"])
    assert {(13, 17, 4), (18, 18, 5), (18, 18, 7), (19, 19, 6)} <= profiles
    assert set(gen.SCHEDULE_PROFILES) == scheduled
    assert {1, 3, 4, 8} <= backgrounds


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_draw_refutes_scan_order_and_solid_border_shortcuts(band):
    for index in range(36):
        grid = gen.generate(7000 + index, index, difficulty=band)
        expected = intended_output(grid)
        assert not scan_order_is_size_order(grid)
        assert rival_scan_order(grid) != expected
        assert rival_solid_rings(grid) != expected
        assert gen.SEMANTIC_RIVALS["scan_order"](grid) == rival_scan_order(grid)
        assert gen.SEMANTIC_RIVALS["solid_rings"](grid) == rival_solid_rings(grid)


def test_default_object_complexity_tracks_the_canonical_manifold():
    canonical_counts = [component_count(pair["input"]) for pair in _pairs()]
    generated_counts = [component_count(gen.generate(8100 + i, i)) for i in range(96)]
    assert 8 <= statistics.median(generated_counts) <= 15
    assert abs(statistics.median(generated_counts) - statistics.median(canonical_counts)) <= 3


def test_largest_connected_glyph_tracks_the_canonical_scale():
    canonical_maxima = [max(component_sizes(pair["input"])) for pair in _pairs()]
    generated_maxima = [max(component_sizes(gen.generate(8600 + i, i))) for i in range(48)]
    assert abs(statistics.median(generated_maxima) - statistics.median(canonical_maxima)) <= 1


def test_difficulty_bands_materially_change_geometry():
    for index in range(12):
        grids = [
            gen.generate(8800 + index, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({repr(grid) for grid in grids}) == 3
        assert all(gen.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_semantic_lesson_contract_is_identifiable_under_query_rotation(band):
    pairs = []
    for index in range(5):
        grid = gen.generate(9200 + index, index, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_malformed_and_unassignable_mutations():
    grid = gen.generate(77, 2)
    ragged = deepcopy(grid)
    ragged[-1].pop()
    bad_color = deepcopy(grid)
    bad_color[-1][-1] = 10
    erased = [[grid[0][0] for _ in row] for row in grid]
    too_large = [[0] * 31 for _ in range(13)]
    for changed in (ragged, bad_color, erased, too_large):
        assert gen.self_check(changed)


def test_real_racket_authority_matches_independent_oracle_on_generated_witnesses():
    from arcpuzzles import Catalog

    grids = [pair["input"] for pair in _pairs()]
    grids.extend(gen.generate(11000 + index, index, difficulty="medium") for index in range(8))
    receipt = Catalog(ROOT).apply(TASK_ID, grids, timeout=120)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        intended_output(grid) for grid in grids
    ]


def test_analysis_assigns_every_generated_shape_once():
    for index in range(64):
        details = analyze(gen.generate(13000 + index, index))
        assert len(details["assignments"]) == details["shape_count"]
        assert sorted(ring for _, ring in details["assignments"]) == details["ring_sizes"]
