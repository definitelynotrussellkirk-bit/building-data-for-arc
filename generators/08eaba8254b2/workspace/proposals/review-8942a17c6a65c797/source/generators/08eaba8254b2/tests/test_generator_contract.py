"""Regression and contract tests for the repaired 08eaba8254b2 base."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_08_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def g():
    return load_generator()


def xor_count(grid) -> int:
    width = len(grid[0])
    return sum(
        (grid[r][c] == 0) != (grid[5 + r][c] == 0)
        for r in range(4)
        for c in range(width)
    )


def test_rule_hash_is_pinned_to_reverified_canonical_authority(g):
    assert g.RULE_HASH == "5679cfe5ff27"


@pytest.mark.parametrize(
    "difficulty,width",
    [("easy", 1), ("hard", 1), ("easy", 30), ("hard", 30), (None, 30)],
)
def test_declared_width_overrides_are_independent_of_sampling_band(g, difficulty, width):
    grid = g.generate(101, 0, difficulty=difficulty, grid_w=width)
    assert len(grid) == 9
    assert {len(row) for row in grid} == {width}
    assert g.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("width,target", [(1, 4), (14, 56), (30, 120)])
def test_dynamic_xor_target_reaches_the_full_declared_canvas(g, width, target):
    grid = g.generate(
        7,
        0,
        difficulty="hard",
        grid_w=width,
        xor_target=target,
        panel_pattern="checker",
    )
    assert xor_count(grid) == target
    assert g.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_w": True},
        {"grid_w": 3.0},
        {"grid_w": "3"},
        {"grid_w": 0},
        {"grid_w": 31},
        {"xor_target": False},
        {"xor_target": 1.0},
        {"grid_w": 3, "xor_target": 13},
        {"panel_pattern": "bogus"},
        {"texture": "bogus"},
        {"panel_pattern": "random", "texture": "random"},
        {"top_density": -0.01},
        {"top_density": 1.01},
        {"top_density": True},
        {"bot_density": float("nan")},
        {"top_color": 0},
        {"top_color": True},
        {"top_color": 3, "bot_color": 3},
        {"top_color": 3, "bot_color": 4, "sep_color": 4},
        {"unknown_axis": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(g, overrides):
    with pytest.raises((TypeError, ValueError)):
        g.generate(0, 0, **overrides)


def test_default_sampling_keeps_historical_width_bands_and_valid_structure(g):
    bands = {"easy": (3, 5), "medium": (3, 14), "hard": (10, 14), None: (3, 14)}
    for difficulty, (low, high) in bands.items():
        for sample_index in range(20):
            grid = g.generate(23, sample_index, difficulty=difficulty)
            assert low <= len(grid[0]) <= high
            assert g.self_check(grid, difficulty=difficulty) == []
            assert 1 <= xor_count(grid) < 4 * len(grid[0])


def test_requested_minimum_xor_is_met_for_nonmaximal_targets(g):
    for width, target in ((3, 7), (8, 20), (30, 83)):
        grid = g.generate(
            88,
            width,
            grid_w=width,
            xor_target=target,
            panel_pattern="border",
            top_density=0,
            bot_density=1,
        )
        assert target <= xor_count(grid) < 4 * width
        assert g.self_check(grid) == []


def test_self_check_rejects_the_retained_minimal_structural_imposter(g):
    imposter = [[0] * 3 for _ in range(9)]
    imposter[0][0] = 2
    errors = g.self_check(imposter)
    assert errors
    assert any("separator" in error for error in errors)
    assert any("bottom panel" in error for error in errors)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[0, 0], [0]],
        [[0] * 3 for _ in range(8)],
        [[0] * 3 for _ in range(10)],
        [[0] * 3 for _ in range(9)],
    ],
)
def test_self_check_rejects_empty_ragged_wrong_height_or_blank_structure(g, grid):
    assert g.self_check(grid)


def test_self_check_rejects_noninteger_or_out_of_palette_cells(g):
    valid = g.generate(5, 0, grid_w=4)
    for value in (True, 1.5, -1, 10):
        bad = [row[:] for row in valid]
        bad[0][0] = value
        assert g.self_check(bad)


def test_broken_separator_is_inert_but_never_entirely_absent(g):
    for width in (1, 3, 14, 30):
        grid = g.generate(9, width, grid_w=width, texture="broken_sep")
        assert any(grid[4][c] != 0 for c in range(width))
        assert g.self_check(grid) == []


def test_degenerate_texture_does_not_silently_ignore_unrelated_controls(g):
    with pytest.raises(ValueError):
        g.generate(0, 0, texture="same_panels", top_color=2)
    grid = g.generate(0, 0, texture="same_panels", grid_w=30)
    assert len(grid[0]) == 30
