"""Query-specific lesson-hook regressions for the zone compression task.

The five small pairs below have hand-derived labels.  Holding out an internal
pair removes a mask name without removing the scan-order counterexamples.
"""
from __future__ import annotations

import copy

import pytest

from reviewer_support import find_root, load_selected_generator


gen, _, _ = load_selected_generator("9df67b512dad", root=find_root(__file__))

# Known occupied cells in each zone of the literal 5x7 fixture.
_ZONE_MARKERS = (
    ((0, 0),),
    ((0, 2), (0, 4)),
    ((0, 6),),
    ((1, 0), (3, 0)),
    ((1, 2), (3, 4)),
    ((1, 6), (3, 6)),
    ((4, 0),),
    ((4, 2), (4, 4)),
    ((4, 6),),
)
_EMPTY_MASKS = ((0, 8), (1, 7), (3, 5), (2, 4, 6), (0, 8))


def _pair(empty_zones, *, multicolor=True):
    # Every non-corner zone starts with 2 and ends with 7.
    grid = [
        [2, 0, 2, 0, 7, 0, 2],
        [2, 0, 2, 0, 0, 0, 2],
        [0, 0, 0, 0, 0, 0, 0],
        [7, 0, 0, 0, 7, 0, 7],
        [2, 0, 2, 0, 7, 0, 2],
    ]
    output = [[2, 7, 2], [7, 7, 7], [2, 7, 2]]
    for zone in empty_zones:
        for row, col in _ZONE_MARKERS[zone]:
            grid[row][col] = 0
        output[zone // 3][zone % 3] = 0
    if not multicolor:
        grid = [[2 if value == 7 else value for value in row] for row in grid]
        output = [[2 if value == 7 else value for value in row] for row in output]
    return {"input": grid, "output": output}


@pytest.mark.parametrize("query_index", range(5))
def test_query_rotation_does_not_require_every_mask_in_demonstrations(query_index):
    pairs = [_pair(empty) for empty in _EMPTY_MASKS]
    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
    query = pairs[query_index]
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
    for rival in gen.LESSON_COMPETITORS.values():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)
    assert gen.lesson_identifiable(demos, query) == []


def test_answer_equivalent_survivors_do_not_make_query_ambiguous():
    pairs = [_pair(empty, multicolor=False) for empty in _EMPTY_MASKS]
    for rival in gen.LESSON_COMPETITORS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_surviving_rivals_that_change_query_are_still_rejected():
    demos = [_pair(empty, multicolor=False) for empty in _EMPTY_MASKS[:4]]
    query = _pair(_EMPTY_MASKS[4])
    reasons = gen.lesson_identifiable(demos, query)
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in demos)
        assert rival(query["input"]) != query["output"]
        assert any(name in reason for reason in reasons), reasons


def test_lawful_unscheduled_mask_can_supply_semantic_counterexample():
    demos = [_pair(empty) for empty in ((0, 1, 8), (3, 5), (2, 4, 6), (0, 8))]
    query = _pair((1, 7))
    assert gen.self_check(demos[0]["input"]) == []
    assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("target", ("demo", "query"))
@pytest.mark.parametrize("defect", ("missing_input", "wrong_output", "unlawful_input"))
def test_pair_validation_is_preserved(target, defect):
    pairs = [_pair(empty) for empty in _EMPTY_MASKS]
    demos, query = pairs[:4], pairs[4]
    pair = demos[0] if target == "demo" else query
    if defect == "missing_input":
        del pair["input"]
    elif defect == "wrong_output":
        pair["output"][0][0] = 9
    else:
        pair["input"][0][0] = 10
    before = copy.deepcopy((demos, query))
    assert gen.lesson_identifiable(demos, query)
    assert (demos, query) == before


def test_insufficient_demonstrations_are_rejected():
    pairs = [_pair(empty) for empty in _EMPTY_MASKS]
    assert gen.lesson_identifiable(pairs[:3], pairs[4])
