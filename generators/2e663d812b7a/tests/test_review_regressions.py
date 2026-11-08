"""Behavioral regressions for the row-key Chebyshev-ring input generator.

Run through ``run_with_racket.py python3 -m pytest`` in a review packet,
or use the public ``arcpuzzles check ... --stage task_tests`` command.
Only this test's own library/runtime supplies code and canonical data.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import shutil

import pytest

from reviewer_support import canonical_pairs, find_root
from arcpuzzles import Catalog


TASK_ID = "2e663d812b7a"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_regressions_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def key(grid):
    """A zero inside the key is meaningful; only trailing zeros are padding."""
    end = max(c for c, value in enumerate(grid[0]) if value != 0)
    return grid[0][:end + 1]


def lower_seed(grid):
    cells = [(r, c) for r in range(2, len(grid))
             for c, value in enumerate(grid[r]) if value != 0]
    assert len(cells) == 1, f"expected exactly one seed below separator: {cells}"
    return cells[0]


def assert_lawful(grid):
    assert isinstance(grid, list) and 9 <= len(grid) <= 30
    width = len(grid[0])
    assert 9 <= width <= 30
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    assert grid[1] == [5] * width, "row 1 must be the full gray separator"
    colors = key(grid)
    assert colors[0] != 0
    assert 1 <= len(colors) <= min(10, width)
    assert 5 not in colors, "gray is reserved for the separator"
    assert len(set(colors) - {0}) <= 6
    row, col = lower_seed(grid)
    assert grid[row][col] == colors[0], "seed must identify the distance-zero key color"
    assert GEN.self_check(grid) == []


def valid_grid():
    grid = [[0] * 16 for _ in range(16)]
    grid[0][:6] = [2, 3, 3, 4, 0, 8]
    grid[1] = [5] * 16
    grid[11][5] = 2
    return grid


@pytest.mark.parametrize("pair", PAIRS, ids=[
    f"variant{p['variant']}-{p['split']}{p['pair_index']}" for p in PAIRS
])
def test_every_canonical_input_is_accepted(pair):
    assert_lawful(pair["input"])


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_seeded_inputs_obey_visible_task_structure(difficulty):
    for sample_index in range(24):
        grid = GEN.generate(20261003, sample_index, difficulty=difficulty)
        assert_lawful(grid)
        assert grid == GEN.generate(20261003, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("height,width", [(9, 18), (18, 9), (16, 16)])
def test_grid_dimension_overrides_are_exact(height, width):
    grid = GEN.generate(701, 3, grid_h=height, grid_w=width, key_len=3)
    assert (len(grid), len(grid[0])) == (height, width)


@pytest.mark.parametrize("length,width", [(1, 9), (6, 9), (9, 9), (10, 10), (10, 18)])
def test_key_length_overrides_include_the_advertised_upper_limit(length, width):
    grid = GEN.generate(812, 4, grid_h=16, grid_w=width, key_len=length)
    assert len(key(grid)) == length
    assert grid[0][length:] == [0] * (width - length)


@pytest.mark.parametrize("damage", [
    "separator_missing", "separator_hole", "multiple_seed", "mismatched_seed",
    "seed_in_separator", "no_key", "no_seed",
])
def test_self_check_rejects_broken_task_structure(damage):
    grid = valid_grid()
    if damage == "separator_missing":
        grid[1] = [0] * 16
    elif damage == "separator_hole":
        grid[1][7] = 0
    elif damage == "multiple_seed":
        grid[12][6] = grid[0][0]
    elif damage == "mismatched_seed":
        grid[11][5] = 7
    elif damage == "seed_in_separator":
        grid[11][5] = 0
        grid[1][5] = 2
    elif damage == "no_key":
        grid[0] = [0] * 16
    elif damage == "no_seed":
        grid[11][5] = 0
    assert GEN.self_check(grid), f"self_check accepted {damage}"


@pytest.mark.parametrize("value", [-1, 10, 2.0, True, "2"])
def test_self_check_rejects_invalid_color_values(value):
    grid = valid_grid()
    grid[0][2] = value
    assert GEN.self_check(grid), f"self_check accepted invalid color {value!r}"


@pytest.mark.parametrize("grid", [[], [[]], [[0, 0], [0]]])
def test_self_check_rejects_empty_or_ragged_grids(grid):
    assert GEN.self_check(grid)


def test_self_check_accepts_zero_rings_and_repeated_ring_colors():
    grid = valid_grid()
    assert key(grid) == [2, 3, 3, 4, 0, 8]
    assert GEN.self_check(grid) == []


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_single_entry_key_is_admitted_by_public_production_generation():
    """A lawful exact override must survive production pair admission."""
    episode, = Catalog(ROOT).generate(
        TASK_ID, seed=71, n_train=1, n_test=1, difficulty="easy",
        overrides={"key_len": 1}, allow_unapproved=True, timeout=30,
    )
    pairs = episode["train"] + episode["test"]
    assert len(pairs) == 2
    assert all(pair["input"] == pair["output"] for pair in pairs)
    assert all(len(key(pair["input"])) == 1 for pair in pairs)


@pytest.fixture(scope="module")
def default_samples():
    return [GEN.generate(4417, index) for index in range(192)]


def test_default_sampling_routinely_reaches_canonical_dimensions(default_samples):
    count = sum((len(grid), len(grid[0])) == (16, 16) for grid in default_samples)
    assert count >= 12, f"only {count}/192 default samples have canonical 16x16 dimensions"


def test_default_sampling_reaches_zero_valued_internal_rings(default_samples):
    assert any(0 in key(grid)[1:-1] for grid in default_samples)


def test_default_sampling_reaches_repeated_nonzero_ring_colors(default_samples):
    assert any(any(count > 1 for count in Counter(value for value in key(grid) if value).values())
               for grid in default_samples)


def test_default_sampling_reaches_complete_and_boundary_clipped_rings(default_samples):
    clipped = []
    for grid in default_samples:
        row, col = lower_seed(grid)
        radius = len(key(grid)) - 1
        if radius == 0:
            continue
        clipped.append(row - radius < 2 or row + radius >= len(grid)
                       or col - radius < 0 or col + radius >= len(grid[0]))
    assert any(clipped), "no boundary-clipped ring examples"
    assert not all(clipped), "no complete ring examples"


def observed_axes(grid):
    colors = key(grid)
    row, col = lower_seed(grid)
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "key_len": len(colors),
        "palette_size": len(set(colors) - {0}), "zero_rings": colors.count(0),
        "seed_r": row, "seed_c": col,
    }


@pytest.mark.parametrize("row,col", [(2, 0), (2, 17), (17, 0), (17, 17), (8, 8)])
def test_seed_coordinates_are_exact_including_all_lower_canvas_corners(row, col):
    overrides = dict(grid_h=18, grid_w=18, key_len=6, palette_size=4,
                     zero_rings=1, seed_r=row, seed_c=col)
    grid = GEN.generate(1504, 3, **overrides)
    assert_lawful(grid)
    assert observed_axes(grid) == overrides


@pytest.mark.parametrize("length,palette_size,zero_rings", [
    (1, 1, 0), (3, 3, 0), (6, 6, 0), (6, 4, 1),
    (8, 6, 1), (8, 3, 4), (10, 1, 8), (10, 2, 8),
])
def test_key_palette_and_zero_ring_counts_are_exact(length, palette_size, zero_rings):
    overrides = dict(grid_h=16, grid_w=16, key_len=length,
                     palette_size=palette_size, zero_rings=zero_rings,
                     seed_r=10, seed_c=10)
    for sample_index in range(4):
        grid = GEN.generate(388, sample_index, **overrides)
        assert_lawful(grid)
        assert observed_axes(grid) == overrides


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 9), ("grid_h", 18), ("grid_w", 9), ("grid_w", 18),
    ("key_len", 1), ("key_len", 10), ("palette_size", 1), ("palette_size", 6),
    ("zero_rings", 0), ("zero_rings", 8), ("seed_r", 2), ("seed_r", 17),
    ("seed_c", 0), ("seed_c", 17),
])
def test_single_axis_extremes_adapt_unpinned_dependencies(axis, value):
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(4):
            grid = GEN.generate(499, sample_index, difficulty=difficulty, **{axis: value})
            assert_lawful(grid)
            assert observed_axes(grid)[axis] == value


@pytest.mark.parametrize("overrides", [
    {"grid_w": 9, "key_len": 10},
    {"grid_h": 9, "seed_r": 17},
    {"grid_w": 9, "seed_c": 17},
    {"key_len": 1, "palette_size": 6},
    {"key_len": 2, "zero_rings": 1},
    {"palette_size": 6, "zero_rings": 8},
    {"key_len": 6, "palette_size": 6, "zero_rings": 1},
])
def test_incompatible_joint_controls_are_reported_without_silent_clipping(overrides):
    with pytest.raises(ValueError) as caught:
        GEN.generate(819, 7, **overrides)
    conflicts = getattr(caught.value, "incompatible_axes", ())
    assert set(overrides).issubset(conflicts), str(caught.value)


@pytest.mark.parametrize("axis,value", [
    ("palette_kind", "warm"), ("texture", "no_seed"),
    ("seed_position", "centered"), ("anchor_corner", True),
    ("asymmetry_force", True), ("not_an_axis", 42),
])
def test_retired_or_unknown_controls_fail_explicitly(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(73, 2, **{axis: value})


@pytest.mark.parametrize("axis", [
    "grid_h", "grid_w", "key_len", "palette_size", "zero_rings", "seed_r", "seed_c",
])
@pytest.mark.parametrize("value", [True, 3.0, "3"])
def test_integer_controls_reject_coercible_nonintegers(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(19, 0, **{axis: value})


@pytest.mark.parametrize("texture", ["no_key", "no_seed", "full_grid"])
def test_legacy_texture_metadata_cannot_disable_input_validation(texture):
    grid = valid_grid()
    grid[1][7] = 0
    assert GEN.self_check(grid, meta={"texture": texture})


@pytest.mark.parametrize("damage", ["gray_key", "seven_color_palette"])
def test_self_check_rejects_colors_outside_the_declared_key_palette(damage):
    grid = valid_grid()
    if damage == "gray_key":
        grid[0][2] = 5
    else:
        grid[0][:7] = [2, 1, 3, 4, 6, 7, 8]
    assert GEN.self_check(grid)


@pytest.mark.parametrize("width", [9, 10, 18])
def test_palette_zero_and_width_matrix_preserves_every_feasible_tuple(width):
    """Unpinned key length must satisfy the requested contents, including endpoints."""
    for palette_size in range(1, 7):
        for zero_rings in range(9):
            overrides = dict(grid_w=width, palette_size=palette_size, zero_rings=zero_rings)
            minimum_length = max(palette_size + zero_rings,
                                 zero_rings + 2 if zero_rings else 1)
            if minimum_length > min(width, 10):
                with pytest.raises(ValueError):
                    GEN.generate(531, 0, **overrides)
            else:
                grid = GEN.generate(531, 0, **overrides)
                assert_lawful(grid)
                observed = observed_axes(grid)
                assert {name: observed[name] for name in overrides} == overrides
