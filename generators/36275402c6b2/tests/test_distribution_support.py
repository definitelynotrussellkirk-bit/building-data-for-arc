"""Canonical geometry, lesson witnesses, and strict input validation."""
from __future__ import annotations

import importlib

import pytest

GEN = importlib.import_module("puzzle_generators.per_puzzle.36275402c6b2.generator")


def _border_sources(analysis):
    crop = analysis["crop"]
    last_row, last_col = len(crop) - 1, len(crop[0]) - 1
    return [
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value in analysis["sources"] and (r in (0, last_row) or c in (0, last_col))
    ]


def test_slots_include_side_legends_and_keep_one_black_cell_gap():
    bbox = (3, 4, 6, 7)
    slots = GEN._legend_slots(11, 13, bbox)
    assert slots == sorted(set(slots))
    assert (4, 0) in slots
    assert (4, 9) in slots
    for row, col in slots:
        assert 0 <= row < 11 and 0 <= col < 12
        assert row <= 1 or row >= 8 or col + 1 <= 2 or col >= 9


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_alternating_branch_supplies_border_and_side_witnesses(difficulty):
    for index in range(8):
        grid = GEN.generate(734, index, difficulty=difficulty)
        analysis = GEN._analysis_or_raise(grid)
        r1, _, r2, _ = analysis["bbox"]
        border = _border_sources(analysis)
        side = [pair for pair in analysis["pairs"] if r1 <= pair[2] <= r2]
        if index % 2:
            assert border, (difficulty, index, "missing border witness")
            assert side, (difficulty, index, "missing side legend witness")
        else:
            assert not border


@pytest.mark.parametrize("bad_color", [True, 1.5, "1", None])
def test_self_check_rejects_noninteger_colors_without_coercion(bad_color):
    grid = GEN.generate(91, 0, frame_color=1)
    r1, c1, _, _ = GEN._analysis_or_raise(grid)["bbox"]
    grid[r1][c1] = bad_color
    assert GEN.self_check(grid)


def test_three_demo_lessons_refute_declared_rivals_under_every_rotation():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(1203, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = pairs[:query_index] + pairs[query_index + 1:]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_new_witness_rivals_are_real_and_do_not_erase_frame_or_crop():
    grid = GEN.generate(73, 1, grid_h=11, grid_w=11, rect_h=7, rect_w=7, pair_count=3)
    official = GEN.rule_mirror(grid)
    for name in ("preserve_border_sources", "ignore_side_legends"):
        assert name in GEN.LESSON_COMPETITORS
        rival = GEN.LESSON_COMPETITORS[name](grid)
        assert len(rival) == len(official)
        assert all(len(a) == len(b) for a, b in zip(rival, official))
        assert rival != official
