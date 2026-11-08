from __future__ import annotations

from collections import deque
from copy import deepcopy

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "d3ae93aa8d37"
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator():
    module, _path, _sha256 = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


def endpoints(grid):
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    assert len(red) == len(green) == 1
    return red[0], green[0]


def shortest_path(grid):
    start, goal = endpoints(grid)
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parents = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = parents[current]
            return list(reversed(path))
        row, column = current
        for dr, dc in DIRECTIONS:
            neighbor = (row + dr, column + dc)
            nr, nc = neighbor
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and neighbor not in parents
            ):
                parents[neighbor] = current
                queue.append(neighbor)
    return []


def solve(grid):
    out = deepcopy(grid)
    path = shortest_path(grid)
    for row, column in path[1:-1]:
        out[row][column] = 8
    return out


def straight_row_rival(grid):
    out = deepcopy(grid)
    start, goal = endpoints(grid)
    if start[0] != goal[0]:
        return out
    row = start[0]
    left, right = sorted((start[1], goal[1]))
    for column in range(left + 1, right):
        out[row][column] = 8
    return out


def wall_forces_detour(grid):
    start, goal = endpoints(grid)
    path = shortest_path(grid)
    return bool(path) and len(path) - 1 > abs(start[0] - goal[0]) + abs(start[1] - goal[1])


@pytest.mark.parametrize(
    "grid",
    [
        [[0] * 8 for _ in range(8)],
        [[True, 0, 0, 0, 0, 0], [0, 2, 0, 3, 0, 0], *([[0] * 6] * 4)],
        [[0, 2, 0, 2, 0, 3], *([[0] * 6] * 5)],
        [[0, 2, 8, 3, 0, 0], *([[0] * 6] * 5)],
        [[5, 2, 5, 3, 0, 0], [0, 5, 0, 0, 0, 0], *([[0] * 6] * 4)],
    ],
)
def test_self_check_rejects_malformed_or_out_of_domain_grids(grid):
    mod = load_generator()
    assert mod.self_check(grid), grid


def test_generate_rejects_unknown_controls_and_honors_exact_axes():
    mod = load_generator()
    with pytest.raises((TypeError, ValueError), match="unknown"):
        mod.generate(0, 0, not_an_axis=1)

    grid = mod.generate(
        20261024,
        0,
        grid_h=12,
        grid_w=13,
        n_walls=7,
        distance=6,
        scene_profile="forced_detour",
        position_bias="horizontal",
    )
    start, goal = endpoints(grid)
    assert (len(grid), len(grid[0])) == (12, 13)
    assert sum(value == 5 for row in grid for value in row) == 7
    assert abs(start[0] - goal[0]) + abs(start[1] - goal[1]) == 6
    assert wall_forces_detour(grid)
    assert mod.self_check(grid) == []


def test_every_four_sample_window_contains_a_straight_rival_counterexample():
    mod = load_generator()
    for start_index in range(20):
        grids = [
            mod.generate(8, index, difficulty="easy")
            for index in range(start_index, start_index + mod.EXAMPLES_NEEDED)
        ]
        assert all(mod.self_check(grid) == [] for grid in grids)
        assert any(
            wall_forces_detour(grid) and solve(grid) != straight_row_rival(grid)
            for grid in grids
        ), start_index


def test_retained_seed8_start1_wrong_query_lesson_is_no_longer_ambiguous():
    mod = load_generator()
    grids = [mod.generate(8, index, difficulty="easy") for index in range(1, 6)]
    authority = [solve(grid) for grid in grids]
    rival = [straight_row_rival(grid) for grid in grids]

    assert any(authority[index] != rival[index] for index in range(4))
    assert all(mod.self_check(grid) == [] for grid in grids)


def test_scheduled_profiles_vary_endpoint_geometry_and_wall_load():
    mod = load_generator()
    grids = [mod.generate(314159, index, difficulty="medium") for index in range(4)]
    geometry = []
    wall_counts = []
    for grid in grids:
        start, goal = endpoints(grid)
        geometry.append(
            "horizontal"
            if start[0] == goal[0]
            else "vertical"
            if start[1] == goal[1]
            else "offset"
        )
        wall_counts.append(sum(value == 5 for row in grid for value in row))
    assert geometry == ["horizontal", "offset", "vertical", "offset"]
    assert wall_counts[3] > wall_counts[1]
    assert wall_forces_detour(grids[0])
    assert wall_forces_detour(grids[2])


def test_literal_minimum_and_30x30_dense_boundary_are_reachable():
    mod = load_generator()
    small = mod.generate(
        11,
        0,
        grid_h=6,
        grid_w=6,
        n_walls=1,
        distance=3,
        scene_profile="forced_detour",
        position_bias="horizontal",
    )
    large = mod.generate(
        12,
        3,
        grid_h=30,
        grid_w=30,
        n_walls=100,
        distance=18,
        scene_profile="dense_maze",
        position_bias="offset",
    )
    assert (len(small), len(small[0])) == (6, 6)
    assert (len(large), len(large[0])) == (30, 30)
    assert len(shortest_path(small)) > 0
    assert len(shortest_path(large)) > 0
    assert sum(value == 5 for row in large for value in row) == 100
    assert mod.self_check(small) == []
    assert mod.self_check(large) == []


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    mod = load_generator()
    first = mod.generate(99, 7, difficulty="hard")
    second = mod.generate(99, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
