"""Regressions for varied, informative transpose-fill inputs (canonical rule)."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("1e7c25b06dac", root=ROOT)


def test_all_canonical_inputs_are_in_the_validation_domain():
    for pair in canonical_pairs("1e7c25b06dac", root=ROOT):
        assert GEN.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])


@pytest.mark.parametrize("bad", [-1, 10, 1.5, True, "2", None])
def test_validator_rejects_non_arc_cells(bad):
    grid = [[0, bad, 0], [0, 0, 2], [3, 0, 0]]
    assert GEN.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0, 1], [0]], [[0, 1, 0], [0, 0, 2]]])
def test_validator_returns_errors_for_malformed_grids(grid):
    assert GEN.self_check(grid)


def test_validator_rejects_identity_only_lessons():
    for grid in ([[0] * 3 for _ in range(3)],
                 [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
                 [[0, 1, 0], [1, 0, 0], [0, 0, 3]]):
        assert GEN.self_check(grid)


@pytest.mark.parametrize("size", [3, 6, 20, 30])
def test_exact_square_size_overrides_and_determinism(size):
    grid = GEN.generate(71, 4, grid_h=size, grid_w=size)
    assert len(grid) == size and all(len(row) == size for row in grid)
    assert GEN.self_check(grid) == []
    assert grid == GEN.generate(71, 4, grid_h=size, grid_w=size)
    assert grid == GEN.generate(71, 4, grid_size=size)


@pytest.mark.parametrize("overrides", [
    {"grid_size": True}, {"grid_size": 6.8}, {"grid_size": "7"},
    {"grid_size": 2}, {"grid_size": 31}, {"grid_h": 5, "grid_w": 6},
    {"grid_size": 6, "grid_h": 7}, {"palette_size": True},
    {"palette_size": 0}, {"palette_size": 10}, {"position_bias": "fixed"},
    {"texture": "unknown"},
])
def test_invalid_overrides_fail_explicitly(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(8, 0, **overrides)


def test_sampling_defeats_one_triangle_and_fixed_position_shortcuts():
    supports, counts, diagonal, repeated = set(), set(), False, False
    for index in range(32):
        grid = GEN.generate(173, index, grid_size=9)
        assert GEN.self_check(grid) == []
        cells = [(r, c) for r in range(9) for c in range(9) if grid[r][c]]
        assert any(r < c and grid[c][r] == 0 for r, c in cells)
        assert any(r > c and grid[c][r] == 0 for r, c in cells)
        assert all(r == c or grid[c][r] == 0 for r, c in cells)
        supports.add(tuple(cells))
        counts.add(len(cells))
        diagonal |= any(r == c for r, c in cells)
        repeated |= len({grid[r][c] for r, c in cells}) < len(cells)
    assert len(supports) >= 24
    assert len(counts) >= 3
    assert diagonal and repeated


def test_one_color_is_supported_without_changing_spatial_rule():
    grid = GEN.generate(91, 2, grid_size=30, palette_size=1)
    assert GEN.self_check(grid) == []
    assert len({cell for row in grid for cell in row if cell}) == 1


def test_diagnostic_textures_stay_out_of_ordinary_lesson_domain():
    for texture in ("no_marks", "full_diagonal", "full_grid"):
        grid = GEN.generate(1, 0, texture=texture, grid_size=6)
        assert len(grid) == 6
        assert GEN.self_check(grid)


@pytest.mark.parametrize("texture", [False, 0, [], {}, ""])
def test_texture_does_not_coerce_falsy_values_to_a_default(texture):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, texture=texture)


def test_self_check_does_not_mutate_a_valid_input():
    grid = [[0, 1, 0], [0, 0, 2], [3, 0, 0]]
    before = deepcopy(grid)
    assert GEN.self_check(grid) == []
    assert grid == before
