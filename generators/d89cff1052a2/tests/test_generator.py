"""Portable regression tests for the vertical-mirror-above-original sampler."""
from __future__ import annotations

from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "d89cff1052a2"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def _oracle(grid):
    return [row[:] for row in reversed(grid)] + [row[:] for row in grid]


def _is_ud_symmetric(grid):
    return grid == list(reversed(grid))


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_canonical_pairs_are_bound():
    assert GEN.RULE_HASH == "370a7fcc45fc"
    assert len(CANONICAL) == 5
    for pair in CANONICAL:
        assert GEN.self_check(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]


def test_public_override_surface_is_small_and_falsifiable():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "palette_size", "ud_asymmetric"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 3, "grid_w": 3, "palette_size": 4, "ud_asymmetric": False},
        {"grid_h": 3, "grid_w": 4, "palette_size": 2, "ud_asymmetric": True},
        {"grid_h": 15, "grid_w": 30, "palette_size": 4, "ud_asymmetric": True},
    ],
)
def test_exact_overrides_are_observable_in_every_band(difficulty, overrides):
    grid = GEN.generate(71, 11, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
    assert GEN.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": 1.0},
        {"seed": "1"},
        {"sample_index": True},
        {"sample_index": 1.0},
        {"sample_index": "1"},
        {"sample_index": -1},
        {"difficulty": True},
        {"difficulty": 1},
        {"difficulty": "expert"},
        {"grid_h": True},
        {"grid_h": 2},
        {"grid_h": 16},
        {"grid_w": 2},
        {"grid_w": 31},
        {"palette_size": 1},
        {"palette_size": 5},
        {"ud_asymmetric": 1},
        {"texture": "noise"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    arguments = {"seed": 0, "sample_index": 0, "difficulty": "medium"}
    arguments.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**arguments)


def test_default_schedule_reaches_canonical_profile_in_every_band_and_keeps_broad_support():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(900 + index, index, difficulty=difficulty) for index in range(20)]
        assert all(GEN.self_check(grid, difficulty=difficulty) == [] for grid in grids)
        exact = sum(_profile(grid) == (3, 4, 2) for grid in grids)
        assert exact >= 10
        assert any(len(grid) != 3 or len(grid[0]) != 4 for grid in grids)
        assert all(not _is_ud_symmetric(grid) for grid in grids)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_default_broad_schedule_slot_has_noncanonical_height(difficulty):
    """Rotating any one lesson pair to query must leave a broad-height demo."""
    for seed in range(12):
        for sample_index in range(1, 12, 2):
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            assert len(grid) != 3, (difficulty, seed, sample_index, grid)


def test_generated_grids_are_repeatable_and_use_every_declared_color():
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(18):
            first = GEN.generate(1234, sample_index, difficulty=difficulty)
            GEN.generate(9999, 999, difficulty="hard")
            second = GEN.generate(1234, sample_index, difficulty=difficulty)
            assert first == second
            counts = Counter(value for row in first for value in row)
            assert 2 <= len(counts) <= 4
            assert min(counts.values()) >= 2


def test_declared_rivals_are_executable_and_have_output_changing_witnesses():
    intended = GEN.generate(
        17,
        2,
        difficulty="medium",
        grid_h=4,
        grid_w=7,
        palette_size=2,
        ud_asymmetric=True,
    )
    expected = _oracle(intended)
    assert GEN.SEMANTIC_WITNESSES["non_three_height"](intended)
    assert GEN.SEMANTIC_WITNESSES["visible_flip"](intended)
    assert GEN.SEMANTIC_RIVALS["fixed_three_row_mirror"](intended) != expected
    assert GEN.SEMANTIC_RIVALS["duplicate_input"](intended) != expected

    # The fixed-three-row shortcut is genuinely canonical-consistent: every
    # official input has height three, so this simpler rival fits every label.
    for pair in CANONICAL:
        assert GEN.CANONICAL_SHORTCUTS["fixed_three_row_mirror"](pair["input"]) == pair["output"]


def test_self_check_rejects_structural_impostors():
    bad_grids = [
        [],
        [[1, 2], [1]],
        [[1, 1, 1] for _ in range(3)],
        [[1, 1, 1], [1, 2, 1], [1, 1, 1]],
        [[1, 2], [2, 1]],
        [[2, 2, 1, 1], [2, 2, 1, 1], [1, 1, 1, 1]],  # modal-bg solid 2x2
        [[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1]],  # modal-bg short line
        [[1, 2, 2], [2, True, 2], [2, 2, 1]],
        [[1, 2, 2], [2, 10, 2], [2, 2, 1]],
    ]
    for grid in bad_grids:
        assert GEN.self_check(grid), grid


def test_strict_canonical_profile_matches_the_documented_shape_not_one_fixed_grid():
    strict_samples = [
        GEN.generate(500 + index, 2 * index, difficulty="medium")
        for index in range(8)
    ]
    assert len({tuple(tuple(row) for row in grid) for grid in strict_samples}) > 1
    for grid in strict_samples:
        assert GEN.strict_canonical_like(grid) == []
        assert _profile(grid) == (3, 4, 2)
