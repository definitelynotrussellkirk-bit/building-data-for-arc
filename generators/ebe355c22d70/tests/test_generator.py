"""Portable regression tests for the opposite-corners-to-cropped-fill sampler."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("review_ebe355c22d70_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
ROOT = find_root(__file__)
CANONICAL_SIGNATURES = {
    (8, 9, 5, 5, "positive"),
    (10, 10, 6, 5, "negative"),
    (9, 12, 6, 6, "negative"),
}


def independent_output(grid):
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert len(points) == 2
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return [[8] * (max(cols) - min(cols) + 1) for _ in range(max(rows) - min(rows) + 1)]


def signature(grid):
    points = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )
    (r0, c0), (r1, c1) = points
    return (
        len(grid),
        len(grid[0]),
        r1 - r0 + 1,
        abs(c1 - c0) + 1,
        "positive" if c1 > c0 else "negative",
    )


def test_canonical_authority_is_pinned_and_mirrored():
    assert gen.RULE_HASH == "cd9402783d01"
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    seen = set()
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert independent_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        seen.add(signature(pair["input"]))
    assert seen == CANONICAL_SIGNATURES


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("slant", ["positive", "negative"])
def test_exact_overrides_are_observable_in_every_band(band, slant):
    grid = gen.generate(
        17,
        9,
        difficulty=band,
        grid_h=6,
        grid_w=6,
        bbox_h=3,
        bbox_w=6,
        slant=slant,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 6,
        "bbox_h": 3,
        "bbox_w": 6,
        "slant": slant,
    }


@pytest.mark.parametrize(
    "override",
    [
        {"typo": 1},
        {"grid_h": 5},
        {"grid_h": 15},
        {"grid_w": 5},
        {"grid_w": 15},
        {"bbox_h": 2},
        {"bbox_h": 7},
        {"bbox_w": 2},
        {"bbox_w": 7},
        {"slant": "diagonal"},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"grid_h": "8"},
        {"bbox_h": True},
        {"bbox_w": 4.0},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


def test_declared_output_codomain_is_exact_and_default_schedule_covers_it():
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 16
    expected = {
        tuple(tuple([8] * width) for _ in range(height))
        for height in range(3, 7)
        for width in range(3, 7)
    }
    observed = {
        tuple(tuple(row) for row in gen.rule_mirror(gen.generate(3100, index)))
        for index in range(16)
    }
    assert observed == expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_twenty_draws_cover_both_slants_and_a_canonical_profile(band):
    grids = [gen.generate(900 + index, index, difficulty=band) for index in range(20)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    observations = [gen.semantic_observables(grid) for grid in grids]
    assert {obs["slant"] for obs in observations} == {"positive", "negative"}
    assert any(obs["strict_canonical"] for obs in observations)
    assert any(obs["rectangular_bbox"] for obs in observations)


def test_every_four_pair_window_is_identifying_after_any_query_rotation():
    for band in ("easy", "medium", "hard"):
        # Fix the seed residue and enumerate the complete sixteen-slot period;
        # varying both seed and sample_index together would visit only half of
        # the cyclic starts because the schedule keys on their sum.
        for start in range(16):
            grids = [
                gen.generate(1200, start + offset, difficulty=band)
                for offset in range(4)
            ]
            pairs = [{"input": grid, "output": independent_output(grid)} for grid in grids]
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                query = pairs[held_out]
                assert gen.lesson_identifiable(demos, query) == []
                slants = {gen.observe_overrides(demo["input"])["slant"] for demo in demos}
                assert slants == {"positive", "negative"}


def test_declared_orientation_rivals_are_real_counterexamples():
    positive = gen.generate(31, 0, slant="positive")
    negative = gen.generate(31, 1, slant="negative")
    truth_pos = independent_output(positive)
    truth_neg = independent_output(negative)
    assert gen.SEMANTIC_RIVALS["positive_slant_only"](positive) == truth_pos
    assert gen.SEMANTIC_RIVALS["positive_slant_only"](negative) != truth_neg
    assert gen.SEMANTIC_RIVALS["negative_slant_only"](negative) == truth_neg
    assert gen.SEMANTIC_RIVALS["negative_slant_only"](positive) != truth_pos
    assert set(gen.LESSON_COMPETITORS) >= {
        "positive_slant_only",
        "negative_slant_only",
        "same_size_fill",
        "border_only_crop",
        "row_span_square",
        "column_span_square",
        "identity",
    }


def test_every_declared_rival_returns_a_well_formed_grid_on_lawful_inputs():
    grids = (
        gen.generate(31, 0, slant="positive"),
        gen.generate(31, 1, slant="negative"),
    )
    for family in (gen.SEMANTIC_RIVALS, gen.LESSON_COMPETITORS):
        for name, rival in family.items():
            for grid in grids:
                output = rival(grid)
                assert isinstance(output, list) and output, name
                assert isinstance(output[0], list) and output[0], name
                width = len(output[0])
                assert all(isinstance(row, list) and len(row) == width for row in output), name
                assert all(
                    type(value) is int and 0 <= value <= 9
                    for row in output
                    for value in row
                ), name


def test_structural_checker_rejects_targeted_impostors():
    lawful = gen.generate(1234, 17, grid_h=8, grid_w=9, slant="negative")
    assert gen.self_check(lawful) == []

    ragged = [[0, 0], [0]]
    bad_color = copy.deepcopy(lawful)
    bad_color[0][0] = 2
    one_point = [[0] * 8 for _ in range(8)]
    one_point[1][1] = 1
    aligned = [[0] * 8 for _ in range(8)]
    aligned[1][1] = aligned[1][6] = 1
    too_thin = [[0] * 8 for _ in range(8)]
    too_thin[1][1] = too_thin[2][6] = 1
    third = copy.deepcopy(lawful)
    third[0][0] = 1

    for grid in (None, [], [[]], ragged, bad_color, one_point, aligned, too_thin, third):
        assert gen.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(778899)
    state = random.getstate()
    first = gen.generate(101, 202, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(101, 202, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
