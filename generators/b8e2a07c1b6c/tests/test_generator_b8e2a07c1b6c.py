from __future__ import annotations

import copy
import importlib
import random

import pytest

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.b8e2a07c1b6c.generator"
)

DIRECTIONS = (
    "right", "left", "down", "up",
    "down_right", "down_left", "up_right", "up_left",
)


def _head_and_forward(grid):
    obs = GEN.observe_overrides(grid)
    head = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    delta = {
        "right": (0, 1), "left": (0, -1),
        "down": (1, 0), "up": (-1, 0),
        "down_right": (1, 1), "down_left": (1, -1),
        "up_right": (-1, 1), "up_left": (-1, -1),
    }[obs["arrow_direction"]]
    return head, delta


def test_all_eight_direction_overrides_are_realized():
    for index, direction in enumerate(DIRECTIONS):
        grid = GEN.generate(
            700 + index,
            900 + index,
            difficulty="hard",
            grid_h=16,
            grid_w=17,
            shape_h=11,
            shape_w=12,
            trail_len=4,
            arrow_direction=direction,
        )
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        assert observed == {
            "grid_h": 16,
            "grid_w": 17,
            "arrow_direction": direction,
            "shape_h": 11,
            "shape_w": 12,
            "trail_len": 4,
        }


def test_boundary_overrides_and_replay_contract():
    cases = [
        dict(grid_h=12, grid_w=18, shape_h=5, shape_w=16,
             trail_len=6, arrow_direction="right"),
        dict(grid_h=18, grid_w=12, shape_h=16, shape_w=5,
             trail_len=6, arrow_direction="down"),
        dict(grid_h=12, grid_w=12, shape_h=10, shape_w=10,
             trail_len=1, arrow_direction="up_left"),
    ]
    before_state = random.getstate()
    for i, overrides in enumerate(cases):
        first = GEN.generate(100 + i, 200 + i, difficulty="medium", **overrides)
        second = GEN.generate(100 + i, 200 + i, difficulty="medium", **overrides)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert GEN.observe_overrides(first) == overrides
        assert GEN.self_check(first) == []
    assert random.getstate() == before_state


def test_self_check_rejects_targeted_impostors():
    grid = GEN.generate(
        1234, 5678, difficulty="hard",
        grid_h=16, grid_w=16, shape_h=11, shape_w=11,
        trail_len=4, arrow_direction="down_right",
    )
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    (hr, hc), (dr, dc) = _head_and_forward(grid)

    no_head = copy.deepcopy(grid)
    no_head[hr][hc] = 7
    assert GEN.self_check(no_head)

    broken_tail = copy.deepcopy(grid)
    broken_tail[hr - dr][hc - dc] = 7
    assert GEN.self_check(broken_tail)

    stray_tail = copy.deepcopy(grid)
    stray_tail[0][0] = 6
    assert GEN.self_check(stray_tail)

    punched_body = copy.deepcopy(grid)
    r0 = min(r for r, row in enumerate(grid) for c, v in enumerate(row) if v in {2, 6, 7})
    c0 = min(c for r, row in enumerate(grid) for c, v in enumerate(row) if v in {2, 6, 7})
    candidate = (r0 + observed["shape_h"] // 2, c0 + observed["shape_w"] // 2)
    if candidate == (hr, hc) or grid[candidate[0]][candidate[1]] != 7:
        candidate = next(
            (r, c)
            for r in range(r0, r0 + observed["shape_h"])
            for c in range(c0, c0 + observed["shape_w"])
            if grid[r][c] == 7
        )
    punched_body[candidate[0]][candidate[1]] = 5
    assert GEN.self_check(punched_body)


def test_incompatible_explicit_geometry_rejects_loudly():
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(
            1, 2, difficulty="hard",
            grid_h=12, grid_w=12,
            shape_h=5, shape_w=5,
            trail_len=6, arrow_direction="down_right",
        )
