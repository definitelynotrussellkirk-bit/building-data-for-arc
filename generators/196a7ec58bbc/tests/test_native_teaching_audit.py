"""Focused regression tests for independent finite-rival audit semantics."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/audit_native.py"
SPEC = importlib.util.spec_from_file_location("quadrant_teaching_audit_tests", SOURCE)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_a_query_answer_cannot_eliminate_a_surviving_wrong_rule():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]], [[4]]],
        {"wrong": [[[1]], [[2]]]}, {"wrong": [[[8]], [[4]]]})
    assert result["surviving_rivals_after_demonstrations"] == ["wrong"]
    assert result["queries"][0]["surviving_disagreeing_rivals"] == ["wrong"]
    assert result["queries"][1]["identified_within_declared_rivals"]
    assert not result["ok"]


def test_demo_refutation_and_answer_equivalence_are_distinct():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]], [[4]]],
        {"refuted": [[[9]], [[2]]], "equivalent": [[[1]], [[2]]]},
        {"refuted": [[[8]], [[7]]], "equivalent": [[[3]], [[4]]]})
    assert result["refuted_rivals"] == ["refuted"]
    assert result["surviving_rivals_after_demonstrations"] == ["equivalent"]
    assert result["ok"]


def test_partial_labels_are_not_silently_accepted():
    with pytest.raises(ValueError, match="label count"):
        AUDIT.score_lesson([[[1]], [[2]]], [[[3]]], {"wrong": [[[1]]]}, {"wrong": [[[3]]]})


def test_demo_refuted_rival_does_not_need_query_execution():
    result = AUDIT.score_lesson([[[1]], [[2]]], [[[3]]], {"refuted": [[[9]], [[2]]]}, {})
    assert result["ok"]
    assert result["refuted_rivals"] == ["refuted"]


def test_surviving_rival_requires_query_execution():
    with pytest.raises(ValueError, match="every demo survivor"):
        AUDIT.score_lesson([[[1]], [[2]]], [[[3]]], {"survivor": [[[1]], [[2]]]}, {})


def test_connectivity_is_per_color_and_excludes_background():
    grid = [[1, 2, 0], [0, 1, 0], [0, 0, 1]]
    four = AUDIT.components(grid, 4)
    eight = AUDIT.components(grid, 8)
    assert [obj["size"] for obj in four] == [1, 1, 1, 1]
    assert [obj["size"] for obj in eight] == [3, 1]
    assert all(obj["color"] != 0 for obj in four)


def test_raw_crop_preserves_unrelated_interior_object():
    grid = [[1, 1, 1], [1, 2, 1], [1, 1, 0]]
    largest = max(AUDIT.components(grid), key=lambda obj: obj["size"])
    masked = AUDIT._extract(grid, largest)
    raw = AUDIT._extract(grid, largest, raw=True)
    assert masked[1][1] == 0
    assert raw[1][1] == 2
    assert AUDIT._tile(masked, "clockwise") != AUDIT._tile(raw, "clockwise")


def test_missing_top_right_anchor_refutes_reflection():
    grid = [[1, 0], [1, 1]]
    assert AUDIT._tile(grid, "clockwise") != AUDIT._tile(grid, "clockwise", "reflection")
    assert AUDIT._tile(grid, "clockwise") != AUDIT._tile(grid, "counterclockwise")


def test_unknown_rival_is_not_silently_canonical():
    with pytest.raises(ValueError, match="unknown rival"):
        AUDIT.python_rival([[1, 0], [1, 1]],
            {"source_mode": "whole", "handedness": "clockwise"}, "typo")


def _old_five_square_core(n, color):
    """Retain the former core's 21-cell, five-square selected-object profile."""
    grid = [[0] * n for _ in range(n)]
    removed = {(0, 4), (0, 3), (4, 1), (3, 3)}
    for row in range(5):
        for col in range(5):
            if (row, col) not in removed:
                grid[row + 2][col + 2] = color
    grid[0][0] = 9
    grid[5][5] = 9
    return grid


def test_fixed_five_crop_survives_old_cores_but_changes_small_query():
    setting = {"source_mode": "largest_component", "handedness": "clockwise"}
    demos = [_old_five_square_core(11, 1), _old_five_square_core(12, 2)]
    query = [[1, 1, 0], [1, 1, 1], [1, 0, 2]]
    demo_labels = [AUDIT.python_intended(grid, setting) for grid in demos]
    query_labels = [AUDIT.python_intended(query, setting)]
    rival_demos = [AUDIT.python_rival(grid, setting, "fixed_five_crop") for grid in demos]
    rival_queries = [AUDIT.python_rival(query, setting, "fixed_five_crop")]
    assert rival_demos == demo_labels
    assert len(query_labels[0]) == 6
    assert len(rival_queries[0]) == 10
    scored = AUDIT.score_lesson(demo_labels, query_labels,
        {"fixed_five_crop": rival_demos}, {"fixed_five_crop": rival_queries})
    assert not scored["ok"]
    assert scored["queries"][0]["surviving_disagreeing_rivals"] == ["fixed_five_crop"]


def test_fixed_five_crop_clips_large_component_at_bbox_origin():
    setting = {"source_mode": "largest_component", "handedness": "counterclockwise"}
    grid = [[1] * 7 for _ in range(7)]
    grid[0][0] = 0
    output = AUDIT.python_rival(grid, setting, "fixed_five_crop")
    assert len(output) == len(output[0]) == 10
    assert [row[:5] for row in output[:5]] == [row[:5] for row in grid[:5]]
    assert output != AUDIT.python_intended(grid, setting)
