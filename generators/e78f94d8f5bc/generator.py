"""Generator for ARC task b15fca0b.

The input is a maze made from walkable color 0 and wall color 1. Exactly two
color-2 endpoints lie in the walkable region. The Racket authority paints the
single shortest path between the endpoints color 4 and then restores both
endpoints to color 2.

Generated mazes are perfect mazes (their walkable graph is a tree), so the
endpoint path is unique. Endpoints are selected so that walls force a detour,
and every scene retains off-path walkable branches. A dimension-preserving
random symmetry varies the lattice phase and orientation. Four-pair teaching
windows repeat both the 10x10 size and four-turn route categories, so any one
pair can serve as the query without reviving size- or turn-conditioned rivals.
Those constraints prevent straight-line, fill-all-background, fixed-lattice,
and arbitrary tie-breaking shortcuts from matching the intended rule.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e78f94d8f5bc"
TASK_ID = "e78f94d8f5bc"
VERSION = "3.2.0"
RULE_HASH = "6726820f442b"

SUMMARY = (
    "A randomly oriented 5..10 square-or-rectangular perfect maze uses color 1 for walls and "
    "color 0 for walkable cells. Exactly two color-2 endpoints have one unique "
    "wall-forced shortest path with 2..4 turns, while unused walkable branches "
    "remain as distractors. Four-pair lesson windows cover all three canonical "
    "sizes and turn counts while repeating 10x10/four-turn evidence for query "
    "rotation safety. Fill only that shortest path with color 4 and preserve both "
    "endpoints as color 2."
)

INVARIANTS = [
    "the input palette is exactly {0, 1, 2}: walkable 0, wall 1, endpoints 2",
    "there are exactly two color-2 endpoints in one connected walkable region",
    "the endpoints have exactly one shortest 4-neighbor path through colors 0/2",
    "walls force the unique path to be longer than endpoint Manhattan distance",
    "at least two walkable color-0 cells lie off the endpoint path",
    "generated walkable cells form a tree, so shortest-path tie-breaking is absent",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "cycle through canonical heights 5, 6, and 10",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "cycle through canonical widths 5, 6, and 10",
        "valid": "5..10",
    },
    "route_turns": {
        "type": "int",
        "default": "cycle 2, 3, and 4 turns",
        "valid": "2..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_CANONICAL_SIZES = ((5, 5), (6, 6), (10, 10))
_TEACHING_SIZES = ((10, 10), (10, 10), (5, 5), (6, 6))
_TEACHING_TURNS = (4, 4, 2, 3)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))

Cell = tuple[int, int]
Edge = tuple[Cell, Cell]
Grid = list[list[int]]


def _draw_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Draw an override over the full domain, otherwise pin the scheduled value."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _neighbors(cell: Cell, h: int, w: int) -> Iterable[Cell]:
    r, c = cell
    for dr, dc in _NEIGHBORS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _bfs_distances(grid: Grid, start: Cell) -> dict[Cell, int]:
    h, w = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for nxt in _neighbors(cell, h, w):
            if nxt in distances or grid[nxt[0]][nxt[1]] not in (0, 2):
                continue
            distances[nxt] = distances[cell] + 1
            queue.append(nxt)
    return distances


def _racket_order_path(grid: Grid, start: Cell, goal: Cell) -> list[Cell]:
    """Mirror shortest-path-fill's up/down/left/right BFS parent choice."""
    h, w = len(grid), len(grid[0])
    parent: dict[Cell, Cell | None] = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in _neighbors(cell, h, w):
            if nxt in parent:
                continue
            if grid[nxt[0]][nxt[1]] == 0 or nxt == goal:
                parent[nxt] = cell
                queue.append(nxt)
    if goal not in parent:
        return []
    path: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def _shortest_path_count(
    grid: Grid, start: Cell, goal: Cell, distances: dict[Cell, int]
) -> int:
    """Count shortest paths, capped at two because only uniqueness matters."""
    if goal not in distances:
        return 0
    reverse = _bfs_distances(grid, goal)
    total = distances[goal]
    ways: dict[Cell, int] = {start: 1}
    by_distance: dict[int, list[Cell]] = {}
    for cell, distance in distances.items():
        if cell in reverse and distance + reverse[cell] == total:
            by_distance.setdefault(distance, []).append(cell)
    h, w = len(grid), len(grid[0])
    for distance in range(total):
        for cell in by_distance.get(distance, ()):
            for nxt in _neighbors(cell, h, w):
                if distances.get(nxt) != distance + 1:
                    continue
                if nxt not in reverse or distances[nxt] + reverse[nxt] != total:
                    continue
                ways[nxt] = min(2, ways.get(nxt, 0) + ways.get(cell, 0))
    return ways.get(goal, 0)


def _turn_count(path: list[Cell]) -> int:
    directions = [
        (path[index + 1][0] - path[index][0],
         path[index + 1][1] - path[index][1])
        for index in range(len(path) - 1)
    ]
    return sum(
        directions[index] != directions[index - 1]
        for index in range(1, len(directions))
    )


def _component_count(cells: set[Cell]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def _analyze(grid) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 5 <= h <= 10:
        errors.append(f"grid height {h} outside 5..10")
    if not 5 <= w <= 10:
        errors.append(f"grid width {w} outside 5..10")

    by_color: dict[int, set[Cell]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1, 2):
                errors.append(f"cell ({r},{c}) has invalid input color {value!r}")
                continue
            by_color.setdefault(value, set()).add((r, c))
    if any("invalid input color" in error for error in errors):
        return {"errors": errors}

    endpoints = sorted(by_color.get(2, set()))
    zeros = set(by_color.get(0, set()))
    walls = set(by_color.get(1, set()))
    if len(endpoints) != 2:
        errors.append(f"expected exactly two color-2 endpoints, got {len(endpoints)}")
        return {"errors": errors}
    if not zeros:
        errors.append("expected walkable color-0 cells")
    if not walls:
        errors.append("expected at least one color-1 wall")

    start, goal = endpoints
    distances = _bfs_distances(grid, start)
    walkable = zeros | set(endpoints)
    if goal not in distances:
        errors.append("endpoints are disconnected through colors 0/2")
        return {"errors": errors}
    if len(distances) != len(walkable):
        errors.append("all walkable color-0 cells must share the endpoint region")

    path_count = _shortest_path_count(grid, start, goal, distances)
    if path_count != 1:
        errors.append(f"expected one unique shortest path, found {path_count if path_count < 2 else 'multiple'}")
    path = _racket_order_path(grid, start, goal)
    distance = len(path) - 1
    manhattan = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    if distance <= manhattan:
        errors.append(
            f"walls do not force a detour: path length {distance}, Manhattan {manhattan}"
        )
    path_cells = set(path)
    off_path_zeros = zeros - path_cells
    if len(off_path_zeros) < 2:
        errors.append(
            f"need at least two off-path walkable distractors, got {len(off_path_zeros)}"
        )

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "endpoints": endpoints,
        "zeros": zeros,
        "walls": walls,
        "path": path,
        "path_cells": path_cells,
        "path_distance": distance,
        "manhattan_distance": manhattan,
        "detour": distance - manhattan,
        "route_turns": _turn_count(path),
        "off_path_zero_count": len(off_path_zeros),
        "walkable_cells": len(walkable),
        "walkable_components": _component_count(walkable),
        "wall_components": _component_count(walls) if walls else 0,
        "walkable_is_tree": _walkable_is_tree(grid, walkable),
        "shortest_path_count": path_count,
    }


def _walkable_is_tree(grid: Grid, walkable: set[Cell]) -> bool:
    h, w = len(grid), len(grid[0])
    edge_count = 0
    for r, c in walkable:
        if r + 1 < h and (r + 1, c) in walkable:
            edge_count += 1
        if c + 1 < w and (r, c + 1) in walkable:
            edge_count += 1
    return bool(walkable) and edge_count == len(walkable) - 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-hiding shortest-path scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": int(analysis["grid_h"]),
        "grid_w": int(analysis["grid_w"]),
        "route_turns": int(analysis["route_turns"]),
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "path_distance": analysis["path_distance"],
        "manhattan_distance": analysis["manhattan_distance"],
        "detour": analysis["detour"],
        "off_path_zero_count": analysis["off_path_zero_count"],
        "walkable_is_tree": analysis["walkable_is_tree"],
        "wall_components": analysis["wall_components"],
        "canonical_size_5x5": (analysis["grid_h"], analysis["grid_w"]) == (5, 5),
        "canonical_size_6x6": (analysis["grid_h"], analysis["grid_w"]) == (6, 6),
        "canonical_size_10x10": (analysis["grid_h"], analysis["grid_w"]) == (10, 10),
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _random_spanning_tree(height: int, width: int, rng) -> list[Edge]:
    nodes = [(r, c) for r in range(height) for c in range(width)]
    edges: list[Edge] = []
    for r, c in nodes:
        if r + 1 < height:
            edges.append(((r, c), (r + 1, c)))
        if c + 1 < width:
            edges.append(((r, c), (r, c + 1)))
    rng.shuffle(edges)

    parent = {node: node for node in nodes}
    rank = {node: 0 for node in nodes}

    def find(node: Cell) -> Cell:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    tree: list[Edge] = []
    for first, second in edges:
        root_first = find(first)
        root_second = find(second)
        if root_first == root_second:
            continue
        if rank[root_first] < rank[root_second]:
            root_first, root_second = root_second, root_first
        parent[root_second] = root_first
        if rank[root_first] == rank[root_second]:
            rank[root_first] += 1
        tree.append((first, second))
        if len(tree) == len(nodes) - 1:
            return tree
    raise AssertionError("failed to construct a spanning tree")


def _tree_path(adjacency: dict[Cell, list[Cell]], start: Cell, goal: Cell) -> list[Cell]:
    parent: dict[Cell, Cell | None] = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in adjacency[cell]:
            if nxt not in parent:
                parent[nxt] = cell
                queue.append(nxt)
    path: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def _endpoint_candidates(
    height: int, width: int, tree: list[Edge], requested_turns: int
) -> list[tuple[Cell, Cell, list[Cell]]]:
    nodes = [(r, c) for r in range(height) for c in range(width)]
    adjacency = {node: [] for node in nodes}
    for first, second in tree:
        adjacency[first].append(second)
        adjacency[second].append(first)

    candidates: list[tuple[Cell, Cell, list[Cell]]] = []
    for first_index, start in enumerate(nodes):
        for goal in nodes[first_index + 1:]:
            path = _tree_path(adjacency, start, goal)
            edges = len(path) - 1
            manhattan = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            if edges < 4 or edges <= manhattan:
                continue
            if _turn_count(path) != requested_turns:
                continue
            # Expanded maze has 2*N-1 walkable cells and 2*edges+1 path cells.
            # Leave at least two off-path zero cells to refute fill-all-zero.
            if 2 * (len(nodes) - edges - 1) < 2:
                continue
            candidates.append((start, goal, path))
    return candidates


def _select_candidate(candidates, difficulty, rng):
    candidates = sorted(candidates, key=lambda item: (len(item[2]), item[0], item[1]))
    third = max(1, len(candidates) // 3)
    if difficulty == "easy":
        pool = candidates[:third]
    elif difficulty == "hard":
        pool = candidates[-third:]
    else:
        begin = max(0, (len(candidates) - third) // 2)
        pool = candidates[begin:begin + third]
    return rng.choice(pool)


def _apply_orientation(grid: Grid, orientation: int) -> Grid:
    """Apply one of four shape-preserving grid symmetries."""
    if orientation == 0:
        return [row[:] for row in grid]
    if orientation == 1:
        return [row[::-1] for row in grid]
    if orientation == 2:
        return [row[:] for row in grid[::-1]]
    if orientation == 3:
        return [row[::-1] for row in grid[::-1]]
    raise ValueError(f"unknown orientation {orientation!r}")


def _build_maze(h: int, w: int, requested_turns: int, difficulty, rng) -> Grid:
    coarse_h = (h + 1) // 2
    coarse_w = (w + 1) // 2
    for _attempt in range(256):
        tree = _random_spanning_tree(coarse_h, coarse_w, rng)
        candidates = _endpoint_candidates(coarse_h, coarse_w, tree, requested_turns)
        if not candidates:
            continue
        start, goal, _coarse_path = _select_candidate(candidates, difficulty, rng)
        grid = full_grid(h, w, 1)
        for r in range(coarse_h):
            for c in range(coarse_w):
                grid[2 * r][2 * c] = 0
        for first, second in tree:
            grid[first[0] + second[0]][first[1] + second[1]] = 0
        grid[2 * start[0]][2 * start[1]] = 2
        grid[2 * goal[0]][2 * goal[1]] = 2
        return grid
    raise ValueError(
        f"could not construct {h}x{w} perfect maze with {requested_turns} turns"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    default_h, default_w = _TEACHING_SIZES[(sample_index + band_offset) % 4]
    default_turns = _TEACHING_TURNS[(sample_index + 2 * band_offset) % 4]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_axis(ctx, overrides, "grid_h", default_h, 5, 10)
    w = _draw_axis(ctx, overrides, "grid_w", default_w, 5, 10)
    route_turns = _draw_axis(ctx, overrides, "route_turns", default_turns, 2, 4)
    grid = _build_maze(h, w, route_turns, difficulty, ctx.draw_rng("maze"))
    grid = _apply_orientation(grid, ctx.draw_rng("orientation").randrange(4))

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid shortest-path lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise AssertionError(
                f"axis {axis!r} requested {value!r} but grid observes {observed.get(axis)!r}"
            )
    return grid


def rule_mirror(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    for r, c in analysis["path"]:
        out[r][c] = 4
    for r, c in analysis["endpoints"]:
        out[r][c] = 2
    return out


def _fill_all_zeros(grid: Grid) -> Grid:
    return [[4 if value == 0 else value for value in row] for row in grid]


def _ignore_walls_row_first(grid: Grid) -> Grid:
    endpoints = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    if len(endpoints) != 2:
        return [row[:] for row in grid]
    start, goal = endpoints
    out = [row[:] for row in grid]
    r, c = start
    step_r = 1 if goal[0] > r else -1
    while r != goal[0]:
        r += step_r
        out[r][c] = 4
    step_c = 1 if goal[1] > c else -1
    while c != goal[1]:
        c += step_c
        out[r][c] = 4
    out[start[0]][start[1]] = 2
    out[goal[0]][goal[1]] = 2
    return out


def _paint_endpoint_bbox(grid: Grid) -> Grid:
    endpoints = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    if len(endpoints) != 2:
        return [row[:] for row in grid]
    (r1, c1), (r2, c2) = endpoints
    out = [row[:] for row in grid]
    for r in range(min(r1, r2), max(r1, r2) + 1):
        for c in range(min(c1, c2), max(c1, c2) + 1):
            if out[r][c] == 0:
                out[r][c] = 4
    return out


def _skip_10x10(grid: Grid) -> Grid:
    """Plausible sparse-demo rival: do nothing on the largest canonical size."""
    if len(grid) == 10 and len(grid[0]) == 10:
        return [row[:] for row in grid]
    return rule_mirror(grid)


def _skip_four_turn_routes(grid: Grid) -> Grid:
    """Plausible sparse-demo rival: transform only paths with at most 3 turns."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis.get("route_turns") == 4:
        return [row[:] for row in grid]
    return rule_mirror(grid)


SEMANTIC_RIVALS = {
    "fill_all_walkable_zeros": _fill_all_zeros,
    "ignore_walls_row_first": _ignore_walls_row_first,
    "paint_endpoint_bbox": _paint_endpoint_bbox,
    "skip_10x10": _skip_10x10,
    "skip_four_turn_routes": _skip_four_turn_routes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness(grid, predicate) -> bool:
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(predicate(observables))


SEMANTIC_WITNESSES = {
    "canonical_size_5x5": lambda grid: _witness(grid, lambda obs: obs["canonical_size_5x5"]),
    "canonical_size_6x6": lambda grid: _witness(grid, lambda obs: obs["canonical_size_6x6"]),
    "canonical_size_10x10": lambda grid: _witness(grid, lambda obs: obs["canonical_size_10x10"]),
    "route_turns_2": lambda grid: _witness(grid, lambda obs: obs["route_turns"] == 2),
    "route_turns_3": lambda grid: _witness(grid, lambda obs: obs["route_turns"] == 3),
    "route_turns_4": lambda grid: _witness(grid, lambda obs: obs["route_turns"] == 4),
    "wall_forced_detour": lambda grid: _witness(grid, lambda obs: obs["detour"] > 0),
    "off_path_distractors": lambda grid: _witness(
        grid, lambda obs: obs["off_path_zero_count"] >= 2
    ),
    "unique_tree_maze": lambda grid: _witness(grid, lambda obs: obs["walkable_is_tree"]),
}

WITNESS_RIVALS = {
    name: ["fill_all_walkable_zeros", "ignore_walls_row_first"]
    for name in SEMANTIC_WITNESSES
}

SCHEDULE_PROFILES = (2, 3, 4)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return _TEACHING_TURNS[(sample_index + 2 * band_offset) % 4]


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if self_check(query_input):
        return ["query input is not a lawful unique shortest-path scene"]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the shortest-path rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query"
                )
    return reasons
