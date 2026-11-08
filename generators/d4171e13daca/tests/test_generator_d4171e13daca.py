"""Focused semantic regressions for Nested Depth Paint generator d4171e13daca."""
from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root
from puzzle_generators.per_puzzle.d4171e13daca import generator as g


TASK_ID = "d4171e13daca"
BANDS = ("easy", "medium", "hard")


def _grid_from_boxes(h, w, boxes):
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for box in boxes:
        g._paint_frame(grid, box)
    return grid


def test_metadata_and_canonical_pairs_are_exact():
    assert g.VERSION == "3.1.0"
    assert g.RULE_HASH == "17513141906a"
    assert set(g.AXES) == {"frame_count", "layout_style", "outer_margin"}
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert g.self_check(source) == []
        assert g.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_boundary_override_is_observable_in_every_band():
    for band in BANDS:
        for count in (2, 5):
            for style in ("canonical", "offset"):
                for margin in ("edge", "inset"):
                    grid = g.generate(
                        914,
                        37,
                        difficulty=band,
                        frame_count=count,
                        layout_style=style,
                        outer_margin=margin,
                    )
                    expected = {
                        "frame_count": count,
                        "layout_style": style,
                        "outer_margin": margin,
                    }
                    assert g.observe_overrides(grid) == expected
                    assert g.self_check(
                        grid, difficulty=band, meta={"overrides": expected}
                    ) == []
                    assert len(grid) <= 30 and len(grid[0]) <= 30


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"frame_count": 1},
        {"layout_style": "diagonal"},
        {"outer_margin": "floating"},
    ],
)
def test_invalid_and_unknown_overrides_reject_loudly(kwargs):
    with pytest.raises(ValueError):
        g.generate(1, 1, **kwargs)


def test_self_check_rejects_four_targeted_impostors():
    lawful = _grid_from_boxes(11, 11, [(0, 0, 10, 10), (2, 2, 8, 8), (4, 4, 6, 6)])
    assert g.self_check(lawful) == []

    broken_corner = copy.deepcopy(lawful)
    broken_corner[0][0] = 0

    filled_interior = copy.deepcopy(lawful)
    filled_interior[5][5] = 1

    collapsed_moat = _grid_from_boxes(11, 11, [(0, 0, 10, 10), (1, 1, 9, 9), (3, 3, 7, 7)])

    non_nested_recombination = _grid_from_boxes(
        15, 15, [(0, 0, 14, 14), (2, 2, 12, 12), (5, 1, 7, 3)]
    )

    for impostor in (
        broken_corner,
        filled_interior,
        collapsed_moat,
        non_nested_recombination,
    ):
        assert g.self_check(impostor), impostor


def test_every_sliding_four_demo_window_is_identifiable():
    for band in BANDS:
        for start in range(8):
            demos = []
            for sample_index in range(start, start + g.EXAMPLES_NEEDED):
                grid = g.generate(44, sample_index, difficulty=band)
                demos.append({"input": grid, "output": g.rule_mirror(grid)})
            query_grid = g.generate(45, start + g.EXAMPLES_NEEDED, difficulty=band)
            assert g.lesson_identifiable(demos, {"input": query_grid}) == []


def test_every_five_pair_query_rotation_is_identifiable():
    """Any one of five consecutive labelled pairs may become the query."""
    for band in BANDS:
        for seed in (0, 4, 5, 20, 44, 914):
            for start in range(10):
                pairs = []
                for sample_index in range(start, start + g.EXAMPLES_NEEDED + 1):
                    grid = g.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": g.rule_mirror(grid)})

                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert g.lesson_identifiable(demos, {"input": query["input"]}) == []


def test_semantic_witnesses_fire_and_kill_their_declared_rivals():
    hits = {name: 0 for name in g.SEMANTIC_WITNESSES}
    for band in BANDS:
        for seed in range(80):
            grid = g.generate(seed + 3000, seed * 17 + 9, difficulty=band)
            expected = g.rule_mirror(grid)
            for name, predicate in g.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    hits[name] += 1
                    for rival_name in g.WITNESS_RIVALS[name]:
                        assert g.SEMANTIC_RIVALS[rival_name](grid) != expected
    assert all(count > 0 for count in hits.values()), hits


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    for band in BANDS:
        first = g.generate(771, 19, difficulty=band)
        second = g.generate(771, 19, difficulty=band)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        pristine = copy.deepcopy(first)
        first[0][0] = (first[0][0] + 1) % 10
        assert g.generate(771, 19, difficulty=band) == pristine
        assert random.getstate() == state
