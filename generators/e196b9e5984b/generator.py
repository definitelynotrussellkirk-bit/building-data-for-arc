"""Generator for hard_e07 — paint the canonical BFS corridor between portals.

Gray (5) cells are walls.  Exactly two cells share one non-{0,5} portal
color.  Read the portals in row-major order, then run 4-connected BFS from the
first portal through zero cells with neighbor priority RIGHT, DOWN, LEFT, UP.
Return a fresh grid containing the walls and the first-discovered shortest path
painted in the portal color.

The original prose called the canonical paths unique, but two training inputs
have multiple shortest routes.  This generator therefore schedules one unique
maze and three controlled tie profiles in every four consecutive samples so a
lesson identifies the selected R/D/L/U queue order instead of learning an
arbitrary "any shortest path" shortcut.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e196b9e5984b"
TASK_ID = "e196b9e5984b"
VERSION = "4.0.0"
RULE_HASH = "d55a733c2b68"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A gray(5)-walled maze contains exactly two same-colored portals. Read the "
    "portals in row-major order and BFS from the first through 0-cells using "
    "neighbor priority right, down, left, up. On a fresh 0-grid preserve the "
    "walls and paint the first-discovered shortest path, including both "
    "portals, with the portal color. Consecutive samples schedule a unique "
    "route plus ties that separately expose R>D, D>L, and L>U priority."
)

INVARIANTS = [
    "the outer border is entirely gray(5), and every non-wall cell is interior",
    "the only input colors are 0, gray(5), and one non-{0,5} portal color",
    "exactly two portal cells share that portal color",
    "all walkable cells form one 4-connected maze containing both portals",
    "ordinary draws add a nontrivial corridor and leave non-path branches visible",
]

_ALLOWED_HEIGHTS = (7, 9, 11)
_ALLOWED_WIDTHS = (9, 11, 13)
_PORTAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted choice from 7|9|11",
        "valid": "7|9|11",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted choice from 9|11|13",
        "valid": "9|11|13",
    },
    "portal_color": {
        "type": "color",
        "default": "keyed non-{0,5} color",
        "valid": "1..9 (≠5)",
    },
}

# Every Cartesian combination of the declared axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_DIRECTIONS = {
    "R": (0, 1),
    "D": (1, 0),
    "L": (0, -1),
    "U": (-1, 0),
}
_OFFICIAL_ORDER = "RDLU"
_PROFILE_NAMES = (
    "unique_detour",
    "right_before_down_tie",
    "down_before_left_tie",
    "left_before_up_tie",
)
_PROFILE_RIVAL_ORDER = {
    "right_before_down_tie": "DRLU",
    "down_before_left_tie": "RLDU",
    "left_before_up_tie": "RDUL",
}
SCHEDULE_PROFILES = _PROFILE_NAMES


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, allowed in (("grid_h", _ALLOWED_HEIGHTS), ("grid_w", _ALLOWED_WIDTHS)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}")
    if "portal_color" in overrides and overrides["portal_color"] is not None:
        value = overrides["portal_color"]
        if isinstance(value, bool) or not isinstance(value, int) or value not in _PORTAL_COLORS:
            raise ValueError(f"portal_color must be one of {_PORTAL_COLORS}")


def _draw_dimensions(ctx, sample_index: int, difficulty: Any, overrides: dict[str, Any]) -> tuple[int, int]:
    """Draw exact dimensions while anchoring every band to canonical 7x{9,11}."""
    canonical_anchor = sample_index % 5 in (0, 1)

    if overrides.get("grid_h") is not None:
        h = ctx.draw_choice("grid_h", _ALLOWED_HEIGHTS)
    elif canonical_anchor:
        h = ctx.draw_choice("grid_h", (7,))
    elif difficulty == "easy":
        h = ctx.draw_choice("grid_h", (7, 7, 9))
    elif difficulty == "hard":
        h = ctx.draw_choice("grid_h", (7, 9, 11, 11))
    else:
        h = ctx.draw_choice("grid_h", _ALLOWED_HEIGHTS)

    if overrides.get("grid_w") is not None:
        w = ctx.draw_choice("grid_w", _ALLOWED_WIDTHS)
    elif canonical_anchor:
        w = ctx.draw_choice("grid_w", (9, 11))
    elif difficulty == "easy":
        w = ctx.draw_choice("grid_w", (9, 9, 11))
    elif difficulty == "hard":
        w = ctx.draw_choice("grid_w", (9, 11, 13, 13))
    else:
        w = ctx.draw_choice("grid_w", _ALLOWED_WIDTHS)
    return h, w


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]


def _portals(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _walkable(grid: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 5
    }


def _bfs_predecessors(
    walkable: set[tuple[int, int]],
    start: tuple[int, int],
    order: str = _OFFICIAL_ORDER,
) -> dict[tuple[int, int], tuple[int, int] | None]:
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for direction in order:
            dr, dc = _DIRECTIONS[direction]
            nxt = (current[0] + dr, current[1] + dc)
            if nxt in walkable and nxt not in previous:
                previous[nxt] = current
                queue.append(nxt)
    return previous


def _rebuild_path(
    previous: dict[tuple[int, int], tuple[int, int] | None],
    goal: tuple[int, int],
) -> tuple[tuple[int, int], ...] | None:
    if goal not in previous:
        return None
    reverse_path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = goal
    while current is not None:
        reverse_path.append(current)
        current = previous[current]
    return tuple(reversed(reverse_path))


def _bfs_path(
    walkable: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    order: str = _OFFICIAL_ORDER,
) -> tuple[tuple[int, int], ...] | None:
    return _rebuild_path(_bfs_predecessors(walkable, start, order), goal)


def _distance_maps(
    walkable: set[tuple[int, int]], start: tuple[int, int]
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    distance = {start: 0}
    ways = {start: 1}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for dr, dc in _DIRECTIONS.values():
            nxt = (current[0] + dr, current[1] + dc)
            if nxt not in walkable:
                continue
            proposed = distance[current] + 1
            if nxt not in distance:
                distance[nxt] = proposed
                ways[nxt] = ways[current]
                queue.append(nxt)
            elif distance[nxt] == proposed:
                ways[nxt] += ways[current]
    return distance, ways


def _shortest_path_stats(
    walkable: set[tuple[int, int]], start: tuple[int, int], goal: tuple[int, int]
) -> tuple[int | None, int]:
    distance, ways = _distance_maps(walkable, start)
    return distance.get(goal), ways.get(goal, 0)


def _path_turns(path: Sequence[tuple[int, int]]) -> int:
    steps = [
        (b[0] - a[0], b[1] - a[1])
        for a, b in zip(path, path[1:])
    ]
    return sum(left != right for left, right in zip(steps, steps[1:]))


def _output_from_cells(
    grid: Sequence[Sequence[int]],
    cells: Iterable[tuple[int, int]],
    color: int,
) -> list[list[int]]:
    out = [
        [5 if value == 5 else 0 for value in row]
        for row in grid
    ]
    h, w = len(out), len(out[0])
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w and out[r][c] != 5:
            out[r][c] = color
    return out


def _output_for_order(grid: Sequence[Sequence[int]], order: str) -> list[list[int]] | None:
    portals = _portals(grid)
    if len(portals) != 2:
        return None
    start = portals[0][:2]
    goal = portals[1][:2]
    path = _bfs_path(_walkable(grid), start, goal, order)
    if path is None:
        return None
    return _output_from_cells(grid, path, portals[0][2])


def oracle_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    output = _output_for_order(grid, _OFFICIAL_ORDER)
    if output is None:
        raise ValueError("grid does not contain two connected portals")
    return output


def _perfect_maze(
    h: int, w: int, rng, extra_edges: int
) -> tuple[set[tuple[int, int]], tuple[tuple[int, int], ...]]:
    """Return a connected maze graph; extra lattice edges create controlled ties."""
    nodes = tuple((r, c) for r in range(1, h - 1, 2) for c in range(1, w - 1, 2))
    node_set = set(nodes)
    edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r, c in nodes:
        for dr, dc in ((0, 2), (2, 0)):
            neighbor = (r + dr, c + dc)
            if neighbor in node_set:
                edges.append(((r, c), neighbor))
    rng.shuffle(edges)

    parent = {node: node for node in nodes}

    def root(node: tuple[int, int]) -> tuple[int, int]:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    tree_edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for left, right in edges:
        left_root, right_root = root(left), root(right)
        if left_root != right_root:
            parent[left_root] = right_root
            tree_edges.append((left, right))

    tree_keys = {tuple(sorted(edge)) for edge in tree_edges}
    non_tree = [edge for edge in edges if tuple(sorted(edge)) not in tree_keys]
    rng.shuffle(non_tree)
    selected_edges = tree_edges + non_tree[: min(extra_edges, len(non_tree))]

    walkable = set(nodes)
    for left, right in selected_edges:
        walkable.add(((left[0] + right[0]) // 2, (left[1] + right[1]) // 2))
    return walkable, nodes


def _candidate_pair(
    walkable: set[tuple[int, int]],
    nodes: Sequence[tuple[int, int]],
    profile: str,
    rng,
    h: int,
    w: int,
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    rival_order = _PROFILE_RIVAL_ORDER.get(profile)
    candidates: list[tuple[tuple[int, ...], tuple[int, int], tuple[int, int]]] = []
    min_distance = max(6, (h + w) // 2)
    min_off_path = max(4, len(walkable) // 7)
    ordered_nodes = sorted(nodes)

    # One BFS tree per source/order is much cheaper than three BFS runs for
    # every source/goal pair.  This matters because the override matrix replays
    # thousands of exact-axis draws.
    for start_index, start in enumerate(ordered_nodes[:-1]):
        official_previous = _bfs_predecessors(walkable, start, _OFFICIAL_ORDER)
        distance_map, ways_map = _distance_maps(walkable, start)
        rival_previous = (
            _bfs_predecessors(walkable, start, rival_order)
            if rival_order is not None
            else None
        )
        for goal in ordered_nodes[start_index + 1 :]:
            official_path = _rebuild_path(official_previous, goal)
            if official_path is None:
                continue
            distance = distance_map.get(goal)
            n_shortest = ways_map.get(goal, 0)
            if distance is None or distance < min_distance:
                continue
            turns = _path_turns(official_path)
            off_path = len(walkable) - len(official_path)
            if turns < 1 or off_path < min_off_path:
                continue

            manhattan = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            if profile == "unique_detour":
                if n_shortest != 1 or distance <= manhattan:
                    continue
            else:
                if n_shortest < 2 or rival_previous is None:
                    continue
                if _rebuild_path(rival_previous, goal) == official_path:
                    continue

            quality = (distance, turns, -min(n_shortest, 999), off_path)
            candidates.append((quality, start, goal))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    shortlist = candidates[: min(8, len(candidates))]
    _, start, goal = shortlist[rng.randrange(len(shortlist))]
    return start, goal


def _construct_scene(h: int, w: int, profile: str, color: int, rng) -> list[list[int]]:
    for _attempt in range(128):
        # A tree gives the unique profile.  Tie profiles open a keyed number of
        # non-tree lattice edges and then search for a pair that separates the
        # selected queue order from its named rival.
        extra_edges = 0 if profile == "unique_detour" else rng.randint(1, 8)
        walkable, nodes = _perfect_maze(h, w, rng, extra_edges)
        pair = _candidate_pair(walkable, nodes, profile, rng, h, w)
        if pair is None:
            continue
        start, goal = pair
        grid = full_grid(h, w, 5)
        for r, c in walkable:
            grid[r][c] = 0
        grid[start[0]][start[1]] = color
        grid[goal[0]][goal[1]] = color
        return grid
    raise ValueError(f"could not construct profile {profile!r} on {h}x{w}")


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    portals = _portals(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "portal_color": portals[0][2] if len(portals) == 2 else -1,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level maze grammar; accept every canonical input."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    h, w = len(grid), width
    errors: list[str] = []
    if not (7 <= h <= 11 and 9 <= w <= 13):
        errors.append(f"grid dimensions {h}x{w} are outside the task envelope")
    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)) or any(
        grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)
    ):
        errors.append("the entire outer border must be gray(5) wall")

    portals = _portals(grid)
    if len(portals) != 2:
        errors.append(f"expected exactly two non-{{0,5}} portal cells, got {len(portals)}")
    elif portals[0][2] != portals[1][2]:
        errors.append("the two portals must have the same color")

    colors = {int(value) for row in grid for value in row}
    portal_colors = {portal[2] for portal in portals}
    if len(portal_colors) <= 1:
        allowed = {0, 5} | portal_colors
        unexpected = sorted(colors - allowed)
        if unexpected:
            errors.append(f"unexpected input colors outside 0, 5, and the portal color: {unexpected}")

    walkable = _walkable(grid)
    if not walkable:
        errors.append("maze has no walkable cells")
    else:
        start = min(walkable)
        seen = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRECTIONS.values():
                nxt = (r + dr, c + dc)
                if nxt in walkable and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if seen != walkable:
            errors.append(
                f"all walkable cells must form one component; found {len(walkable) - len(seen)} disconnected cell(s)"
            )

    if len(portals) == 2:
        path = _bfs_path(walkable, portals[0][:2], portals[1][:2], _OFFICIAL_ORDER)
        if path is None:
            errors.append("the two portals must be connected through non-wall cells")
    if not any(grid[r][c] == 5 for r in range(1, h - 1) for c in range(1, w - 1)):
        errors.append("the interior must contain gray walls that constrain the route")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Blocking curriculum predicate: valid, nontrivial, bent, branch-bearing."""
    errors = self_check(grid)
    if errors:
        return errors
    portals = _portals(grid)
    walkable = _walkable(grid)
    path = _bfs_path(walkable, portals[0][:2], portals[1][:2], _OFFICIAL_ORDER)
    assert path is not None
    distance = len(path) - 1
    if distance < max(6, (len(grid) + len(grid[0])) // 2):
        errors.append(f"portal path is too short to teach the transformation: {distance} edges")
    if _path_turns(path) < 1:
        errors.append("portal path must bend at least once")
    if len(walkable) - len(path) < max(4, len(walkable) // 7):
        errors.append("maze must retain visible non-path branches")
    if len(path) <= 2:
        errors.append("ordinary lessons may not be identity/marker-only cases")
    return errors


def _scene_analysis(grid):
    portals = _portals(grid)
    if len(portals) != 2:
        return None
    walkable = _walkable(grid)
    start, goal = portals[0][:2], portals[1][:2]
    path = _bfs_path(walkable, start, goal, _OFFICIAL_ORDER)
    if path is None:
        return None
    distance, ways = _shortest_path_stats(walkable, start, goal)
    return portals, walkable, path, distance, ways


def _all_shortest_cells(grid):
    analysis = _scene_analysis(grid)
    if analysis is None:
        return None
    portals, walkable, _, distance, _ = analysis
    start, goal = portals[0][:2], portals[1][:2]
    from_start, _ = _distance_maps(walkable, start)
    from_goal, _ = _distance_maps(walkable, goal)
    cells = {
        cell
        for cell in walkable
        if cell in from_start
        and cell in from_goal
        and from_start[cell] + from_goal[cell] == distance
    }
    return _output_from_cells(grid, cells, portals[0][2])


def _fill_all_open(grid):
    portals = _portals(grid)
    if len(portals) != 2:
        return None
    return _output_from_cells(grid, _walkable(grid), portals[0][2])


def _markers_only(grid):
    portals = _portals(grid)
    if len(portals) != 2:
        return None
    return _output_from_cells(grid, [portal[:2] for portal in portals], portals[0][2])


def _row_then_column(grid):
    portals = _portals(grid)
    if len(portals) != 2:
        return None
    start, goal = portals[0][:2], portals[1][:2]
    cells: list[tuple[int, int]] = []
    col_step = 1 if goal[1] >= start[1] else -1
    for c in range(start[1], goal[1] + col_step, col_step):
        cells.append((start[0], c))
    row_step = 1 if goal[0] >= start[0] else -1
    for r in range(start[0] + row_step, goal[0] + row_step, row_step):
        cells.append((r, goal[1]))
    return _output_from_cells(grid, cells, portals[0][2])


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]] | None]] = {
    "down_before_right": lambda grid: _output_for_order(grid, "DRLU"),
    "left_before_down": lambda grid: _output_for_order(grid, "RLDU"),
    "up_before_left": lambda grid: _output_for_order(grid, "RDUL"),
    "reverse_neighbor_order": lambda grid: _output_for_order(grid, "ULDR"),
    "all_shortest_cells": _all_shortest_cells,
    "fill_all_open": _fill_all_open,
    "markers_only": _markers_only,
    "row_then_column": _row_then_column,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# Both fit every canonical pair, so only generated tie witnesses can falsify
# them.  This is the central shortcut risk in the original generator.
CANONICAL_SHORTCUTS = {
    "left_before_down": SEMANTIC_RIVALS["left_before_down"],
    "up_before_left": SEMANTIC_RIVALS["up_before_left"],
}


def _w_unique_detour(grid) -> bool:
    analysis = _scene_analysis(grid)
    return bool(analysis and analysis[4] == 1 and _w_detour(grid))


def _w_multiple(grid) -> bool:
    analysis = _scene_analysis(grid)
    return bool(analysis and analysis[4] > 1)


def _w_order_diff(order: str):
    return lambda grid: _output_for_order(grid, order) != oracle_output(grid)


def _w_detour(grid) -> bool:
    analysis = _scene_analysis(grid)
    if analysis is None:
        return False
    portals, _, _, distance, _ = analysis
    start, goal = portals[0][:2], portals[1][:2]
    return bool(distance and distance > abs(start[0] - goal[0]) + abs(start[1] - goal[1]))


def _w_branches(grid) -> bool:
    analysis = _scene_analysis(grid)
    return bool(analysis and len(analysis[1]) > len(analysis[2]))


def _w_nonidentity(grid) -> bool:
    analysis = _scene_analysis(grid)
    return bool(analysis and len(analysis[2]) > 2)


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "unique_shortest_detour": _w_unique_detour,
    "multiple_shortest_paths": _w_multiple,
    "right_before_down_tie": _w_order_diff("DRLU"),
    "down_before_left_tie": _w_order_diff("RLDU"),
    "left_before_up_tie": _w_order_diff("RDUL"),
    "wall_forced_detour": _w_detour,
    "visible_nonpath_branches": _w_branches,
    "nonidentity_corridor": _w_nonidentity,
}

WITNESS_RIVALS = {
    "unique_shortest_detour": ["row_then_column"],
    "multiple_shortest_paths": ["all_shortest_cells"],
    "right_before_down_tie": ["down_before_right"],
    "down_before_left_tie": ["left_before_down"],
    "left_before_up_tie": ["up_before_left"],
    "wall_forced_detour": ["row_then_column"],
    "visible_nonpath_branches": ["fill_all_open"],
    "nonidentity_corridor": ["markers_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    official_query = oracle_output(query["input"])
    errors: list[str] = []
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != official_query:
                errors.append(f"demos do not rule out rival operation {name}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-degenerate maze input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx, sample_index, difficulty, overrides)
    color = ctx.draw_color("portal_color", exclude=(0, 5))
    profile = schedule_profile(seed, sample_index, difficulty)
    grid = _construct_scene(h, w, profile, color, ctx.draw_rng("layout"))

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("generator constructed an invalid lesson: " + "; ".join(errors))
    if profile == "unique_detour" and not _w_unique_detour(grid):
        raise AssertionError("scheduled unique profile did not realize a unique route")
    rival_order = _PROFILE_RIVAL_ORDER.get(profile)
    if rival_order and _output_for_order(grid, rival_order) == oracle_output(grid):
        raise AssertionError(f"scheduled profile {profile!r} did not separate its rival")
    return grid
