"""Color-priority lesson-gate regressions; canonical labels are unchanged."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("color_priority_625b40fb6218", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
COLORS = (3, 4, 6, 7, 8, 9)
SEED = 11180556991150295210


def truth(grid):
    w = (len(grid[0]) - 1) // 2
    return [[2 if a and not b else 1 if b and not a else a
             for a, b in zip(row[:w], row[w + 1:])] for row in grid]


def favorite(grid, color):
    w = (len(grid[0]) - 1) // 2
    return [[2 if a and not b else 1 if b and not a else
             color if a and b and color in (a, b) else a
             for a, b in zip(row[:w], row[w + 1:])] for row in grid]


def pair(grid):
    return {"input": grid, "output": truth(grid)}


def scene(a, b, shift=0):
    grid = [[0] * 9 for _ in range(6)]
    for row in grid:
        row[4] = 5
    grid[0][0] = a
    grid[0][6] = b
    for row, col, color in ((1, 0, a), (1, 1, b), (1, 2, a)):
        grid[row][col] = grid[row][col + 5] = color
    grid[2 + shift][0] = a
    grid[2 + shift][5] = b
    assert GEN.self_check(grid) == []
    return grid


def test_retained_yellow_priority_lesson_is_rejected_without_query_label():
    rows = [pair(GEN.generate(SEED, i)) for i in range(6, 11)]
    assert all(GEN.self_check(row["input"]) == [] for row in rows)
    assert all(favorite(row["input"], 4) == row["output"] for row in rows[:4])
    output = rows[4]["output"]
    rival = favorite(rows[4]["input"], 4)
    differences = [(r, c, a, b) for r, (ar, br) in enumerate(zip(output, rival))
                   for c, (a, b) in enumerate(zip(ar, br)) if a != b]
    assert differences == [(1, 6, 3, 4)]
    reasons = GEN.lesson_identifiable(rows[:4], {"input": rows[4]["input"]})
    assert any("color_priority_4" in reason for reason in reasons)


@pytest.mark.parametrize("color", COLORS)
def test_each_foreground_color_priority_shortcut_is_detected(color):
    a, b = [candidate for candidate in COLORS if candidate != color][:2]
    demos = [pair(scene(a, b))]
    query = pair(scene(a, color, shift=1))
    assert favorite(demos[0]["input"], color) == demos[0]["output"]
    assert favorite(query["input"], color) != query["output"]
    reasons = GEN.lesson_identifiable(demos, {"input": query["input"]})
    assert any(f"color_priority_{color}" in reason for reason in reasons)


def test_query_equivalent_surviving_color_priority_is_allowed():
    demos = [pair(scene(3, 6))]
    query = pair(scene(3, 6, shift=1))
    assert favorite(demos[0]["input"], 4) == demos[0]["output"]
    assert favorite(query["input"], 4) == query["output"]
    assert GEN.lesson_identifiable(demos, {"input": query["input"]}) == []


def test_distinguishing_demonstration_repairs_the_retained_yellow_lesson():
    rows = [pair(GEN.generate(SEED, i)) for i in range(6, 11)]
    demos = rows[:4] + [pair(scene(3, 4))]
    assert favorite(demos[-1]["input"], 4) != demos[-1]["output"]
    reasons = GEN.lesson_identifiable(demos, {"input": rows[4]["input"]})
    assert not any("color_priority_4" in reason for reason in reasons)


def test_color_gate_keeps_labels_authoritative_and_inputs_unchanged():
    demos = [pair(scene(3, 6))]
    query = pair(scene(3, 4, shift=1))
    before = deepcopy((demos, query))
    GEN.lesson_identifiable(demos, query)
    assert (demos, query) == before
    demos[0]["output"][0][0] = 9
    reasons = GEN.lesson_identifiable(demos, query)
    assert any("demo 0 output disagrees" in reason for reason in reasons)


def test_new_color_rivals_preserve_existing_semantic_and_canonical_sets():
    assert set(GEN.SEMANTIC_RIVALS) == {"equal_overlap_only", "right_priority_overlap"}
    assert set(GEN.CANONICAL_SHORTCUTS) == set(GEN.SEMANTIC_RIVALS)
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS) | {
        f"color_priority_{color}" for color in COLORS
    }
