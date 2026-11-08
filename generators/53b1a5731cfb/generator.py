"""Generator for ``hard_p02`` — shortest path with a key, door, and portal.

Canonical rule: color 2 is the start and color 3 the goal.  Color 8 is wall,
color 4 is a key, color 5 is a locked door, and the two color-6 cells are a
portal pair.  The shortest stateful route must collect the key before crossing
the door and teleports between the portals.  Traversed zero cells become 7;
all markers remain unchanged.

The generated mazes exercise both canonical branches.  In ``key_door``
scenes, the key is on a side branch of the unique route to a locked door and
the first portal.  In ``portal_bypass`` scenes, the shortest portal route
correctly ignores a key/door side branch.  A separate portal-linked chamber
contains the goal, and unused maze branches rebut "paint every corridor".
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "53b1a5731cfb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # repair canonical key/door/portal semantics and input prior
RULE_HASH = "f8201177b934"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A color-8 walled maze has one start (2), goal (3), key (4), locked door "
    "(5), and a pair of portals (6). Find the shortest stateful route: collect "
    "the key before crossing the door, and entering either portal teleports to "
    "the other. Paint only traversed zero cells color 7; preserve all markers."
)

INVARIANTS = [
    "color 8 is the modal wall/background and forms the complete outer border",
    "exactly one start 2, goal 3, key 4, and door 5; exactly two portal-6 cells",
    "the shortest route always uses a portal and either uses both key+door or bypasses both",
    "the maze contains unused zero-corridor branches, so the output is not every zero cell",
]

# Only exact, recoverable axes are declared.  Maze topology, marker positions,
# detour length, and mirror orientation remain deterministic nuisance variation.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 9..13", "valid": "9..13"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 12..17", "valid": "12..17"},
    "route_mode": {
        "type": "str",
        "default": "alternates by sample_index: key_door|portal_bypass",
        "valid": "key_door|portal_bypass",
    },
}

_ALLOWED = frozenset({0, 2, 3, 4, 5, 6, 8})
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class _SearchResult:
    reachable: bool
    states: tuple[tuple[int, int, bool], ...]
    entered_cells: tuple[tuple[int, int], ...]
    used_key: bool
    used_door: bool
    used_portal: bool


def _positions(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _stateful_search(
    grid,
    *,
    allow_portal: bool = True,
    allow_door_after_key: bool = True,
) -> _SearchResult:
    """Python semantic mirror used only for structural validation.

    The canonical Racket program remains the sole output authority.  This
    helper records the entered cell separately from the post-teleport state so
    the key, door, and portal branches can be audited precisely.
    """
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    portals = _positions(grid, 6)
    if len(starts) != 1 or len(goals) != 1 or len(portals) != 2:
        return _SearchResult(False, (), (), False, False, False)

    start = (starts[0][0], starts[0][1], False)
    goal = goals[0]
    portal_other = {portals[0]: portals[1], portals[1]: portals[0]}
    queue = deque([start])
    parent: dict[tuple[int, int, bool], tuple[int, int, bool] | None] = {start: None}
    entered: dict[tuple[int, int, bool], tuple[int, int]] = {}
    end = None

    h, w = len(grid), len(grid[0])
    while queue:
        state = queue.popleft()
        r, c, has_key = state
        if (r, c) == goal:
            end = state
            break
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            cell = grid[nr][nc]
            if cell == 8:
                continue
            if cell == 5 and not (allow_door_after_key and has_key):
                continue
            key2 = has_key or cell == 4
            entered_cell = (nr, nc)
            dest = portal_other.get(entered_cell, entered_cell) if allow_portal else entered_cell
            next_state = (dest[0], dest[1], key2)
            if next_state in parent:
                continue
            parent[next_state] = state
            entered[next_state] = entered_cell
            queue.append(next_state)

    if end is None:
        return _SearchResult(False, (), (), False, False, False)

    states_rev = []
    entered_rev = []
    cur = end
    while cur is not None:
        states_rev.append(cur)
        if cur in entered:
            entered_rev.append(entered[cur])
        cur = parent[cur]
    states = tuple(reversed(states_rev))
    entered_cells = tuple(reversed(entered_rev))
    values = [grid[r][c] for r, c in entered_cells]
    used_key = 4 in values
    used_door = 5 in values
    used_portal = any(
        entered_cell != (state[0], state[1])
        for entered_cell, state in zip(entered_cells, states[1:])
    )
    return _SearchResult(True, states, entered_cells, used_key, used_door, used_portal)


def _node_graph(rows: list[int], cols: list[int], rng):
    """Randomized DFS perfect maze over lattice nodes; return adjacency + cells."""
    nodes = [(r, c) for r in rows for c in cols]
    by_index = {(ri, ci): (r, c) for ri, r in enumerate(rows) for ci, c in enumerate(cols)}
    start = rng.choice(nodes)
    stack = [start]
    seen = {start}
    adjacency = {node: set() for node in nodes}
    carved = set(nodes)

    row_index = {r: i for i, r in enumerate(rows)}
    col_index = {c: i for i, c in enumerate(cols)}
    while stack:
        node = stack[-1]
        ri, ci = row_index[node[0]], col_index[node[1]]
        options = []
        for dri, dci in _DIRS:
            nxt = by_index.get((ri + dri, ci + dci))
            if nxt is not None and nxt not in seen:
                options.append(nxt)
        if not options:
            stack.pop()
            continue
        nxt = rng.choice(options)
        seen.add(nxt)
        adjacency[node].add(nxt)
        adjacency[nxt].add(node)
        carved.add(((node[0] + nxt[0]) // 2, (node[1] + nxt[1]) // 2))
        stack.append(nxt)
    return adjacency, carved


def _tree_path(adjacency, start, goal) -> list[tuple[int, int]]:
    queue = deque([start])
    parent = {start: None}
    while queue:
        node = queue.popleft()
        if node == goal:
            break
        for nxt in adjacency[node]:
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    if goal not in parent:
        return []
    out = []
    cur = goal
    while cur is not None:
        out.append(cur)
        cur = parent[cur]
    return list(reversed(out))


def _component_from(adjacency, first, blocked: set[tuple[int, int]]) -> set[tuple[int, int]]:
    queue = deque([first])
    seen = {first}
    while queue:
        node = queue.popleft()
        for nxt in adjacency[node]:
            if nxt in blocked or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return seen


def _left_candidates(adjacency):
    """All start/key/door/portal placements with a true key detour."""
    nodes = list(adjacency)
    leaves = [node for node in nodes if len(adjacency[node]) == 1]
    endpoints = leaves if len(leaves) >= 2 else nodes
    candidates = []
    for start in endpoints:
        for portal in endpoints:
            if portal == start:
                continue
            path = _tree_path(adjacency, start, portal)
            if len(path) < 6:
                continue
            path_set = set(path)
            for junction_index in range(2, len(path) - 2):
                junction = path[junction_index]
                off_path = [n for n in adjacency[junction] if n not in path_set]
                for branch_first in off_path:
                    component = _component_from(adjacency, branch_first, path_set)
                    if not component:
                        continue
                    key = max(component, key=lambda n: len(_tree_path(adjacency, junction, n)))
                    detour = len(_tree_path(adjacency, junction, key)) - 1
                    if detour < 1:
                        continue
                    # Door is the first corridor edge after returning to the junction.
                    door_a, door_b = path[junction_index], path[junction_index + 1]
                    door = ((door_a[0] + door_b[0]) // 2, (door_a[1] + door_b[1]) // 2)
                    score = (len(path) - 1) + 2 * detour
                    candidates.append((score, start, key, door, portal, junction, detour))
    return candidates


def _left_bypass_candidates(adjacency):
    """Placements where the shortest portal route bypasses a key/door side branch."""
    nodes = list(adjacency)
    leaves = [node for node in nodes if len(adjacency[node]) == 1]
    endpoints = leaves if len(leaves) >= 2 else nodes
    candidates = []
    for start in endpoints:
        for portal in endpoints:
            if portal == start:
                continue
            main_path = _tree_path(adjacency, start, portal)
            if len(main_path) < 4:
                continue
            main_set = set(main_path)
            for junction_index in range(1, len(main_path) - 1):
                junction = main_path[junction_index]
                for branch_first in (n for n in adjacency[junction] if n not in main_set):
                    component = _component_from(adjacency, branch_first, main_set)
                    for leaf in component:
                        branch_path = _tree_path(adjacency, junction, leaf)
                        if len(branch_path) < 4:
                            continue
                        key = branch_path[1]
                        door_a, door_b = branch_path[2], branch_path[3]
                        door = ((door_a[0] + door_b[0]) // 2, (door_a[1] + door_b[1]) // 2)
                        score = (len(main_path) - 1) + (len(branch_path) - 1)
                        candidates.append((score, start, key, door, portal, junction, len(branch_path) - 1))
    return candidates


def _right_candidates(adjacency):
    nodes = list(adjacency)
    leaves = [node for node in nodes if len(adjacency[node]) == 1]
    endpoints = leaves if len(leaves) >= 2 else nodes
    candidates = []
    for portal in endpoints:
        for goal in endpoints:
            if portal == goal:
                continue
            path = _tree_path(adjacency, portal, goal)
            if len(path) >= 3:
                candidates.append((len(path) - 1, portal, goal))
    return candidates


def _pick_by_difficulty(candidates, difficulty, rng):
    """Choose from a score quantile while retaining layout variation."""
    ordered = sorted(candidates, key=lambda item: item[0])
    if not ordered:
        raise ValueError("no semantic placement candidates")
    n = len(ordered)
    if difficulty == "easy":
        pool = ordered[: max(1, n // 3)]
    elif difficulty == "hard":
        pool = ordered[max(0, (2 * n) // 3) :]
    else:
        pool = ordered[max(0, n // 4) : max(1, (3 * n) // 4)] or ordered
    return rng.choice(pool)


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror; generated mazes have a unique stateful route.

    The canonical Racket program remains the sole producer/output authority.
    """
    result = _stateful_search(grid)
    if not result.reachable:
        raise ValueError("goal is unreachable")
    out = [row[:] for row in grid]
    for r, c, _has_key in result.states:
        if grid[r][c] == 0:
            out[r][c] = 7
    return out


def observe_overrides(grid) -> dict[str, int | str]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    result = _stateful_search(grid)
    if not result.reachable or not result.used_portal:
        raise ValueError("grid has no lawful portal route")
    if result.used_key and result.used_door:
        route_mode = "key_door"
    elif not result.used_key and not result.used_door:
        route_mode = "portal_bypass"
    else:
        raise ValueError("shortest route uses only one of key/door")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "route_mode": route_mode}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]

    errors = []
    values = [value for row in grid for value in row]
    illegal = sorted(set(values) - _ALLOWED)
    if illegal:
        errors.append(f"illegal colors: {illegal}")
    if not (9 <= h <= 13 and 12 <= w <= 17):
        errors.append(f"shape {h}x{w} outside lawful range")
    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)):
        errors.append("top/bottom border must be all color 8")
    if any(grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)):
        errors.append("left/right border must be all color 8")
    for color, name, expected in ((2, "start", 1), (3, "goal", 1), (4, "key", 1), (5, "door", 1), (6, "portal", 2)):
        count = values.count(color)
        if count != expected:
            errors.append(f"expected {expected} {name} cell(s) in color {color}, got {count}")
    if values.count(8) <= values.count(0):
        errors.append("color 8 must be the modal wall/background")
    if errors:
        return errors

    result = _stateful_search(grid)
    if not result.reachable:
        errors.append("goal is not reachable under key/door/portal semantics")
        return errors
    if not result.used_portal:
        errors.append("shortest route does not use a portal teleport")
    if result.used_key != result.used_door:
        errors.append("shortest route uses only one of the key/door pair")

    traversed_zeros = {
        (state[0], state[1])
        for state in result.states
        if grid[state[0]][state[1]] == 0
    }
    all_zeros = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    if len(traversed_zeros) < 4:
        errors.append("route has too few paintable zero cells")
    if len(all_zeros - traversed_zeros) < 3:
        errors.append("maze lacks unused corridor distractors")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 9, 13)
    w = ctx.draw_int_diff("grid_w", 12, 17)
    # Four consecutive examples always contain both decisive canonical branches.
    # Reorder the same legal option set so draw_choice records the scheduled value
    # without bypassing GenCtx provenance; explicit overrides still take priority.
    desired_mode = "key_door" if sample_index % 2 == 0 else "portal_bypass"
    other_mode = "portal_bypass" if desired_mode == "key_door" else "key_door"
    chosen_index = ctx.draw_rng("route_mode").randrange(2)
    mode_options = [None, None]
    mode_options[chosen_index] = desired_mode
    mode_options[1 - chosen_index] = other_mode
    route_mode = ctx.draw_choice("route_mode", tuple(mode_options))
    rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}:{route_mode}")

    # Try several split/parity choices.  Every successful draw is a fresh object.
    for _attempt in range(80):
        split_lo = 5
        split_hi = w - 6
        if split_lo > split_hi:
            raise ValueError(f"grid width {w} too small for two maze chambers")
        split = rng.randint(split_lo, split_hi)
        rows = list(range(1, h - 1, 2))
        left_cols = list(range(1, split, 2))
        right_cols = list(range(split + 1, w - 1, 2))
        if len(rows) < 4 or len(left_cols) < 2 or len(right_cols) < 2:
            continue

        left_adj, left_carved = _node_graph(rows, left_cols, rng)
        right_adj, right_carved = _node_graph(rows, right_cols, rng)
        left_candidates = (
            _left_candidates(left_adj)
            if route_mode == "key_door"
            else _left_bypass_candidates(left_adj)
        )
        right_candidates = _right_candidates(right_adj)
        if not left_candidates or not right_candidates:
            continue

        _, start, key, door, portal_left, _junction, _detour = _pick_by_difficulty(
            left_candidates, difficulty, rng
        )
        _, portal_right, goal = _pick_by_difficulty(right_candidates, difficulty, rng)

        grid = full_grid(h, w, 8)
        for r, c in left_carved | right_carved:
            grid[r][c] = 0
        grid[start[0]][start[1]] = 2
        grid[goal[0]][goal[1]] = 3
        grid[key[0]][key[1]] = 4
        grid[door[0]][door[1]] = 5
        grid[portal_left[0]][portal_left[1]] = 6
        grid[portal_right[0]][portal_right[1]] = 6

        # Mirror nuisance variation prevents fixed-side shortcuts while keeping
        # exact grid_h/grid_w axes observable.
        if rng.randrange(2):
            grid = [list(reversed(row)) for row in grid]
        if rng.randrange(2):
            grid = list(reversed(grid))

        errors = self_check(grid)
        if not errors:
            observed = observe_overrides(grid)
            if observed["route_mode"] != route_mode:
                continue
            if _stateful_search(grid, allow_portal=False).reachable:
                continue
            if route_mode == "key_door" and _stateful_search(
                grid, allow_door_after_key=False
            ).reachable:
                continue
            return [row[:] for row in grid]

    raise ValueError("could not realize a lawful key-door-portal maze")
