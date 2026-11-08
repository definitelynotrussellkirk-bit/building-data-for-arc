"""Focused regression tests for generator af9ade3c3e16."""
from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.af9ade3c3e16 import generator as gen
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)


def _canonical_inputs():
    return [row["input"] for row in canonical_pairs(gen.TASK_ID, root=ROOT)]


def _boxes(grid):
    return gen._frame_bboxes(grid)


def test_af9ade3c3e16_canonical_inputs_are_accepted():
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    assert [gen.self_check(grid) for grid in inputs] == [[] for _ in inputs]


def test_af9ade3c3e16_generated_scene_matches_canonical_grammar():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = gen.generate(seed, seed * 7 + 1, difficulty=band)
            observed = gen.observe_overrides(grid)
            boxes = _boxes(grid)
            assert gen.self_check(grid) == []
            assert set(value for row in grid for value in row) == {0, 2, 4, 6}
            assert 2 <= len(boxes) <= 5
            assert gen._strictly_nested(boxes)
            assert observed["n_frames"] == len(boxes)
            assert observed["rank"] == sum(value == 2 for row in grid for value in row)
            assert len(gen._component_cells(grid, 6)) == 1
            assert sum(value == 6 for row in grid for value in row) == 3


def test_af9ade3c3e16_exact_overrides_and_incompatibilities():
    cases = (
        {"grid_h": 12},
        {"grid_w": 12},
        {"n_frames": 5},
        {"rank": 5},
        {"grid_h": 24, "grid_w": 26, "n_frames": 5, "rank": 5},
        {"grid_h": 12, "grid_w": 12, "n_frames": 2, "rank": 2},
    )
    for case in cases:
        grid = gen.generate(91, 13, difficulty="hard", **case)
        observed = gen.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value
        assert gen.self_check(grid) == []

    for case in (
        {"n_frames": 2, "rank": 5},
        {"grid_h": 12, "n_frames": 5},
        {"grid_w": 12, "rank": 5},
    ):
        with pytest.raises(ValueError, match="(incompatible|cannot fit|exceeds)"):
            gen.generate(91, 13, difficulty="easy", **case)


def test_af9ade3c3e16_sequential_rank_schedule_exposes_multiple_answers():
    ranks = [
        gen.observe_overrides(gen.generate(44, index, difficulty="medium"))["rank"]
        for index in range(8)
    ]
    assert {1, 2}.issubset(ranks)
    assert len(set(ranks)) >= 3


def test_af9ade3c3e16_self_check_rejects_targeted_impostors():
    base = gen.generate(17, 9, difficulty="hard", n_frames=4, rank=3)
    assert gen.self_check(base) == []

    broken_border = copy.deepcopy(base)
    r0, c0, _, _ = _boxes(broken_border)[0]
    broken_border[r0][c0] = 0
    assert any("complete hollow rectangle" in msg for msg in gen.self_check(broken_border))

    marker_inside = copy.deepcopy(base)
    outside = next(
        (r, c)
        for r, row in enumerate(marker_inside)
        for c, value in enumerate(row)
        if value == 2
    )
    marker_inside[outside[0]][outside[1]] = 0
    outer = _boxes(marker_inside)[0]
    inside = next(
        (r, c)
        for r in range(outer[0] + 1, outer[2])
        for c in range(outer[1] + 1, outer[3])
        if marker_inside[r][c] == 0
    )
    marker_inside[inside[0]][inside[1]] = 2
    assert any("outside the outermost frame" in msg for msg in gen.self_check(marker_inside))

    foreign_palette = copy.deepcopy(base)
    foreign_palette[0][0] = 9
    assert any("palette" in msg for msg in gen.self_check(foreign_palette))

    split_distractor = copy.deepcopy(base)
    sixes = [(r, c) for r, row in enumerate(split_distractor) for c, v in enumerate(row) if v == 6]
    split_distractor[sixes[0][0]][sixes[0][1]] = 0
    replacement = next(
        (r, c)
        for r, row in enumerate(split_distractor)
        for c, value in enumerate(row)
        if value == 0 and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in sixes[1:])
    )
    split_distractor[replacement[0]][replacement[1]] = 6
    assert any("connected triomino" in msg for msg in gen.self_check(split_distractor))


def test_af9ade3c3e16_replay_freshness_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(1234, 56, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(1234, 56, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
