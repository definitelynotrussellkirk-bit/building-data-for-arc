"""Public rotation-contract regressions; canonical answers are authoring data.

Run from WORK with ``python3 run_with_racket.py python3 -m pytest -q
generators/148acacd84d9/tests/test_rotation_contract.py``. These tests must not
be consulted during a blind solve. Geometry is checked independently of the
generator's private sampling and transform helpers.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "148acacd84d9"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("rotation_contract_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def transform(grid, name):
    """Scatter each cell using explicit coordinate maps for the eight D4 rules."""
    height, width = len(grid), len(grid[0])
    swapped = name in {"clockwise", "counterclockwise", "transpose", "antitranspose"}
    out = [[0] * (height if swapped else width)
           for _ in range(width if swapped else height)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            destinations = {
                "identity": (r, c),
                "clockwise": (c, height - 1 - r),
                "halfturn": (height - 1 - r, width - 1 - c),
                "counterclockwise": (width - 1 - c, r),
                "flip_lr": (r, width - 1 - c),
                "flip_ud": (height - 1 - r, c),
                "transpose": (c, r),
                "antitranspose": (width - 1 - c, height - 1 - r),
            }
            nr, nc = destinations[name]
            out[nr][nc] = color
    return out


RIVALS = ("identity", "halfturn", "counterclockwise", "flip_lr", "flip_ud",
          "transpose", "antitranspose")
CROP_PLACEMENTS = [(vertical, horizontal) for vertical in ("start", "center", "center_ceil", "end")
                   for horizontal in ("start", "center", "center_ceil", "end")]


def crop_repadding(grid, vertical, horizontal):
    """Rotate the foreground bounding box and paste it into the normal canvas."""
    height, width = len(grid), len(grid[0])
    positions = [(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != 0]
    output = [[0] * height for _ in range(width)]
    if not positions:
        return output
    r0, r1 = min(r for r, _ in positions), max(r for r, _ in positions)
    c0, c1 = min(c for _, c in positions), max(c for _, c in positions)
    cropped_height, cropped_width = r1 - r0 + 1, c1 - c0 + 1
    spare_rows, spare_columns = width - cropped_width, height - cropped_height
    row_offset = {"start": 0, "center": spare_rows // 2,
                  "center_ceil": (spare_rows + 1) // 2, "end": spare_rows}[vertical]
    column_offset = {"start": 0, "center": spare_columns // 2,
                     "center_ceil": (spare_columns + 1) // 2, "end": spare_columns}[horizontal]
    for r, c in positions:
        output[c - c0 + row_offset][r1 - r + column_offset] = grid[r][c]
    return output


def stats(grid):
    cells = [color for row in grid for color in row]
    return len(grid), len(grid[0]), sum(color != 0 for color in cells), set(cells)


def assert_normal(grid):
    height, width, marks, colors = stats(grid)
    assert 4 <= height <= 12 and 4 <= width <= 12
    assert 3 <= marks <= 12
    assert 0 in colors and 3 <= len(colors) <= 10
    assert all(type(color) is int and 0 <= color <= 9 for row in grid for color in row)
    assert gen.self_check(grid) == []
    expected = transform(grid, "clockwise")
    assert all(transform(grid, rival) != expected for rival in RIVALS)


def test_each_control_changes_the_observed_grid_property_exactly():
    baseline = {"grid_h": 4, "grid_w": 12, "mark_count": 9, "palette_size": 10}
    cases = [baseline] + [{**baseline, key: value} for key, value in (
        ("grid_h", 12), ("grid_w", 4), ("mark_count", 12), ("palette_size", 3))]
    observed = []
    for overrides in cases:
        grid = gen.generate(619, 0, **overrides)
        assert_normal(grid)
        height, width, marks, colors = stats(grid)
        properties = (height, width, marks, len(colors))
        assert properties == tuple(overrides.values())
        observed.append(properties)
    assert len(set(observed)) == len(cases)


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=[f"{p['split']}-{p['pair_index']}" for p in CANONICAL])
def test_original_canonical_inputs_are_normal_and_clockwise(pair):
    assert gen.self_check(pair["input"]) == []
    assert transform(pair["input"], "clockwise") == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_square_profiles_and_d4_witnesses_are_present_in_every_band(band):
    small_sizes, large_sizes = set(), set()
    for index in range(36):
        grid = gen.generate(1203, index, difficulty=band)
        assert grid == gen.generate(1203, index, difficulty=band)
        assert_normal(grid)
        height, width, marks, colors = stats(grid)
        assert height == width
        if index % 2 == 0:
            assert height in {4, 5, 6}
            assert marks in {3, 4, 5} and len(colors) in {4, 5}
            small_sizes.add(height)
        else:
            assert 7 <= height <= 12
            large_sizes.add(height)
    assert small_sizes == {4, 5, 6}
    assert len(large_sizes) >= 2


@pytest.mark.parametrize("overrides", [
    {"grid_h": 4, "grid_w": 12, "mark_count": 3, "palette_size": 3},
    {"grid_h": 12, "grid_w": 4, "mark_count": 12, "palette_size": 10},
    {"grid_h": 4, "grid_w": 4, "mark_count": 12, "palette_size": 3},
    {"grid_h": 12, "grid_w": 12, "mark_count": 9, "palette_size": 10},
])
def test_joint_axis_overrides_are_exact_in_every_difficulty(overrides):
    for band in (None, "easy", "medium", "hard"):
        for index in (0, 1, 11):
            grid = gen.generate(731, index, difficulty=band, **overrides)
            assert_normal(grid)
            height, width, marks, colors = stats(grid)
            assert (height, width, marks, len(colors)) == tuple(overrides.values())


def test_single_palette_override_selects_enough_marks_without_coercion():
    for index in range(12):
        grid = gen.generate(819, index, difficulty="easy", palette_size=10)
        assert_normal(grid)
        assert len(stats(grid)[3]) == 10 and stats(grid)[2] >= 9


@pytest.mark.parametrize("marks,palette", [(3, 5), (8, 10)])
def test_impossible_joint_palette_is_rejected_with_declared_axes(marks, palette):
    with pytest.raises(ValueError) as caught:
        gen.generate(82, 0, mark_count=marks, palette_size=palette)
    axes = getattr(caught.value, "incompatible_axes", None)
    documented = getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", ())
    assert (axes is not None and set(axes) == {"mark_count", "palette_size"}) or any(
        isinstance(case, (tuple, list)) and set(case) == {"mark_count", "palette_size"}
        for case in documented)


@pytest.mark.parametrize("overrides", [
    {"size": 5}, {"palette_kind": "warm"}, {"anchor_corner": True},
    {"asymmetry_force": True}, {"position_bias": "center"}, {"unknown_axis": 1},
    {"texture": "warm"}, {"texture": "typo"},
    {"grid_h": 3}, {"grid_w": 13}, {"mark_count": 2}, {"mark_count": 13},
    {"palette_size": 2}, {"palette_size": 11},
    {"grid_h": True}, {"grid_w": 4.0}, {"mark_count": "3"},
    {"palette_size": False}, {"palette_size": None},
])
def test_invalid_unknown_and_removed_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(931, 1, **overrides)


@pytest.mark.parametrize("grid", [
    None, 5, "0000", {}, [], [[]], [[0], [0, 1]], [[0], None],
])
def test_self_check_is_total_for_malformed_grids(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("cell", [True, 1.0, "1", None, -1, 10])
def test_self_check_rejects_bad_cell_types_on_an_otherwise_lawful_grid(cell):
    # Preserve lawful shape, sparse mark count, palette and asymmetry so a
    # different grammar failure cannot mask acceptance of bool/float cells.
    grid = [[5, 0, 0, 0], [0, 0, 9, 0], [0, 0, 0, 0], [0, 2, 0, 0]]
    assert gen.self_check(grid) == []
    grid[2][3] = cell
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("texture", ["empty_grid", "single_mark", "full_grid"])
def test_degenerates_remain_diagnostic_fixtures_outside_normal_grammar(texture):
    assert texture in gen.DEGENERATE_TEXTURES
    grid = gen.generate(919, 1, texture=texture)
    assert gen.self_check(grid)
    height, width, marks, colors = stats(grid)
    assert (height, width) == (5, 5)
    assert marks == {"empty_grid": 0, "single_mark": 1, "full_grid": 25}[texture]
    assert colors == {"empty_grid": {0}, "single_mark": {0, 3}, "full_grid": {3}}[texture]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_each_three_demo_lesson_and_all_four_query_exchanges_refute_competitors(band):
    rivals = getattr(gen, "LESSON_COMPETITORS", {})
    assert "canonical_sizes_only" in rivals
    assert callable(getattr(gen, "lesson_identifiable", None))
    for start in range(4):
        pairs = [{"input": gen.generate(4109, i, difficulty=band)}
                 for i in range(start, start + 4)]
        for pair in pairs:
            pair["output"] = transform(pair["input"], "clockwise")
        strong_crop_witnesses = sum(
            all(crop_repadding(pair["input"], vertical, horizontal) != pair["output"]
                for vertical, horizontal in CROP_PLACEMENTS) for pair in pairs)
        assert strong_crop_witnesses >= 2, (band, start, strong_crop_witnesses)
        # This public rival agrees on the original family and fails on its extension.
        for pair in pairs:
            height, width, _, _ = stats(pair["input"])
            expected = pair["output"] if height == width and height in (4, 5, 6) else pair["input"]
            assert rivals["canonical_sizes_only"](pair["input"]) == expected
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []
            assert any(max(stats(pair["input"])[:2]) > 6 for pair in demos)
            for name, rival in rivals.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
            for vertical, horizontal in CROP_PLACEMENTS:
                assert any(crop_repadding(pair["input"], vertical, horizontal) != pair["output"]
                           for pair in demos), (band, start, query_index, vertical, horizontal)


def test_actual_canonical_shortcut_declarations_fit_all_four_originals():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert shortcuts
    for name, rival in shortcuts.items():
        assert callable(rival)
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL), name
    for vertical, horizontal in CROP_PLACEMENTS:
        name = f"crop_{vertical}_{horizontal}"
        if name in shortcuts:
            assert all(shortcuts[name](pair["input"]) ==
                       crop_repadding(pair["input"], vertical, horizontal)
                       for pair in CANONICAL), name


def test_independent_crop_family_has_eight_actual_canonical_fits():
    canonical_fits = [(vertical, horizontal) for vertical, horizontal in CROP_PLACEMENTS
                      if all(crop_repadding(pair["input"], vertical, horizontal) == pair["output"]
                             for pair in CANONICAL)]
    assert len(canonical_fits) == 8
    assert {vertical for vertical, _ in canonical_fits} == {"start", "center"}


def test_declared_crop_rivals_match_independent_odd_gap_centering():
    # Rotated bounding box has three spare columns and five spare rows, so the
    # two center conventions select different offsets in both dimensions.
    grid = [[0] * 9 for _ in range(7)]
    for r, c, color in ((1, 2, 2), (2, 5, 3), (4, 3, 4)):
        grid[r][c] = color
    assert gen.self_check(grid) == []
    rivals = getattr(gen, "LESSON_COMPETITORS", {})
    expected_names = {f"crop_{vertical}_{horizontal}" for vertical, horizontal in CROP_PLACEMENTS}
    assert expected_names <= set(rivals), expected_names - set(rivals)
    for vertical, horizontal in CROP_PLACEMENTS:
        name = f"crop_{vertical}_{horizontal}"
        assert rivals[name](grid) == crop_repadding(grid, vertical, horizontal), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_retained_crop_shortcut_lesson_is_reported_as_unidentifiable(band):
    retained = json.loads((SOURCE.parent / "counterexamples/crop_repadding.json").read_text())
    window = next(item for item in retained["windows"] if item["difficulty"] == band)
    demos, query = window["demos"], window["query"]
    assert all(gen.self_check(pair["input"]) == [] for pair in demos + [query])
    assert all(crop_repadding(pair["input"], "start", "start") == pair["output"]
               for pair in retained["canonical"] + demos)
    assert crop_repadding(query["input"], "start", "start") != query["output"]
    reasons = gen.lesson_identifiable(demos, query)
    assert reasons, "crop-and-repad fits every demonstration but changes the Racket query answer"
    assert any("crop" in reason for reason in reasons)


@pytest.mark.skipif(shutil.which("racket") is None and not os.environ.get("RACKET_PATH"),
                    reason="Racket reference runtime required")
def test_racket_reference_labels_originals_and_rectangular_hand_fixture():
    from arcpuzzles import Catalog

    rectangle = [[0, 0, 2, 0, 0, 0], [5, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 7, 0], [0, 9, 0, 0, 0, 0]]
    expected_rectangle = [[0, 0, 5, 0], [9, 0, 0, 0], [0, 0, 0, 2],
                          [0, 0, 0, 0], [0, 7, 0, 0], [0, 0, 0, 0]]
    assert transform(rectangle, "clockwise") == expected_rectangle
    assert gen.self_check(rectangle) == []
    record = Catalog(ROOT).apply(TASK_ID, [p["input"] for p in CANONICAL] + [rectangle])
    assert record["rule_hash_matches_catalog"]
    assert all(result["error"] is None for result in record["results"])
    assert [result["output"] for result in record["results"]] == [
        p["output"] for p in CANONICAL] + [expected_rectangle]
