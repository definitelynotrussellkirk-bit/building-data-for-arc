"""Focused validation regression: a marker must belong to only one bar."""
import pytest

from reviewer_support import find_root, load_selected_generator


MODULE, _, _ = load_selected_generator("96ebf3053dbe", root=find_root(__file__))


def shared_anchor_scene():
    # Two separate singleton bars touch the same center marker below the mirror.
    return [
        [7, 7, 7],
        [7, 5, 7],
        [7, 7, 7],
        [9, 9, 9],
        [7, 6, 7],
        [7, 2, 7],
        [7, 6, 7],
    ]


def test_shared_anchor_is_rejected_by_all_validation_entry_points():
    grid = shared_anchor_scene()
    assert any("exactly one 6-component" in error for error in MODULE.self_check(grid))
    for entry_point in (MODULE.rule_mirror, MODULE.observe_overrides):
        with pytest.raises(ValueError, match="exactly one 6-component"):
            entry_point(grid)


def test_separate_singleton_anchors_remain_valid():
    grid = shared_anchor_scene()
    grid[1][1] = grid[5][1] = 7
    grid[4][0] = grid[6][2] = 2
    grid[2][0] = grid[0][2] = 5
    assert MODULE.self_check(grid) == []
    assert MODULE.observe_overrides(grid) == {"scene_profile": "singleton_cycle"}
    output = MODULE.rule_mirror(grid)
    assert {(r, c) for r, row in enumerate(output) for c, cell in enumerate(row) if cell == 2} == {(4, 1), (6, 1)}
