from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest
from arc_repl.parser import parse_all

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "959992fc8fa9"
ROOT = find_root(__file__)
gen, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_rows():
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _foreground(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def test_generator_959992fc8fa9_accepts_all_canonical_pairs_and_matches_rule():
    pairs = []
    for row in _canonical_rows():
        pairs.extend(row.get("train", []))
        pairs.extend(row.get("test", []))
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generator_959992fc8fa9_exact_axes_and_boundaries_are_observable():
    cases = (
        dict(grid_h=6, grid_w=18, n_pixels=2, color_pattern="all_distinct", anchor_corner=True),
        dict(grid_h=18, grid_w=6, n_pixels=5, color_pattern="one_repeat", anchor_corner=False),
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(700 + index, 900 + index, difficulty="easy", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="requires n_pixels >= 3"):
        gen.generate(1, 1, n_pixels=2, color_pattern="one_repeat")


def test_generator_959992fc8fa9_repeated_color_branch_rebuts_all_crossings_red():
    grid = gen.generate(
        33,
        17,
        difficulty="hard",
        n_pixels=5,
        color_pattern="one_repeat",
        anchor_corner=False,
    )
    output = gen.rule_mirror(grid)
    pixels = _foreground(grid)
    by_color = {}
    for row, col, color in pixels:
        by_color.setdefault(color, []).append((row, col))
    repeated = next(color for color, cells in by_color.items() if len(cells) == 2)
    (r1, c1), (r2, c2) = by_color[repeated]
    assert output[r1][c2] == repeated
    assert output[r2][c1] == repeated

    other_row, other_col, other_color = next(
        pixel for pixel in pixels if pixel[2] != repeated
    )
    assert output[r1][other_col] == 2
    assert output[other_row][c1] == 2
    assert other_color != repeated


def test_generator_959992fc8fa9_self_check_rejects_targeted_impostors():
    valid = gen.generate(44, 12, n_pixels=4, color_pattern="one_repeat")
    h, w = len(valid), len(valid[0])
    pixels = _foreground(valid)

    impostors = []
    impostors.append([[0] * w for _ in range(h)])

    singleton = [[0] * w for _ in range(h)]
    singleton[1][1] = 3
    impostors.append(singleton)

    red_input = copy.deepcopy(valid)
    red_input[pixels[0][0]][pixels[0][1]] = 2
    impostors.append(red_input)

    shared_row = [[0] * w for _ in range(h)]
    shared_row[1][1] = 3
    shared_row[1][w - 2] = 4
    impostors.append(shared_row)

    solid = [[0] * w for _ in range(h)]
    solid[1][1] = solid[1][2] = solid[2][1] = solid[2][2] = 3
    impostors.append(solid)

    all_one_color = copy.deepcopy(valid)
    for row, col, _ in pixels:
        all_one_color[row][col] = 3
    impostors.append(all_one_color)

    too_many_corners = [[0] * w for _ in range(h)]
    too_many_corners[0][0] = 3
    too_many_corners[h - 1][w - 1] = 4
    impostors.append(too_many_corners)

    triple_repeat = copy.deepcopy(valid)
    for row, col, _ in pixels[:3]:
        triple_repeat[row][col] = 3
    for row, col, _ in pixels[3:]:
        triple_repeat[row][col] = 4
    impostors.append(triple_repeat)

    assert len(impostors) >= 4
    for grid in impostors:
        assert gen.self_check(grid), grid


def test_generator_959992fc8fa9_is_deterministic_fresh_and_rng_pure():
    random.seed(987654321)
    before = random.getstate()
    first = gen.generate(123, 456, difficulty="medium")
    after = random.getstate()
    second = gen.generate(123, 456, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_generator_959992fc8fa9_rule_authorities_are_semantically_synced():
    canonical = _canonical_rows()[0]["program_solution"]
    canonical_ast = parse_all(canonical)
    assert gen.RULE_HASH == "1d9c05259f79"
    for relpath in (
        "solutions/training/45bbe264__959992fc8fa9.json",
        "solutions/augmented/45bbe264__2d6748a7f610.json",
    ):
        candidates = (ROOT / "data/base" / relpath, ROOT / "shared/data/base" / relpath)
        source = next((candidate for candidate in candidates if candidate.is_file()), None)
        assert source is not None, relpath
        data = json.loads(source.read_text(encoding="utf-8"))
        target = data["racket_target"]
        assert target["canonicalization_status"] == "exact_canonical_source"
        # The authority export minifies whitespace, but its two source fields
        # must agree exactly and parse to the canonical program structure.
        assert target["raw_code"] == target["target_code"]
        assert parse_all(target["raw_code"]) == canonical_ast
