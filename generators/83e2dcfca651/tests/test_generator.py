"""Regression and semantic-contract tests for 83e2dcfca651."""
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
    components4,
    green_cells,
    load_generator,
    marker_vector,
    observed,
    racket_outputs,
    shape_signature,
    translated_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_contract_metadata():
    assert gen.RULE_HASH == "94474e600431"
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.AXES) == {"grid_h", "grid_w", "object_size", "vector_dr", "vector_dc"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_inputs_are_accepted_and_oracle_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert translated_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 8, "grid_w": 10, "object_size": 3, "vector_dr": -4, "vector_dc": -5},
        {"grid_h": 12, "grid_w": 15, "object_size": 6, "vector_dr": 4, "vector_dc": 5},
        {"grid_h": 9, "grid_w": 12, "object_size": 5, "vector_dr": -1, "vector_dc": 1},
    ],
)
def test_exact_overrides_are_realized_in_every_band(band, options):
    grid = gen.generate(41, 7, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 7},
        {"grid_w": 16},
        {"object_size": 2},
        {"object_size": 7},
        {"vector_dr": 0},
        {"vector_dc": 0},
        {"vector_dr": -5},
        {"vector_dc": 6},
        {"grid_h": True},
        {"object_size": 4.0},
        {"vector_dc": "2"},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_quadrant_schedule_is_explicit_and_repeatable():
    expected = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for start in range(8):
        signs = []
        for offset in range(4):
            grid = gen.generate(77, start + offset, difficulty="medium")
            dr, dc = marker_vector(grid)
            signs.append(((dr > 0) - (dr < 0), (dc > 0) - (dc < 0)))
            assert gen.schedule_profile(77, start + offset, difficulty="medium") == gen.SCHEDULE_PROFILES[(start + offset) % 4]
        assert set(signs) == set(expected)


def test_difficulty_bands_materially_change_instances_without_changing_domain():
    triples = [
        tuple(tuple(row) for row in gen.generate(901 + i, i, difficulty=band))
        for i in range(24)
        for band in ("easy", "medium", "hard")
    ]
    grouped = [triples[i : i + 3] for i in range(0, len(triples), 3)]
    assert sum(len(set(group)) > 1 for group in grouped) >= 20


def test_generated_distribution_is_lawful_diverse_and_reference_equivalent():
    grids = []
    shapes = set()
    sizes = set()
    vectors = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(32):
            grid = gen.generate(1200 + band_index * 100 + i, i, difficulty=band)
            assert gen.self_check(grid) == []
            assert len(components4(green_cells(grid))) == 1
            shapes.add(shape_signature(grid))
            sizes.add(len(green_cells(grid)))
            vectors.add(marker_vector(grid))
            if i < 6:
                grids.append(grid)
    assert sizes == {3, 4, 5, 6}
    assert len(shapes) >= 30
    assert len(vectors) >= 40
    expected = [translated_output(grid) for grid in grids]
    assert racket_outputs(grids) == expected


def test_generation_and_rivals_are_pure():
    grid = gen.generate(8, 3, vector_dr=-3, vector_dc=4)
    original = deepcopy(grid)
    canonical = translated_output(grid)
    rival = gen.CANONICAL_SHORTCUTS["absolute_vector"](grid)
    assert grid == original
    assert canonical != rival
    assert gen.SEMANTIC_WITNESSES["signed_vector"](grid)
    assert gen.WITNESS_RIVALS["signed_vector"] == ["absolute_vector"]


def test_absolute_vector_shortcut_fits_canonical_but_is_refuted_by_generation():
    rival = gen.CANONICAL_SHORTCUTS["absolute_vector"]
    pairs = canonical_pairs()
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    for index in (2, 3, 6, 7):
        grid = gen.generate(55, index)
        assert gen.SEMANTIC_WITNESSES["signed_vector"](grid)
        assert rival(grid) != translated_output(grid)


def test_four_example_lessons_are_identifiable_and_short_lessons_can_be_rejected():
    for start in range(8):
        pairs = []
        for offset in range(5):
            grid = gen.generate(500 + start, start + offset, difficulty="hard")
            pairs.append({"input": grid, "output": translated_output(grid)})
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
    positive = []
    for index in (0, 4, 8, 12):
        grid = gen.generate(33, index, vector_dr=2, vector_dc=3)
        positive.append({"input": grid, "output": translated_output(grid)})
    reasons = gen.lesson_identifiable(positive[:3], positive[3])
    assert reasons and any("absolute" in reason.lower() for reason in reasons)


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_color",
        "extra_marker",
        "disconnect_object",
        "erase_object",
        "target_collision",
        "out_of_bounds_translation",
    ],
)
def test_self_check_rejects_semantic_mutations(mutation):
    grid = gen.generate(910, 5, grid_h=12, grid_w=15, object_size=5, vector_dr=3, vector_dc=4)
    if mutation == "unknown_color":
        grid[0][0] = 9
    elif mutation == "extra_marker":
        grid[0][0] = 1
    elif mutation == "disconnect_object":
        cells = sorted(green_cells(grid))
        grid[cells[0][0]][cells[0][1]] = 0
        grid[0][0] = 3
    elif mutation == "erase_object":
        for r, c in green_cells(grid):
            grid[r][c] = 0
    elif mutation == "target_collision":
        dr, dc = marker_vector(grid)
        r, c = next(iter(green_cells(grid)))
        grid[r + dr][c + dc] = 3
    elif mutation == "out_of_bounds_translation":
        p2 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
        grid[p2[0]][p2[1]] = 0
        grid[-1][-1] = 2
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 0]], [[True] * 10 for _ in range(8)]])
def test_self_check_is_diagnostic_on_malformed_grids(bad):
    assert gen.self_check(bad)
