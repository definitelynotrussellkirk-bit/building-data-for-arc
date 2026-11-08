"""Focused contract and teaching regressions for dfc4967f816f."""
from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "dfc4967f816f"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _tiles(grid):
    """Parse the selected one-row 3x3 tile strip."""
    assert len(grid) == 3
    width = len(grid[0])
    assert width >= 11 and (width + 1) % 4 == 0
    count = (width + 1) // 4
    for row in grid:
        assert len(row) == width
    for divider in range(3, width, 4):
        assert all(row[divider] == 9 for row in grid)
    return [
        [row[left:left + 3] for row in grid]
        for left in range(0, width, 4)
    ]


def _vertically_symmetric(tile):
    return all(row == row[::-1] for row in tile)


def independent_rule(grid):
    return [[8 if _vertically_symmetric(tile) else 0 for tile in _tiles(grid)]]


def top_row_only_rival(grid):
    return [[8 if tile[0] == tile[0][::-1] else 0 for tile in _tiles(grid)]]


def fixed_even_positions_rival(grid):
    return [[8 if index % 2 == 0 else 0 for index, _ in enumerate(_tiles(grid))]]


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_and_small_honest_axis_surface():
    assert GEN.RULE_HASH == "136bfe841cf2"
    assert set(GEN.AXES) == {"tile_cols", "foreground_color"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("tile_cols", [3, 4, 5, 6])
@pytest.mark.parametrize("foreground_color", [1, 4, 8])
def test_exact_controls_are_constructive_observable_and_semantically_mixed(
    band, tile_cols, foreground_color
):
    grid = GEN.generate(
        20261019,
        7,
        difficulty=band,
        tile_cols=tile_cols,
        foreground_color=foreground_color,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "tile_cols": tile_cols,
        "foreground_color": foreground_color,
    }
    assert len(grid) == 3
    assert len(grid[0]) == tile_cols * 4 - 1
    assert {value for row in grid for value in row} == {0, 9, foreground_color}
    output = independent_rule(grid)
    assert 0 in output[0] and 8 in output[0]
    # Every normal lesson contains a hard negative for the canonical top-row shortcut.
    assert top_row_only_rival(grid) != output
    # And it does not repeat the canonical fixed 8,0,8,0 positional pattern.
    assert fixed_even_positions_rival(grid) != output


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"tile_cols": True},
        {"tile_cols": 4.0},
        {"tile_cols": "4"},
        {"tile_cols": 2},
        {"tile_cols": 7},
        {"foreground_color": False},
        {"foreground_color": 2.0},
        {"foreground_color": "2"},
        {"foreground_color": 0},
        {"foreground_color": 9},
    ],
)
def test_invalid_or_unknown_controls_fail_loudly(kwargs):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **kwargs)


def test_canonical_inputs_are_accepted_and_shortcuts_really_fit_them():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert top_row_only_rival(pair["input"]) == pair["output"]
        assert fixed_even_positions_rival(pair["input"]) == pair["output"]


def test_declared_semantic_contract_matches_independent_rivals():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"top_row_only", "fixed_even_positions"}
    assert set(GEN.SEMANTIC_RIVALS) == set(GEN.CANONICAL_SHORTCUTS)
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.CANONICAL_SHORTCUTS)
    assert GEN.WITNESS_RIVALS == {
        "deep_row_asymmetry": ["top_row_only"],
        "noncanonical_positions": ["fixed_even_positions"],
    }
    expected = {
        "top_row_only": top_row_only_rival,
        "fixed_even_positions": fixed_even_positions_rival,
    }
    for name, rival in expected.items():
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert GEN.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sampled_grid_refutes_both_declared_shortcuts(band):
    for index in range(24):
        grid = GEN.generate(881, index, difficulty=band)
        truth = independent_rule(grid)
        assert GEN.SEMANTIC_WITNESSES["deep_row_asymmetry"](grid)
        assert GEN.SEMANTIC_WITNESSES["noncanonical_positions"](grid)
        assert GEN.SEMANTIC_RIVALS["top_row_only"](grid) != truth
        assert GEN.SEMANTIC_RIVALS["fixed_even_positions"](grid) != truth


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_native_profile_floor_has_exact_canonical_support_in_every_band(band):
    exact = 0
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        exact += _profile(grid) == (3, 15, 3)
    assert exact >= 3, (band, exact)


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(91, index, difficulty=band)
            second = GEN.generate(91, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            snapshot = deepcopy(first)
            assert GEN.self_check(first) == []
            assert GEN.observe_overrides(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
            assert first == snapshot


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 11 for _ in range(2)],
        [[0] * 11 for _ in range(3)],
        [[0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0] for _ in range(3)],
    ],
)
def test_validator_rejects_malformed_or_semantically_empty_inputs(grid):
    assert GEN.self_check(grid)
