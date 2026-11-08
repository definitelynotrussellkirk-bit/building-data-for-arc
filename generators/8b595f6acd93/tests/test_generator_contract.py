"""Focused contract tests for the repaired 8b595f6acd93 base generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_8b_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def g():
    return load_generator()


def test_rule_hash_is_pinned_to_reverified_canonical_authority(g):
    assert g.RULE_HASH == "bd39a99359bd"


@pytest.mark.parametrize(
    "difficulty,height,width,count",
    [
        ("easy", 7, 16, 1),
        ("medium", 16, 7, 2),
        ("hard", 16, 16, 6),
        (None, 7, 7, 1),
    ],
)
def test_declared_overrides_are_valid_independently_of_sampling_band(
    g, difficulty, height, width, count
):
    grid = g.generate(
        17,
        0,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        n_pluses=count,
    )
    assert len(grid) == height
    assert {len(row) for row in grid} == {width}
    assert len(g._fillable_plus_centers(grid)) == count
    assert g.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard", None])
def test_explicit_motif_count_expands_only_unspecified_dimensions(g, difficulty):
    for sample_index in range(12):
        grid = g.generate(31, sample_index, difficulty=difficulty, n_pluses=6)
        assert 7 <= len(grid) <= 16
        assert 7 <= len(grid[0]) <= 16
        assert len(g._fillable_plus_centers(grid)) == 6
        assert g.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": True},
        {"grid_h": 7.0},
        {"grid_h": "7"},
        {"grid_h": 6},
        {"grid_h": 17},
        {"grid_w": False},
        {"n_pluses": 0},
        {"n_pluses": 7},
        {"texture": "bogus"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(g, overrides):
    with pytest.raises((TypeError, ValueError)):
        g.generate(0, 0, **overrides)


def test_default_sampling_stays_inside_original_bands(g):
    bands = {
        "easy": ((8, 9), (8, 9), (2, 2)),
        "medium": ((8, 12), (8, 12), (2, 4)),
        "hard": ((11, 12), (11, 12), (3, 4)),
        None: ((8, 12), (8, 12), (2, 4)),
    }
    for difficulty, (hs, ws, counts) in bands.items():
        for sample_index in range(12):
            grid = g.generate(23, sample_index, difficulty=difficulty)
            centers = g._fillable_plus_centers(grid)
            assert hs[0] <= len(grid) <= hs[1]
            assert ws[0] <= len(grid[0]) <= ws[1]
            assert len(centers) >= counts[0]
            assert g.self_check(grid, difficulty=difficulty) == []


def test_near_misses_do_not_create_fillable_targets(g):
    for texture in ("no_pluses", "partial_arms", "mismatched_arms"):
        grid = g.generate(0, 0, texture=texture)
        assert g._fillable_plus_centers(grid) == []
        assert g.self_check(grid)


@pytest.mark.parametrize(
    "height,width,count,seed,sample_index",
    [
        (7, 7, 2, 0, 10),
        (9, 9, 2, 0, 31),
        (11, 9, 3, 0, 2),
        (12, 12, 4, 0, 2),
        (16, 16, 6, 0, 2),
    ],
)
def test_explicit_n_pluses_is_the_exact_number_of_fillable_centers(
    g, height, width, count, seed, sample_index
):
    grid = g.generate(
        seed,
        sample_index,
        grid_h=height,
        grid_w=width,
        n_pluses=count,
    )
    assert g._fillable_plus_centers(grid) == sorted(g._fillable_plus_centers(grid))
    assert len(g._fillable_plus_centers(grid)) == count
    assert g.self_check(grid) == []


def test_self_check_rejects_out_of_domain_shape_and_overlapping_targets(g):
    small = [[0] * 5 for _ in range(5)]
    g._draw_plus(small, 2, 2)
    assert any("dimensions" in error for error in g.self_check(small))

    overlapping = [[0] * 7 for _ in range(7)]
    g._draw_plus(overlapping, 2, 2)
    g._draw_plus(overlapping, 4, 4)
    assert len(g._fillable_plus_centers(overlapping)) == 3
    assert any("overlap" in error for error in g.self_check(overlapping))


def test_self_check_allows_canonical_partial_plus_distractors(g):
    canonical_like = [[0] * 9 for _ in range(9)]
    g._draw_plus(canonical_like, 2, 2)
    canonical_like[6][6] = 3
    canonical_like[7][5] = 3
    canonical_like[7][7] = 3
    assert g._fillable_plus_centers(canonical_like) == [(2, 2)]
    assert g.self_check(canonical_like) == []
