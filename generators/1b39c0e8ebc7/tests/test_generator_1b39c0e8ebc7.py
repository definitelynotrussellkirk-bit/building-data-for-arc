from __future__ import annotations

from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "1b39c0e8ebc7"
ROOT = find_root(__file__)


def load_generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def test_exact_controls_are_honored_and_malformed_overrides_fail_closed():
    g = load_generator()
    grid = g.generate(
        7,
        0,
        grid_h=12,
        grid_w=14,
        vector="(2,3)",
        matched_pairs=3,
        reverse_pairs=2,
        source_decoys=1,
        target_decoys=1,
    )
    info = g.analyze_scene(grid)
    assert (len(grid), len(grid[0])) == (12, 14)
    assert info["vector"] == (2, 3)
    assert len(info["forward_targets"]) == 3
    assert len(info["reverse_targets"]) == 2
    assert len(info["unmatched_sources"]) == 1
    assert len(info["unmatched_targets"]) == 1

    for kwargs in (
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 7.5},
        {"vector": "(0,0)"},
        {"matched_pairs": 1},
        {"reverse_pairs": -1},
    ):
        with pytest.raises((TypeError, ValueError)):
            g.generate(0, 0, **kwargs)


def test_ordinary_generation_breaks_recolor_all_targets_and_uses_the_vector():
    g = load_generator()
    seen_vectors = set()
    for seed in range(12):
        grid = g.generate(seed, seed % 4, difficulty="medium")
        assert g.self_check(grid, difficulty="medium") == []
        info = g.analyze_scene(grid)
        seen_vectors.add(info["vector"])
        assert len(info["forward_targets"]) >= 2
        assert len(info["reverse_targets"]) >= 1
        assert info["unmatched_sources"]
        assert info["unmatched_targets"]

        answer = g.apply_direction(grid, "forward")
        assert {cell for row in answer for cell in row} <= {0, 7}
        assert {
            (r, c)
            for r, row in enumerate(answer)
            for c, value in enumerate(row)
            if value == 7
        } == set(info["forward_targets"])

        recolor_all = [
            [7 if value == 4 else 0 for value in row]
            for row in grid
        ]
        assert recolor_all != answer

    assert len(seen_vectors) >= 4


def test_explicit_30_square_scene_is_dense_spread_and_exact():
    g = load_generator()
    grid = g.generate(
        101,
        3,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        vector="(-3,-2)",
        matched_pairs=12,
        reverse_pairs=11,
        source_decoys=4,
        target_decoys=4,
    )
    info = g.analyze_scene(grid)
    assert info["errors"] == []
    assert len(info["forward_targets"]) == 12
    assert len(info["reverse_targets"]) == 11
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(occupied) >= 56
    quadrants = [
        sum((r, c) in occupied for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert all(count >= 6 for count in quadrants)
