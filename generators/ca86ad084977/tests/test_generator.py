"""Regression tests for the ordered checkpoint-path generator.

The oracle here is intentionally independent of production helpers.  It mirrors
Racket's pinned up/down/left/right BFS and, unlike the retired generator, paints
*every* interior path cell cyan -- even when that cell is another checkpoint.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "ca86ad084977"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

UDLR = ((-1, 0), (1, 0), (0, -1), (0, 1))
UDRL = ((-1, 0), (1, 0), (0, 1), (0, -1))
CHECKPOINTS = (2, 3, 4, 7)
LEGS = ((2, 3), (3, 4), (4, 7))


def positions(grid):
    hits = {color: [] for color in CHECKPOINTS}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in hits:
                hits[value].append((row, col))
    if any(len(points) != 1 for points in hits.values()):
        raise ValueError(f"checkpoint multiplicities: {hits}")
    return {color: points[0] for color, points in hits.items()}


def shortest_path(grid, start, goal, order=UDLR):
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for delta_row, delta_col in order:
            neighbor = point[0] + delta_row, point[1] + delta_col
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
    answer = []
    point = goal
    while point is not None:
        answer.append(point)
        point = parent[point]
    return list(reversed(answer))


def solve_all_interiors(grid, order=UDLR):
    points = positions(grid)
    route = set()
    for first, second in LEGS:
        route.update(shortest_path(grid, points[first], points[second], order)[1:-1])
    output = deepcopy(grid)
    for row, col in route:
        output[row][col] = 8
    return output


def preserve_checkpoint_rival(grid):
    points = positions(grid)
    route = set()
    for first, second in LEGS:
        route.update(shortest_path(grid, points[first], points[second], UDLR)[1:-1])
    output = deepcopy(grid)
    for row, col in route:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def right_before_left_rival(grid):
    return solve_all_interiors(grid, UDRL)


def wall_component_sizes(grid):
    walls = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    seen = set()
    sizes = []
    for start in sorted(walls):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for delta_row, delta_col in UDLR:
                neighbor = row + delta_row, col + delta_col
                if neighbor in walls and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def changed_cells(before, after):
    return [
        (row, col)
        for row in range(len(before))
        for col in range(len(before[0]))
        if before[row][col] != after[row][col]
    ]


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "1c1d9560813f"
    assert GEN.VERSION == "3.0.0"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert set(GEN.AXES) == {"grid_h", "grid_w", "scene_pattern"}
    assert set(GEN.SCHEDULE_PROFILES) == {"canonical_maze", "semantic_witness"}


def test_independent_oracle_matches_all_canonical_pairs_and_exposes_overwrite_branch():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    overwrite_examples = 0
    for pair in pairs:
        assert solve_all_interiors(pair["input"]) == pair["output"]
        assert right_before_left_rival(pair["input"]) == pair["output"]
        if preserve_checkpoint_rival(pair["input"]) != pair["output"]:
            overwrite_examples += 1
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
    assert overwrite_examples == 3


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height", [12, 13])
@pytest.mark.parametrize("width", [12, 14])
@pytest.mark.parametrize("pattern", ["canonical_maze", "semantic_witness"])
def test_joint_exact_overrides_are_constructive_and_observable(
    band, height, width, pattern
):
    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_pattern": pattern,
    }
    grid = GEN.generate(91, 7, difficulty=band, **expected)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected
    truth = solve_all_interiors(grid)
    assert 6 <= len(changed_cells(grid, truth)) <= 48
    if pattern == "semantic_witness":
        assert truth != right_before_left_rival(grid)
        assert truth != preserve_checkpoint_rival(grid)
    else:
        assert truth == right_before_left_rival(grid)
        assert truth == preserve_checkpoint_rival(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 11),
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


@pytest.mark.parametrize(
    "args",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, 1.0, None),
        (1, "1", None),
        (1, -1, None),
        (1, 0, True),
        (1, 0, 0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_seed_sample_index_and_difficulty_are_rejected(args):
    seed, sample_index, difficulty = args
    with pytest.raises(ValueError):
        GEN.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_sparse_maze_like_deterministic_and_balanced(band):
    patterns = set()
    shapes = set()
    component_counts = set()
    distinct = set()
    for index in range(128):
        seed = 20_000 + index * 997
        grid = GEN.generate(seed, index, difficulty=band)
        assert grid == GEN.generate(seed, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert {value for row in grid for value in row} == {0, 2, 3, 4, 5, 7}
        assert sum(value == 0 for row in grid for value in row) > len(grid) * len(grid[0]) // 2
        assert len({positions(grid)[color][0] for color in CHECKPOINTS}) >= 3
        wall_count = sum(value == 5 for row in grid for value in row)
        components = len(wall_component_sizes(grid))
        assert 6 <= wall_count <= 15
        assert 2 <= components <= 3
        truth = solve_all_interiors(grid)
        assert 6 <= len(changed_cells(grid, truth)) <= 48
        observed = GEN.observe_overrides(grid)
        pattern = observed["scene_pattern"]
        patterns.add(pattern)
        shapes.add((len(grid), len(grid[0])))
        component_counts.add(components)
        distinct.add(json.dumps(grid, separators=(",", ":")))
        assert GEN.SEMANTIC_WITNESSES["left_right_tie"](grid) == (
            pattern == "semantic_witness"
        )
        assert GEN.SEMANTIC_WITNESSES["checkpoint_overwrite"](grid) == (
            pattern == "semantic_witness"
        )
    assert patterns == {"canonical_maze", "semantic_witness"}
    assert len(shapes) == 6
    assert component_counts == {2, 3}
    assert len(distinct) >= 120


def test_four_step_schedule_teaches_both_canonical_checkpoint_overwrite_colors():
    seen = []
    for sample_index in (1, 3):
        grid = GEN.generate(
            123,
            sample_index,
            grid_h=12,
            grid_w=12,
            scene_pattern="semantic_witness",
        )
        truth = solve_all_interiors(grid)
        overwritten = {
            grid[row][col]
            for row, col in changed_cells(grid, truth)
            if grid[row][col] in CHECKPOINTS
        }
        seen.append(overwritten)
    assert seen == [{2}, {4}]


def test_declared_rivals_are_source_bound_and_semantic_witness_refutes_both():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"right_before_left"}
    assert all(
        GEN.CANONICAL_SHORTCUTS["right_before_left"](pair["input"])
        == pair["output"]
        for pair in pairs
    )
    grid = GEN.generate(42, 1, grid_h=12, grid_w=12, scene_pattern="semantic_witness")
    intended = solve_all_interiors(grid)
    assert GEN.SEMANTIC_WITNESSES["left_right_tie"](grid)
    assert GEN.SEMANTIC_WITNESSES["checkpoint_overwrite"](grid)
    assert intended != GEN.SEMANTIC_RIVALS["right_before_left"](grid)
    assert intended != GEN.SEMANTIC_RIVALS["preserve_checkpoints"](grid)


def test_every_four_pair_window_and_query_rotation_refutes_both_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(700_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": solve_all_interiors(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 9, scene_pattern="semantic_witness")
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
    [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(12)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert GEN.self_check(grid)


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from puzzle_generators import runner

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        row = next(
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == TASK_ID
        )
    grids = [pair["input"] for pair in canonical_pairs(TASK_ID, root=root)]
    grids.extend(GEN.generate(319, index) for index in range(12))
    source = row["program_solution"].strip()
    assert source.startswith("(rule!") and source.endswith(")")
    body = source[len("(rule!") : -1].strip()
    callable_text = (
        "(lambda (g) (let* ((h (rows g)) (w (cols g))) " + body + "))"
    )
    bridge, name = runner._open_bridge_with_rule(callable_text)
    try:
        actual = [runner._apply_rule(bridge, name, grid) for grid in grids]
    finally:
        bridge.close()
    assert actual == [solve_all_interiors(grid) for grid in grids]
