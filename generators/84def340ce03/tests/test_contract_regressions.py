"""Behavioral regressions for the canonical four-quadrant ring task.

These checks inspect returned pixels or use literal expected grids.  They do
not call production geometry helpers to calculate their expected answers.
Set GENERATOR_UNDER_TEST to replay the suite against a retained source file.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "84def340ce03"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO = find_root(__file__)
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("ring_contract_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def _canonical_records():
    with canonical_path(REPO).open() as stream:
        records = [row for line in stream if (row := json.loads(line))["task_id"] == TASK_ID]
    assert records, "the selected canonical task must be present"
    return records


RECORDS = _canonical_records()
CANONICAL_PAIRS = [
    pytest.param(pair, id=f"{record['source']}-{split}-{index}")
    for record in RECORDS
    for split in ("train", "test")
    for index, pair in enumerate(record[split])
]


@pytest.mark.parametrize("pair", CANONICAL_PAIRS)
def test_self_check_accepts_every_canonical_input(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original


@pytest.mark.parametrize("grid", [
    pytest.param([[0, 0], [0, 0]], id="zero-is-a-color"),
    pytest.param([[0, 1], [2, 3]], id="four-distinct-quadrants"),
    pytest.param(((0, 1), (2, 3)), id="tuple-grid-and-rows"),
    pytest.param([(0, 0), (0, 0)], id="tuple-rows"),
    pytest.param([[1, 2, 1, 2], [3, 4, 3, 4]], id="repeated-heterogeneous-blocks"),
    pytest.param([[1, 1, 2, 2], [1, 1, 2, 2]], id="uniform-blocks-remain-lawful"),
    pytest.param([[0] * 30 for _ in range(2)], id="wide-output-limit"),
    pytest.param([[9] * 2 for _ in range(30)], id="tall-output-limit"),
    pytest.param([[0] * 10 for _ in range(6)], id="sixty-input-cells"),
])
def test_self_check_accepts_the_rule_domain(grid):
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("grid", [
    pytest.param(None, id="none"),
    pytest.param(7, id="scalar"),
    pytest.param([], id="empty"),
    pytest.param([[]], id="empty-row"),
    pytest.param({"row": [1, 1]}, id="mapping"),
    pytest.param("11", id="string-grid"),
    pytest.param(["11", "11"], id="string-rows"),
    pytest.param([[1, 1], None], id="none-row"),
    pytest.param([[1, 1], 1], id="scalar-row"),
    pytest.param([[1, 1], [1]], id="ragged"),
    pytest.param([[1, 1], [1, 1], [1, 1]], id="odd-height"),
    pytest.param([[1, 1, 1], [1, 1, 1]], id="odd-width"),
    pytest.param([[True, True], [True, True]], id="bool-pixels"),
    pytest.param([[1.0, 1.0], [1.0, 1.0]], id="float-pixels"),
    pytest.param([["1", "1"], ["1", "1"]], id="string-pixels"),
    pytest.param([[None, None], [None, None]], id="none-pixels"),
    pytest.param([[[], []], [[], []]], id="unhashable-pixels"),
    pytest.param([[-1, -1], [-1, -1]], id="negative-color"),
    pytest.param([[10, 10], [10, 10]], id="color-above-nine"),
    pytest.param([[1] * 8 for _ in range(8)], id="output-would-be-32-square"),
    pytest.param([[1] * 32 for _ in range(2)], id="input-too-wide"),
    pytest.param([[1] * 2 for _ in range(32)], id="input-too-tall"),
])
def test_malformed_or_oversized_input_returns_diagnostics(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list)
    assert errors
    assert all(isinstance(error, str) and error for error in errors)


@pytest.fixture(scope="module", params=[None, "easy", "medium", "hard"])
def default_draws(request):
    band = request.param
    return band, [gen.generate(900 + index, index, difficulty=band) for index in range(20)]


def test_default_draws_cover_heterogeneous_quadrants(default_draws):
    _, grids = default_draws
    assert any(
        len({grid[row][col], grid[row][col + 1],
             grid[row + 1][col], grid[row + 1][col + 1]}) > 1
        for grid in grids
        for row in range(0, len(grid), 2)
        for col in range(0, len(grid[0]), 2)
    ), "default draws must teach the four distinct quadrant positions"


def test_default_draws_can_use_zero_as_an_ordinary_color(default_draws):
    _, grids = default_draws
    assert any(0 in row for grid in grids for row in grid)


def test_default_draws_are_valid_bounded_and_reproducible(default_draws):
    band, grids = default_draws
    for index, grid in enumerate(grids):
        height, width = len(grid), len(grid[0])
        assert height % 2 == width % 2 == 0
        assert 2 <= height <= 30 and 2 <= width <= 30
        assert height * width // 2 <= 30
        assert all(len(row) == width for row in grid)
        assert all(type(color) is int and 0 <= color <= 9 for row in grid for color in row)
        assert gen.self_check(grid) == []
        assert gen.generate(900 + index, index, difficulty=band) == grid


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, __unknown_axis__=1)


@pytest.mark.parametrize("key,value", [
    ("grid_size_kind", "16"),
    ("palette_kind", "warm"),
    ("ring_order_kind", "ascending"),
    ("anchor_corner", True),
    ("asymmetry_force", True),
    ("distinct_blocks", True),
    ("block_color_distribution", "even"),
])
def test_retired_misleading_controls_are_rejected(key, value):
    assert key not in gen.AXES
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("key,value", [
    ("grid_h", 1), ("grid_h", 3), ("grid_h", 31), ("grid_h", 2.0),
    ("grid_h", True), ("grid_h", "4"),
    ("grid_w", 0), ("grid_w", 5), ("grid_w", 32), ("grid_w", False),
    ("palette_size", 0), ("palette_size", 11), ("palette_size", 2.5),
    ("palette_size", True), ("palette_size", "2"),
    ("include_zero", 1), ("include_zero", 0), ("include_zero", "true"),
    ("texture", "not-a-mode"), ("texture", True),
    ("texture", "monochrome"), ("texture", "two_colors"),
    ("texture", "all_distinct"),
])
def test_invalid_override_values_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(17, 3, **{key: value})


@pytest.mark.parametrize("key", ["grid_h", "grid_w", "palette_size", "include_zero", "texture"])
def test_none_uses_the_shared_unset_override_convention(key):
    for index in (1, 2, 3):
        assert gen.generate(2, index, difficulty="hard", **{key: None}) == gen.generate(
            2, index, difficulty="hard"
        )


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3])
def test_unknown_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(17, 3, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,palette_size,include_zero", [
    (2, 2, 4, True),
    (2, 30, 10, True),
    (30, 2, 9, False),
    (6, 10, 1, True),
    (4, 14, 1, False),
])
def test_exact_dimensions_palette_and_zero_override_difficulty(
    band, height, width, palette_size, include_zero
):
    grid = gen.generate(73, 11, difficulty=band, grid_h=height, grid_w=width,
                        palette_size=palette_size, include_zero=include_zero,
                        texture="independent")
    assert (len(grid), len(grid[0])) == (height, width)
    colors = {color for row in grid for color in row}
    assert len(colors) == palette_size
    assert (0 in colors) is include_zero
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["grid_h"] == height
    assert observed["grid_w"] == width
    assert observed["palette_size"] == palette_size
    assert observed["include_zero"] is include_zero


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("key,value", [
    ("grid_h", 30), ("grid_w", 30), ("palette_size", 1),
    ("palette_size", 10), ("include_zero", False),
])
def test_single_axis_boundaries_choose_feasible_other_axes(band, key, value):
    grid = gen.generate(21, 7, difficulty=band, **{key: value})
    colors = {color for row in grid for color in row}
    actual = {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "palette_size": len(colors), "include_zero": 0 in colors,
    }
    assert actual[key] == value
    assert gen.self_check(grid) == []
    assert len(grid) * len(grid[0]) <= 60


@pytest.mark.parametrize("options", [
    {"grid_h": 8, "grid_w": 8},
    {"grid_h": 2, "grid_w": 2, "palette_size": 5},
    {"palette_size": 10, "include_zero": False},
    {"palette_size": 1, "texture": "mixed_uniform"},
    {"grid_h": 2, "grid_w": 2, "texture": "repeat_tiles"},
    {"grid_h": 2, "grid_w": 2, "texture": "mixed_uniform"},
    {"grid_h": 2, "grid_w": 4, "texture": "contrast"},
    {"grid_h": 2, "grid_w": 2, "texture": "uniform_blocks"},
    {"grid_h": 2, "grid_w": 4, "texture": "uniform_blocks", "palette_size": 3},
])
def test_incompatible_requests_raise_structured_value_error(options):
    with pytest.raises(ValueError) as caught:
        gen.generate(0, 0, **options)
    axes = getattr(caught.value, "incompatible_axes", None)
    assert isinstance(axes, tuple)
    assert len(axes) >= 2
    assert set(axes) <= set(gen.AXES)


@pytest.mark.parametrize("grid,expected", [
    ([[0, 1, 0, 1], [2, 2, 2, 2]],
     {"grid_h": 2, "grid_w": 4, "palette_size": 3, "include_zero": True}),
    ([[3, 1], [2, 2], [3, 1], [2, 2]],
     {"grid_h": 4, "grid_w": 2, "palette_size": 3, "include_zero": False}),
])
def test_observer_measures_hand_written_pixels(grid, expected):
    observed = gen.observe_overrides(grid)
    assert {key: observed[key] for key in expected} == expected


@pytest.mark.parametrize("texture", ["repeat_tiles", "mixed_uniform", "contrast", "uniform_blocks"])
@pytest.mark.parametrize("seed", [0, 17, 99])
def test_texture_modes_have_their_advertised_visible_structure(texture, seed):
    grid = gen.generate(seed, 3, grid_h=6, grid_w=6, palette_size=4,
                        include_zero=True, texture=texture)
    assert (len(grid), len(grid[0])) == (6, 6)
    colors = {color for row in grid for color in row}
    assert len(colors) == 4 and 0 in colors
    assert gen.self_check(grid) == []
    tiles = {
        (row // 2, col // 2): (grid[row][col], grid[row][col + 1],
                             grid[row + 1][col], grid[row + 1][col + 1])
        for row in range(0, 6, 2)
        for col in range(0, 6, 2)
    }
    uniform = [tile for tile in tiles.values() if len(set(tile)) == 1]
    heterogeneous = [tile for tile in tiles.values() if len(set(tile)) > 1]
    if texture == "uniform_blocks":
        assert len(uniform) == 9
    if texture in {"mixed_uniform", "contrast"}:
        assert uniform and heterogeneous
    if texture in {"repeat_tiles", "contrast"}:
        # Consecutive row-major tiles become adjacent output rings, including
        # a pair crossing an input tile-row boundary (the seed-0 regression).
        sequence = list(tiles.values())
        assert any(
            len(set(left)) > 1 and left == right
            for left, right in zip(sequence, sequence[1:])
        )


@pytest.fixture(scope="module")
def canonical_reference():
    from arcpuzzles import Catalog

    grids = [
        [[1, 2, 5, 6], [3, 4, 7, 8]],
        [[1, 2], [3, 4], [5, 6], [7, 8]],
        [[0] * 30 for _ in range(2)],
        [[0, 1, 4, 5], [2, 3, 6, 7], [8, 9, 1, 2], [3, 4, 5, 6]],
    ]
    record = Catalog(REPO).apply(TASK_ID, grids, timeout=60)
    assert record["rule_hash_matches_catalog"]
    assert all(result["error"] is None for result in record["results"])
    outputs = {
        tuple(map(tuple, grid)): result["output"]
        for grid, result in zip(grids, record["results"], strict=True)
    }
    return lambda grid: outputs[tuple(map(tuple, grid))]


@pytest.mark.parametrize("grid", [
    pytest.param([[1, 2, 5, 6], [3, 4, 7, 8]], id="horizontal-block-sequence"),
    pytest.param([[1, 2], [3, 4], [5, 6], [7, 8]], id="vertical-block-sequence"),
])
def test_reference_preserves_quadrants_and_reads_blocks_from_the_center(grid, canonical_reference):
    assert canonical_reference(grid) == [
        [5, 5, 6, 6],
        [5, 1, 2, 6],
        [7, 3, 4, 8],
        [7, 7, 8, 8],
    ]


def test_reference_accepts_the_maximum_output_size(canonical_reference):
    output = canonical_reference([[0] * 30 for _ in range(2)])
    assert len(output) == 30
    assert all(row == [0] * 30 for row in output)


def test_reference_uses_row_major_block_order_and_preserves_zero(canonical_reference):
    grid = [[0, 1, 4, 5], [2, 3, 6, 7], [8, 9, 1, 2], [3, 4, 5, 6]]
    assert canonical_reference(grid) == [
        [1, 1, 1, 1, 2, 2, 2, 2],
        [1, 8, 8, 8, 9, 9, 9, 2],
        [1, 8, 4, 4, 5, 5, 9, 2],
        [1, 8, 4, 0, 1, 5, 9, 2],
        [5, 3, 6, 2, 3, 7, 4, 6],
        [5, 3, 6, 6, 7, 7, 4, 6],
        [5, 3, 3, 3, 4, 4, 4, 6],
        [5, 5, 5, 5, 6, 6, 6, 6],
    ]
