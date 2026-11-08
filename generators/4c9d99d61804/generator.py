"""Generator for hard_n01 — shortest path with paired teleport portals.

The input contains one red(2) start, one green(3) goal, gray(5) walls, and
exactly two same-colored portal cells (7, 8, or 9).  Run four-neighbor BFS with
priority UP, DOWN, LEFT, RIGHT.  Stepping onto either portal immediately moves
the search state to its twin.  Paint only zero-valued cells on the selected
shortest route yellow(4); preserve every marker, wall, and portal.

Five consecutive sample profiles make the lesson falsifiable: one requires the
portal shortcut, one makes the portal a longer distractor, and three expose the
U>D, D>L, and L>R queue-priority decisions on equal shortest paths.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c9d99d61804"
TASK_ID = "4c9d99d61804"
VERSION = "3.0.0"
RULE_HASH = "bd90e027e0bf"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains exactly one red(2) start, one green(3) "
    "goal, gray(5) walls, and one pair of equal-colored portals chosen from "
    "7/8/9. Run four-neighbor BFS in up, down, left, right order. Entering a "
    "portal teleports to its twin before the state is queued. Paint only the "
    "intermediate 0-cells of the selected shortest route yellow(4), preserving "
    "start, goal, walls, and portals. A five-profile schedule proves that a "
    "portal can be either useful or irrelevant and disambiguates all three "
    "adjacent priority comparisons in the canonical BFS order."
)

INVARIANTS = [
    "0 is the modal background and 5 is the only wall color",
    "there is exactly one color-2 start and one color-3 goal",
    "exactly one color from 7/8/9 appears exactly twice as a portal pair",
    "all non-wall cells are ordinarily connected and the goal is reachable",
    "normal draws paint a nonempty shortest path and preserve every nonzero role",
]

_ALLOWED_HEIGHTS = (7, 8, 9)
_ALLOWED_WIDTHS = (10, 11, 12)
_PORTAL_COLORS = (7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted choice from 7|8|9",
        "valid": "7|8|9",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted choice from 10|11|12",
        "valid": "10|11|12",
    },
    "portal_color": {
        "type": "color",
        "default": "keyed choice from 7|8|9",
        "valid": "7|8|9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIRECTIONS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}
_OFFICIAL_ORDER = "UDLR"
_PROFILE_NAMES = (
    "portal_shortcut",
    "portal_distractor",
    "up_before_down_tie",
    "down_before_left_tie",
    "left_before_right_tie",
)
SCHEDULE_PROFILES = _PROFILE_NAMES


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    domains = {
        "grid_h": _ALLOWED_HEIGHTS,
        "grid_w": _ALLOWED_WIDTHS,
        "portal_color": _PORTAL_COLORS,
    }
    for name, allowed in domains.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}")


def _draw_choice_with_override(ctx, name: str, default_options: Sequence[int], full_options: Sequence[int]) -> int:
    options = full_options if ctx.overrides.get(name) is not None else default_options
    return int(ctx.draw_choice(name, options))


def _draw_dimensions(ctx, difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        height_options = (7, 8)
        width_options = (10, 11)
    elif difficulty == "hard":
        height_options = (8, 9)
        width_options = (11, 12)
    else:
        height_options = _ALLOWED_HEIGHTS
        width_options = _ALLOWED_WIDTHS
    h = _draw_choice_with_override(ctx, "grid_h", height_options, _ALLOWED_HEIGHTS)
    w = _draw_choice_with_override(ctx, "grid_w", width_options, _ALLOWED_WIDTHS)
    return h, w


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _positions_of(grid: Sequence[Sequence[int]], value: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell == value
    ]


def _portal_pair(grid: Sequence[Sequence[int]]) -> tuple[int, tuple[tuple[int, int], tuple[int, int]]] | None:
    found = [(color, _positions_of(grid, color)) for color in _PORTAL_COLORS]
    found = [(color, points) for color, points in found if points]
    if len(found) != 1 or len(found[0][1]) != 2:
        return None
    color, points = found[0]
    return color, (points[0], points[1])


def _portal_destination(
    position: tuple[int, int],
    pair: tuple[int, tuple[tuple[int, int], tuple[int, int]]] | None,
    *,
    enabled: bool,
) -> tuple[int, int]:
    if not enabled or pair is None:
        return position
    _, (first, second) = pair
    if position == first:
        return second
    if position == second:
        return first
    return position


def _bfs_trace(
    grid: Sequence[Sequence[int]],
    *,
    order: str = _OFFICIAL_ORDER,
    use_portals: bool = True,
) -> dict[str, Any]:
    starts = _positions_of(grid, 2)
    goals = _positions_of(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return {"path": None, "entered": {}, "teleport_used": False, "distance": None}
    start, goal = starts[0], goals[0]
    h, w = len(grid), len(grid[0])
    pair = _portal_pair(grid)
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    entered: dict[tuple[int, int], tuple[int, int]] = {}
    queue = deque([start])

    while queue and goal not in previous:
        current = queue.popleft()
        for direction in order:
            dr, dc = _DIRECTIONS[direction]
            nr, nc = current[0] + dr, current[1] + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
                continue
            entry = (nr, nc)
            nxt = _portal_destination(entry, pair, enabled=use_portals)
            if nxt not in previous:
                previous[nxt] = current
                entered[nxt] = entry
                queue.append(nxt)

    if goal not in previous:
        return {"path": None, "entered": entered, "teleport_used": False, "distance": None}

    reverse_path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = goal
    while current is not None:
        reverse_path.append(current)
        current = previous[current]
    path = tuple(reversed(reverse_path))
    teleport_used = any(entered.get(position) != position for position in path[1:])
    return {
        "path": path,
        "entered": entered,
        "teleport_used": teleport_used,
        "distance": len(path) - 1,
    }


def _paint_path(grid: Sequence[Sequence[int]], path: Iterable[tuple[int, int]] | None) -> list[list[int]]:
    output = [list(row) for row in grid]
    if path is None:
        return output
    for r, c in path:
        if output[r][c] == 0:
            output[r][c] = 4
    return output


def _output_for_order(
    grid: Sequence[Sequence[int]], order: str, *, use_portals: bool = True
) -> list[list[int]]:
    return _paint_path(grid, _bfs_trace(grid, order=order, use_portals=use_portals)["path"])


def oracle_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; the canonical Racket program is authoritative."""
    return _output_for_order(grid, _OFFICIAL_ORDER, use_portals=True)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Diagnostic mirror checked against the canonical Racket rule in smoke tests."""
    return oracle_output(grid)


def _plain_bfs_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _output_for_order(grid, _OFFICIAL_ORDER, use_portals=False)


def _forced_portal_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Plausible shortcut: force one teleport before accepting the goal."""
    starts = _positions_of(grid, 2)
    goals = _positions_of(grid, 3)
    pair = _portal_pair(grid)
    if len(starts) != 1 or len(goals) != 1 or pair is None:
        return [list(row) for row in grid]
    start, goal = starts[0], goals[0]
    h, w = len(grid), len(grid[0])
    initial = (start, False)
    target = (goal, True)
    previous: dict[
        tuple[tuple[int, int], bool], tuple[tuple[int, int], bool] | None
    ] = {initial: None}
    queue = deque([initial])

    while queue and target not in previous:
        current, used = queue.popleft()
        for direction in _OFFICIAL_ORDER:
            dr, dc = _DIRECTIONS[direction]
            nr, nc = current[0] + dr, current[1] + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
                continue
            entry = (nr, nc)
            nxt = _portal_destination(entry, pair, enabled=True)
            teleported = nxt != entry
            new_used = used or teleported
            if nxt == goal and not new_used:
                continue
            state = (nxt, new_used)
            if state not in previous:
                previous[state] = (current, used)
                queue.append(state)

    if target not in previous:
        return [list(row) for row in grid]
    reverse_positions: list[tuple[int, int]] = []
    state: tuple[tuple[int, int], bool] | None = target
    while state is not None:
        reverse_positions.append(state[0])
        state = previous[state]
    return _paint_path(grid, reversed(reverse_positions))


def _directed_graph(grid: Sequence[Sequence[int]]) -> dict[tuple[int, int], tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    pair = _portal_pair(grid)
    graph: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5:
                continue
            neighbors: list[tuple[int, int]] = []
            for direction in _OFFICIAL_ORDER:
                dr, dc = _DIRECTIONS[direction]
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5:
                    neighbors.append(
                        _portal_destination((nr, nc), pair, enabled=True)
                    )
            graph[(r, c)] = tuple(neighbors)
    return graph


def _distances(
    graph: dict[tuple[int, int], tuple[tuple[int, int], ...]],
    start: tuple[int, int],
) -> dict[tuple[int, int], int]:
    distance = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in graph.get(current, ()):
            if nxt not in distance:
                distance[nxt] = distance[current] + 1
                queue.append(nxt)
    return distance


def _all_shortest_cells_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    starts = _positions_of(grid, 2)
    goals = _positions_of(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return [list(row) for row in grid]
    graph = _directed_graph(grid)
    reverse: dict[tuple[int, int], list[tuple[int, int]]] = {node: [] for node in graph}
    for source, targets in graph.items():
        for target in targets:
            reverse.setdefault(target, []).append(source)
    reverse_graph = {node: tuple(sources) for node, sources in reverse.items()}
    from_start = _distances(graph, starts[0])
    to_goal = _distances(reverse_graph, goals[0])
    total = from_start.get(goals[0])
    if total is None:
        return [list(row) for row in grid]
    cells = [
        node
        for node, distance in from_start.items()
        if node in to_goal and distance + to_goal[node] == total
    ]
    return _paint_path(grid, cells)


def _identity_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _build_portal_shortcut(h: int, w: int, portal_color: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mid = h // 2
    barrier = w // 2
    grid[mid][1] = 2
    grid[mid][w - 2] = 3
    for r in range(1, h - 1):
        grid[r][barrier] = 5
    grid[1][2] = portal_color
    grid[h - 2][w - 3] = portal_color
    return grid


def _build_portal_distractor(h: int, w: int, portal_color: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mid = h // 2
    grid[mid][1] = 2
    grid[mid][w - 2] = 3
    for r in range(1, mid):
        for c in range(w // 2 - 1, w // 2 + 2):
            grid[r][c] = 5
    grid[h - 2][w - 3] = portal_color
    grid[h - 2][w - 2] = portal_color
    return grid


def _build_up_before_down(h: int, w: int, portal_color: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mid = h // 2
    grid[mid][1] = 2
    grid[mid][w - 2] = 3
    for c in range(2, w - 2):
        grid[mid][c] = 5
    grid[0][w - 2] = portal_color
    grid[0][w - 1] = portal_color
    return grid


def _build_down_before_left(h: int, w: int, portal_color: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    top, bottom = 1, h - 2
    left, right = 1, w - 3
    grid[top][right] = 2
    grid[bottom][left] = 3
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            grid[r][c] = 5
    grid[0][w - 2] = portal_color
    grid[0][w - 1] = portal_color
    return grid


def _build_left_before_right(h: int, w: int, portal_color: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    top, bottom = 1, h - 2
    center = w // 2
    grid[top][center] = 2
    grid[bottom][center] = 3
    for r in range(top + 1, bottom):
        for c in range(center - 1, center + 2):
            grid[r][c] = 5
    grid[0][w - 2] = portal_color
    grid[0][w - 1] = portal_color
    return grid


_PROFILE_BUILDERS: dict[str, Callable[[int, int, int], list[list[int]]]] = {
    "portal_shortcut": _build_portal_shortcut,
    "portal_distractor": _build_portal_distractor,
    "up_before_down_tie": _build_up_before_down,
    "down_before_left_tie": _build_down_before_left,
    "left_before_right_tie": _build_left_before_right,
}


def _profile_matches(grid: Sequence[Sequence[int]], profile: str) -> bool:
    official = oracle_output(grid)
    trace = _bfs_trace(grid)
    if trace["path"] is None or official == [list(row) for row in grid]:
        return False
    if profile == "portal_shortcut":
        plain = _bfs_trace(grid, use_portals=False)
        return (
            trace["teleport_used"]
            and plain["path"] is not None
            and trace["distance"] < plain["distance"]
            and official != _plain_bfs_output(grid)
        )
    if profile == "portal_distractor":
        return (
            not trace["teleport_used"]
            and official == _plain_bfs_output(grid)
            and official != _forced_portal_output(grid)
        )
    if profile == "up_before_down_tie":
        return (
            not trace["teleport_used"]
            and official != _output_for_order(grid, "DULR")
            and official != _all_shortest_cells_output(grid)
        )
    if profile == "down_before_left_tie":
        return (
            not trace["teleport_used"]
            and official != _output_for_order(grid, "ULDR")
            and official != _all_shortest_cells_output(grid)
        )
    if profile == "left_before_right_tie":
        return (
            not trace["teleport_used"]
            and official != _output_for_order(grid, "UDRL")
            and official != _all_shortest_cells_output(grid)
        )
    return False


def _nonwall_connected(grid: Sequence[Sequence[int]]) -> bool:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 5
    }
    if not cells:
        return False
    start = min(cells)
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRECTIONS.values():
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _add_isolated_walls(
    grid: list[list[int]], profile: str, rng, difficulty: Any
) -> list[list[int]]:
    desired = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 2)
    desired += rng.randint(0, 1)
    h, w = len(grid), len(grid[0])
    protected = set(_bfs_trace(grid)["path"] or ())
    protected.update(_positions_of(grid, 2))
    protected.update(_positions_of(grid, 3))
    pair = _portal_pair(grid)
    if pair is not None:
        protected.update(pair[1])

    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and (r, c) not in protected
    ]
    rng.shuffle(candidates)
    added = 0
    for r, c in candidates:
        if added >= desired:
            break
        if any(
            0 <= r + dr < h
            and 0 <= c + dc < w
            and grid[r + dr][c + dc] == 5
            for dr, dc in _DIRECTIONS.values()
        ):
            continue
        trial = [row[:] for row in grid]
        trial[r][c] = 5
        counts = {value: sum(row.count(value) for row in trial) for value in (0, 5)}
        if counts[0] <= counts[5] or not _nonwall_connected(trial):
            continue
        if not _profile_matches(trial, profile):
            continue
        grid = trial
        added += 1
    return grid


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    pair = _portal_pair(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "portal_color": pair[0] if pair is not None else -1,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar and reject malformed lessons."""
    del difficulty
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
    if h not in _ALLOWED_HEIGHTS or w not in _ALLOWED_WIDTHS:
        errors.append(
            f"grid dimensions {h}x{w} must use height {_ALLOWED_HEIGHTS} and width {_ALLOWED_WIDTHS}"
        )

    flat = [int(value) for row in grid for value in row]
    if flat.count(2) != 1:
        errors.append(f"expected exactly one color-2 start, found {flat.count(2)}")
    if flat.count(3) != 1:
        errors.append(f"expected exactly one color-3 goal, found {flat.count(3)}")

    pair = _portal_pair(grid)
    if pair is None:
        portal_counts = {color: flat.count(color) for color in _PORTAL_COLORS}
        errors.append(
            "expected exactly one portal color from 7/8/9 appearing twice; "
            f"found {portal_counts}"
        )
        portal_color = None
    else:
        portal_color = pair[0]

    allowed = {0, 2, 3, 5}
    if portal_color is not None:
        allowed.add(portal_color)
    unexpected = sorted(set(flat) - allowed)
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}")
    if flat.count(0) <= flat.count(5):
        errors.append("color 0 must remain the modal background rather than gray walls")
    if flat.count(5) < 4:
        errors.append("expected at least four gray(5) wall cells")
    if not _nonwall_connected(grid):
        errors.append("all non-wall cells must form one ordinary 4-connected component")

    if flat.count(2) == 1 and flat.count(3) == 1 and pair is not None:
        trace = _bfs_trace(grid)
        if trace["path"] is None:
            errors.append("the color-3 goal must be reachable under portal BFS")
        else:
            painted = sum(
                1 for r, c in trace["path"] if grid[r][c] == 0
            )
            if painted < 2:
                errors.append("the selected route must paint at least two background cells")
        start, goal = _positions_of(grid, 2)[0], _positions_of(grid, 3)[0]
        if abs(start[0] - goal[0]) + abs(start[1] - goal[1]) < 4:
            errors.append("start and goal must be separated by Manhattan distance at least four")

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for name in AXES:
            if requested.get(name) is not None and observed.get(name) != requested[name]:
                errors.append(
                    f"override {name}={requested[name]!r} realized as {observed.get(name)!r}"
                )
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Return targeted malformed scenes used to prove checker sensitivity.

    The fixtures attack distinct parts of the input grammar rather than merely
    changing a random pixel.  In particular, ``unpaired_replacement_color`` is
    the required negative recombination: one portal endpoint is replaced by a
    color absent from every other scene part, so no surviving cue can complete
    the pair.
    """
    base = _build_portal_shortcut(8, 12, 7)
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_goal = [row[:] for row in base]
    goal = _positions_of(missing_goal, 3)[0]
    missing_goal[goal[0]][goal[1]] = 0
    fixtures.append(("missing_goal", missing_goal))

    unpaired_replacement = [row[:] for row in base]
    portal = _positions_of(unpaired_replacement, 7)[0]
    unpaired_replacement[portal[0]][portal[1]] = 6
    fixtures.append(("unpaired_replacement_color", unpaired_replacement))

    split_portals = [row[:] for row in base]
    portal = _positions_of(split_portals, 7)[0]
    split_portals[portal[0]][portal[1]] = 8
    fixtures.append(("split_portal_colors", split_portals))

    unexpected_yellow = [row[:] for row in base]
    yellow_cell = next(
        (r, c)
        for r, row in enumerate(unexpected_yellow)
        for c, value in enumerate(row)
        if value == 0
    )
    unexpected_yellow[yellow_cell[0]][yellow_cell[1]] = 4
    fixtures.append(("yellow_already_in_input", unexpected_yellow))

    disconnected = [row[:] for row in base]
    separator_row = len(disconnected) // 2 + 1
    disconnected[separator_row] = [5] * len(disconnected[0])
    fixtures.append(("disconnected_floor_regions", disconnected))

    short_route = [row[:] for row in base]
    old_goal = _positions_of(short_route, 3)[0]
    start = _positions_of(short_route, 2)[0]
    short_route[old_goal[0]][old_goal[1]] = 0
    short_route[start[0] - 1][start[1]] = 3
    fixtures.append(("start_goal_too_close", short_route))

    too_few_walls = [row[:] for row in base]
    for r, c in _positions_of(too_few_walls, 5)[3:]:
        too_few_walls[r][c] = 0
    fixtures.append(("too_few_walls", too_few_walls))

    return fixtures


def strict_canonical_like(grid) -> list[str]:
    errors = list(self_check(grid))
    if errors:
        return errors
    flat = [int(value) for row in grid for value in row]
    pair = _portal_pair(grid)
    assert pair is not None
    expected_palette = {0, 2, 3, 5, pair[0]}
    if set(flat) != expected_palette:
        errors.append(
            f"expected exact five-role palette {sorted(expected_palette)}, got {sorted(set(flat))}"
        )
    output = oracle_output(grid)
    if output == [list(row) for row in grid]:
        errors.append("ordinary lesson must not be an identity transformation")
    changed = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if output[r][c] != value
    ]
    if changed and any(grid[r][c] != 0 or output[r][c] != 4 for r, c in changed):
        errors.append("the output may change only 0-cells to yellow(4)")
    for color in (2, 3, 5, pair[0]):
        if _positions_of(grid, color) != _positions_of(output, color):
            errors.append(f"output failed to preserve color-{color} role positions")
    return errors


def _w_portal_shortcut(grid: Sequence[Sequence[int]]) -> bool:
    trace = _bfs_trace(grid)
    plain = _bfs_trace(grid, use_portals=False)
    return bool(
        trace["path"] is not None
        and plain["path"] is not None
        and trace["teleport_used"]
        and trace["distance"] < plain["distance"]
        and oracle_output(grid) != _plain_bfs_output(grid)
    )


def _w_portal_distractor(grid: Sequence[Sequence[int]]) -> bool:
    trace = _bfs_trace(grid)
    return bool(
        trace["path"] is not None
        and not trace["teleport_used"]
        and oracle_output(grid) != _forced_portal_output(grid)
    )


def _w_up_before_down(grid: Sequence[Sequence[int]]) -> bool:
    return oracle_output(grid) != _output_for_order(grid, "DULR")


def _w_down_before_left(grid: Sequence[Sequence[int]]) -> bool:
    return oracle_output(grid) != _output_for_order(grid, "ULDR")


def _w_left_before_right(grid: Sequence[Sequence[int]]) -> bool:
    return oracle_output(grid) != _output_for_order(grid, "UDRL")


def _w_multiple_shortest(grid: Sequence[Sequence[int]]) -> bool:
    return oracle_output(grid) != _all_shortest_cells_output(grid)


def _w_nonidentity(grid: Sequence[Sequence[int]]) -> bool:
    return oracle_output(grid) != [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "ignore_portals": _plain_bfs_output,
    "always_route_via_portal": _forced_portal_output,
    "down_before_up": lambda grid: _output_for_order(grid, "DULR"),
    "left_before_down": lambda grid: _output_for_order(grid, "ULDR"),
    "right_before_left": lambda grid: _output_for_order(grid, "UDRL"),
    "paint_all_shortest_cells": _all_shortest_cells_output,
    "markers_only": _identity_output,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All four fit every supplied canonical pair; generated counterexamples are
# therefore required to establish the full selected rule rather than a shortcut.
CANONICAL_SHORTCUTS = {
    "always_route_via_portal": _forced_portal_output,
    "down_before_up": SEMANTIC_RIVALS["down_before_up"],
    "left_before_down": SEMANTIC_RIVALS["left_before_down"],
    "right_before_left": SEMANTIC_RIVALS["right_before_left"],
}

SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "portal_shortcut_selected": _w_portal_shortcut,
    "portal_distractor_rejected": _w_portal_distractor,
    "up_before_down_tie": _w_up_before_down,
    "down_before_left_tie": _w_down_before_left,
    "left_before_right_tie": _w_left_before_right,
    "multiple_shortest_paths_single_choice": _w_multiple_shortest,
    "nonidentity_yellow_route": _w_nonidentity,
}

WITNESS_RIVALS = {
    "portal_shortcut_selected": ["ignore_portals"],
    "portal_distractor_rejected": ["always_route_via_portal"],
    "up_before_down_tie": ["down_before_up", "paint_all_shortest_cells"],
    "down_before_left_tie": ["left_before_down", "paint_all_shortest_cells"],
    "left_before_right_tie": ["right_before_left", "paint_all_shortest_cells"],
    "multiple_shortest_paths_single_choice": ["paint_all_shortest_cells"],
    "nonidentity_yellow_route": ["markers_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must be a mapping containing an input grid"]
    errors: list[str] = []
    official_query = oracle_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                isinstance(demo, dict)
                and "input" in demo
                and "output" in demo
                and rival(demo["input"]) == demo["output"]
                for demo in demos
            )
            if survives and rival(query["input"]) != official_query:
                errors.append(f"demonstrations do not rule out rival operation {name}")
        except Exception as exc:
            errors.append(f"rival operation {name} raised {type(exc).__name__}: {exc}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, profile-certified portal-path input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx, difficulty)
    portal_color = _draw_choice_with_override(
        ctx, "portal_color", _PORTAL_COLORS, _PORTAL_COLORS
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    grid = _PROFILE_BUILDERS[profile](h, w, portal_color)
    grid = _add_isolated_walls(grid, profile, ctx.draw_rng("extra_walls"), difficulty)

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    if not _profile_matches(grid, profile):
        raise AssertionError(f"scheduled profile {profile!r} lost its semantic discriminator")
    return grid
