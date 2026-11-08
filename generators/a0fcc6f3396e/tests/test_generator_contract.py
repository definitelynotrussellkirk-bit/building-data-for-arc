"""Behavioral regressions for the canonical corner-rectangle family.

These tests inspect the actual returned grids, not generator draw metadata.
Canonical labels come from the portable data helper; broad reference execution
is also covered by the retained battery and lesson census.
"""
from collections import Counter
from copy import deepcopy
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "a0fcc6f3396e"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def panel_dimensions(grid):
    result = []
    for start in (0, 7, 14):
        cells = [(r, c) for r in range(6) for c in range(start, start + 6)
                 if grid[r][c] == 2]
        result.append((max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
                       max(c for _, c in cells) - min(c for _, c in cells) + 1))
    return result


def independent_output(grid):
    shapes = panel_dimensions(grid)
    counts = Counter(shapes)
    assert sorted(counts.values()) == [1, 2]
    height, width = next(shape for shape in shapes if counts[shape] == 1)
    return [[8] * width for _ in range(height)]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_all_joint_exact_controls_are_observable(band):
    for panel in range(3):
        for height in range(2, 6):
            for width in range(2, 7):
                grid = GEN.generate(17, 11, difficulty=band, odd_panel=panel,
                                    rect_h=height, rect_w=width)
                shapes = panel_dimensions(grid)
                assert shapes[panel] == (height, width), (panel, height, width, shapes)
                assert shapes.count((height, width)) == 1
                assert GEN.self_check(grid) == []


@pytest.mark.parametrize("axis, bad", [
    ("odd_panel", -1), ("odd_panel", 3), ("odd_panel", True),
    ("odd_panel", "1"), ("odd_panel", 1.0),
    ("rect_h", 1), ("rect_h", 6), ("rect_h", False),
    ("rect_h", "3"), ("rect_h", 3.0),
    ("rect_w", 1), ("rect_w", 7), ("rect_w", True),
    ("rect_w", "4"), ("rect_w", 4.0),
    ("misspelled_axis", 2),
])
def test_invalid_and_unknown_controls_fail_visibly(axis, bad):
    with pytest.raises(ValueError):
        GEN.generate(17, 11, **{axis: bad})


def test_self_check_rejects_foreign_separator_color_inside_a_panel():
    grid = GEN.generate(31, 4)
    row, col = next((r, c) for r in range(6) for c in range(6)
                    if grid[r][c] == 0)
    grid[row][col] = 9
    assert GEN.self_check(grid), "A panel 9 is a real marker to Racket, not background"


def test_canonical_examples_remain_in_domain_and_match_rectangle_oracle():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert independent_output(pair["input"]) == pair["output"]


def test_retained_same_height_left_query_refutes_canonical_shortcuts():
    fixture = json.loads((ROOT / "generators" / TASK / "counterexamples" /
                         "same-height-odd-left.json").read_text())
    grid, expected = fixture["query"]["input"], fixture["query"]["output"]
    assert GEN.self_check(grid) == []
    assert independent_output(grid) == expected
    for name in ("always_panel_2", "height_else_panel_2"):
        rival = GEN.LESSON_COMPETITORS[name]
        assert all(rival(pair["input"]) == pair["output"]
                   for pair in canonical_pairs(TASK, root=ROOT))
        assert rival(grid) != expected


def test_rule_authority_and_lesson_size_are_explicit():
    assert GEN.RULE_HASH == "aadcb1545847"
    assert GEN.EXAMPLES_NEEDED == 8
    assert GEN.LESSON_SCHEDULE_PERIOD == 9


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_cyclic_start_retains_all_rival_witnesses_after_any_holdout(band):
    for seed in (0, 1, 17, 83, 2147483647):
        for start in range(9):
            pairs = [{"input": GEN.generate(seed, start + j, difficulty=band)}
                     for j in range(9)]
            for pair in pairs:
                pair["output"] = independent_output(pair["input"])
            for held_out in range(9):
                demos = [p for j, p in enumerate(pairs) if j != held_out]
                query = pairs[held_out]
                assert GEN.lesson_identifiable(demos, query) == [], (seed, start, held_out)
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(deepcopy(p["input"])) != p["output"] for p in demos), (
                        name, seed, start, held_out)


def test_all_twenty_odd_rectangle_sizes_and_three_positions_remain_supported():
    for band in ("easy", "medium", "hard"):
        sizes, positions = set(), set()
        for index in range(240):
            grid = GEN.generate(71, index, difficulty=band)
            shapes = panel_dimensions(grid)
            odd = next(p for p, shape in enumerate(shapes) if shapes.count(shape) == 1)
            sizes.add(shapes[odd])
            positions.add(odd)
        assert sizes == {(h, w) for h in range(2, 6) for w in range(2, 7)}
        assert positions == {0, 1, 2}


def test_generation_is_repeatable_and_does_not_reuse_mutable_grids():
    first = GEN.generate(9, 14, difficulty="hard")
    second = GEN.generate(9, 14, difficulty="hard")
    assert first == second
    first[0][0] = 7
    assert GEN.generate(9, 14, difficulty="hard") == second
