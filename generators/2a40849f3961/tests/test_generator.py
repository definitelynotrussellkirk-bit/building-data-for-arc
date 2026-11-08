"""Regression tests for the checkpoint-maze sampler.

The test oracle is independent of production helpers.  It mirrors the selected
Racket BFS order (up, down, left, right) and separately implements the strongest
canonical-fitting rival found during review: up, down, right, left.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2a40849f3961"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

UP_DOWN_LEFT_RIGHT = ((-1, 0), (1, 0), (0, -1), (0, 1))
UP_DOWN_RIGHT_LEFT = ((-1, 0), (1, 0), (0, 1), (0, -1))


def _positions(grid):
    hits = {color: [] for color in (1, 2, 3, 4)}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in hits:
                hits[value].append((row, col))
    if any(len(points) != 1 for points in hits.values()):
        raise ValueError(f"checkpoint multiplicities: {hits}")
    return {color: points[0] for color, points in hits.items()}


def _shortest_path(grid, start, goal, order):
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for delta_row, delta_col in order:
            neighbor = (point[0] + delta_row, point[1] + delta_col)
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and grid[neighbor[0]][neighbor[1]] != 5
                and neighbor not in parent
            ):
                parent[neighbor] = point
                queue.append(neighbor)
    if goal not in parent:
        return []
    path = []
    point = goal
    while point is not None:
        path.append(point)
        point = parent[point]
    return list(reversed(path))


def solve_with_order(grid, order=UP_DOWN_LEFT_RIGHT):
    positions = _positions(grid)
    route = set()
    for first, second in ((1, 2), (2, 3), (3, 4)):
        path = _shortest_path(grid, positions[first], positions[second], order)
        route.update(path[1:-1])
    output = deepcopy(grid)
    for row, col in route:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def right_before_left_rival(grid):
    return solve_with_order(grid, UP_DOWN_RIGHT_LEFT)


def _wall_component_sizes(grid):
    walls = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    seen = set()
    sizes = []
    for start in walls:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for delta_row, delta_col in UP_DOWN_LEFT_RIGHT:
                neighbor = (row + delta_row, col + delta_col)
                if neighbor in walls and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _wall_components(grid):
    return len(_wall_component_sizes(grid))


def _all_generated_legs_reachable(grid):
    positions = _positions(grid)
    return all(
        _shortest_path(grid, positions[first], positions[second], UP_DOWN_LEFT_RIGHT)
        for first, second in ((1, 2), (2, 3), (3, 4))
    )


def _changed_cells(before, after):
    return [
        (row, col)
        for row in range(len(before))
        for col in range(len(before[0]))
        if before[row][col] != after[row][col]
    ]


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "cd7f3a44d341"
    assert GEN.VERSION == "3.0.0"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.AXES) == {"grid_h", "grid_w", "scene_pattern"}
    assert set(GEN.SCHEDULE_PROFILES) == {"canonical_maze", "tie_break"}


def test_independent_oracle_and_rival_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert solve_with_order(pair["input"]) == pair["output"]
        assert right_before_left_rival(pair["input"]) == pair["output"]
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height", [11, 13])
@pytest.mark.parametrize("width", [12, 14])
@pytest.mark.parametrize("pattern", ["canonical_maze", "tie_break"])
def test_joint_exact_overrides_are_constructive_and_observable(
    band, height, width, pattern
):
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        scene_pattern=pattern,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "scene_pattern": pattern,
    }
    assert _all_generated_legs_reachable(grid)
    truth = solve_with_order(grid)
    assert len(_changed_cells(grid, truth)) >= 5
    if pattern == "tie_break":
        assert truth != right_before_left_rival(grid)
    else:
        assert truth == right_before_left_rival(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 10),
        ("grid_h", 14),
        ("grid_w", 11),
        ("grid_w", 15),
        ("scene_pattern", "unknown"),
        ("typo_axis", 1),
        ("grid_h", True),
        ("grid_w", 12.5),
        ("scene_pattern", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_maze_like_deterministic_and_balanced(band):
    patterns = set()
    shapes = set()
    wall_component_counts = set()
    distinct = set()
    for index in range(128):
        seed = 20_000 + index * 997
        grid = GEN.generate(seed, index, difficulty=band)
        assert grid == GEN.generate(seed, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert _all_generated_legs_reachable(grid)
        assert {value for row in grid for value in row} == {0, 1, 2, 3, 4, 5}
        assert sum(value == 0 for row in grid for value in row) > len(grid) * len(grid[0]) // 2
        wall_count = sum(value == 5 for row in grid for value in row)
        components = _wall_components(grid)
        assert 12 <= wall_count <= 40
        assert 3 <= components <= 8
        truth = solve_with_order(grid)
        assert 5 <= len(_changed_cells(grid, truth)) <= 60
        observed = GEN.observe_overrides(grid)
        pattern = observed["scene_pattern"]
        patterns.add(pattern)
        shapes.add((len(grid), len(grid[0])))
        wall_component_counts.add(components)
        distinct.add(json.dumps(grid, separators=(",", ":")))
        assert GEN.SEMANTIC_WITNESSES["left_right_tie"](grid) == (
            pattern == "tie_break"
        )
        assert (truth != right_before_left_rival(grid)) == (
            pattern == "tie_break"
        )
    assert patterns == {"canonical_maze", "tie_break"}
    assert len(shapes) >= 6
    assert len(wall_component_counts) >= 2
    assert len(distinct) >= 120


def test_canonical_maze_supports_source_scale_wall_objects():
    maxima = []
    for index in range(128):
        grid = GEN.generate(88_000 + index, index, scene_pattern="canonical_maze")
        maxima.append(max(_wall_component_sizes(grid)))
    assert max(maxima) >= 12
    assert min(maxima) >= 3


def test_declared_shortcut_is_canonical_fitting_and_tie_scene_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"right_before_left"}
    shortcut = GEN.CANONICAL_SHORTCUTS["right_before_left"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)
    grid = GEN.generate(
        42,
        1,
        grid_h=11,
        grid_w=12,
        scene_pattern="tie_break",
    )
    intended = solve_with_order(grid)
    rival = shortcut(grid)
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["left_right_tie"](grid)
    assert intended != rival
    assert _changed_cells(intended, rival)


def test_every_four_pair_window_and_query_rotation_refutes_the_shortcut():
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(700_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": solve_with_order(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, query_index, name)


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 9, scene_pattern="tie_break")
    original = deepcopy(grid)
    GEN.observe_overrides(grid)
    GEN.strict_canonical_like(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == original


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(11)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_semantically_malformed_near_misses():
    grid = GEN.generate(55, 3, scene_pattern="tie_break")
    no_wall = [[0 if value == 5 else value for value in row] for row in grid]
    duplicate = deepcopy(grid)
    duplicate[0][0] = 1
    unknown = deepcopy(grid)
    unknown[0][0] = 9
    all_background = [[0 for _ in row] for row in grid]
    for changed in (no_wall, duplicate, unknown, all_background):
        assert GEN.self_check(changed)


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from puzzle_generators import runner

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    root = find_root(__file__)
    with (root / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK_ID)
    grids = [pair["input"] for pair in canonical_pairs(TASK_ID, root=root)]
    grids.extend(GEN.generate(319, index) for index in range(12))
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(row["program_solution"]))
    try:
        actual = [runner._apply_rule(bridge, name, grid) for grid in grids]
    finally:
        bridge.close()
    assert actual == [solve_with_order(grid) for grid in grids]
