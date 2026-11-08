"""Generator for ARC task 671a9af906aa — shortest path with a key and door.

Color 2 marks the start, 3 the goal, 4 the key, 5 a locked door, and 8
walls.  The authoritative rule finds the shortest orthogonal route in the
state space ``(row, column, has_key)``: a door may be entered only after the
key has been visited.  Traversed zero cells become 7 and every marker stays
unchanged.  If no lawful route exists, the input is returned unchanged.

The original sampler placed markers and walls independently, so most examples
had little relationship to the stateful rule.  This reviewed generator builds
perfect mazes and schedules three semantic profiles instead:

``key_detour``
    The only route to the goal crosses a locked door, while the key lies on a
    side branch before it.  The solver must detour, return, and then use the
    door.  This refutes treating a key anywhere on the board as already held.

``unreachable``
    The key is behind the only door on the start-goal route.  No lawful route
    exists, so the output is unchanged.  This exercises the authority's empty
    path branch.

``key_bypass``
    The shortest route ignores a key/door side branch.  This refutes the
    canonical-compatible shortcut "always visit the key first".
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, NamedTuple, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "671a9af906aa"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"
RULE_HASH = "09280085884a"
EXAMPLES_NEEDED = 5
# The canonical authority intentionally returns the input unchanged when the
# key is trapped behind its own locked door.  Runner materialization must keep
# that branch rather than silently rejecting it as a degenerate identity pair.
ALLOW_IDENTITY_OUTPUT = True
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "In a color-8 maze, find the shortest route from start 2 to goal 3 in "
    "(position, has-key) state space.  Color 4 grants the key needed to enter "
    "door 5.  Paint only traversed zero cells 7; preserve markers, and leave "
    "the grid unchanged when the goal is unreachable."
)

INVARIANTS = [
    "the complete outer border is color 8 and color 8 is the modal input color",
    "there is exactly one start 2, goal 3, key 4, and door 5",
    "the input palette is exactly a subset of {0,2,3,4,5,8}",
    "reachable routes either use both key and door or bypass both",
    "unreachable scenes return unchanged under the canonical rule",
    "reachable scenes retain unused zero-corridor distractors",
]

SCHEDULE_PROFILES = ("key_detour", "unreachable", "key_bypass")
_ROUTE_CYCLE = ("key_detour", "key_bypass", "key_detour", "key_bypass", "unreachable")

# Only controls that are exact and recoverable from the generated grid are
# public axes.  Topology, route length, branch shape, and mirror orientation are
# deterministic nuisance variation.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7-row scenes four times in five; otherwise difficulty-scheduled",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9..11 columns four times in five; otherwise difficulty-scheduled",
        "valid": "9..17",
    },
    "route_mode": {
        "type": "str",
        "default": "five-scene cycle with two key_detours, two key_bypasses, and one unreachable",
        "valid": "key_detour|unreachable|key_bypass",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ALLOWED = frozenset({0, 2, 3, 4, 5, 8})
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class _SearchResult(NamedTuple):
    reachable: bool
    states: tuple[tuple[int, int, bool], ...]
    used_key: bool
    used_door: bool


def _positions(grid: Sequence[Sequence[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _stateful_search(
    grid: Sequence[Sequence[int]],
    *,
    doors_open_from_start: bool = False,
    doors_never_open: bool = False,
) -> _SearchResult:
    """Mirror the canonical BFS, including its neighbor order and state key."""
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return _SearchResult(False, (), False, False)

    start = (starts[0][0], starts[0][1], False)
    goal = goals[0]
    queue = deque([start])
    parent: dict[tuple[int, int, bool], tuple[int, int, bool] | None] = {start: None}
    end: tuple[int, int, bool] | None = None
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
            new_key = has_key or cell == 4
            if cell == 5:
                if doors_never_open:
                    continue
                if not doors_open_from_start and not new_key:
                    continue
            nxt = (nr, nc, new_key)
            if nxt in parent:
                continue
            parent[nxt] = state
            queue.append(nxt)

    if end is None:
        return _SearchResult(False, (), False, False)

    reversed_states: list[tuple[int, int, bool]] = []
    cur: tuple[int, int, bool] | None = end
    while cur is not None:
        reversed_states.append(cur)
        cur = parent[cur]
    states = tuple(reversed(reversed_states))
    values = [grid[r][c] for r, c, _ in states]
    return _SearchResult(True, states, 4 in values, 5 in values)


def _paint_states(
    grid: Sequence[Sequence[int]],
    states: Iterable[tuple[int, int, bool]] | None,
) -> list[list[int]]:
    out = [list(row) for row in grid]
    if states is None:
        return out
    for r, c, _has_key in states:
        if grid[r][c] == 0:
            out[r][c] = 7
    return out


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Python test mirror; the pinned Racket rule remains output authority."""
    structural = _basic_grid_errors(grid)
    if structural:
        raise ValueError("invalid grid for rule_mirror: " + "; ".join(structural))
    result = _stateful_search(grid)
    return _paint_states(grid, result.states if result.reachable else None)


def _coordinate_path(
    grid: Sequence[Sequence[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    door_open: bool,
) -> list[tuple[int, int]] | None:
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for dr, dc in _DIRS:
            nxt = (point[0] + dr, point[1] + dc)
            if not (0 <= nxt[0] < h and 0 <= nxt[1] < w) or nxt in parent:
                continue
            cell = grid[nxt[0]][nxt[1]]
            if cell == 8 or (cell == 5 and not door_open):
                continue
            parent[nxt] = point
            queue.append(nxt)
    if goal not in parent:
        return None
    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path))


def _global_key_unlock_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Wrong rule: merely seeing a key on the board unlocks the door."""
    result = _stateful_search(grid, doors_open_from_start=bool(_positions(grid, 4)))
    return _paint_states(grid, result.states if result.reachable else None)


def _door_is_wall_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Wrong rule: a door is impassable even after the key is collected."""
    result = _stateful_search(grid, doors_never_open=True)
    return _paint_states(grid, result.states if result.reachable else None)


def _always_visit_key_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Wrong rule: force start-to-key, then key-to-goal, regardless of length.

    This shortcut fits every public training pair but fails the public query,
    whose shortest route correctly bypasses the irrelevant key and door.
    """
    starts, keys, goals = _positions(grid, 2), _positions(grid, 4), _positions(grid, 3)
    if len(starts) != 1 or len(keys) != 1 or len(goals) != 1:
        return [list(row) for row in grid]
    first = _coordinate_path(grid, starts[0], keys[0], door_open=False)
    if first is None:
        return [list(row) for row in grid]
    second = _coordinate_path(grid, keys[0], goals[0], door_open=True)
    if second is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    for r, c in first + second[1:]:
        if grid[r][c] == 0:
            out[r][c] = 7
    return out


SEMANTIC_RIVALS: dict[
    str, Callable[[Sequence[Sequence[int]]], list[list[int]]]
] = {
    "global_key_unlock": _global_key_unlock_rival,
    "door_is_wall": _door_is_wall_rival,
    "always_visit_key": _always_visit_key_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"always_visit_key": _always_visit_key_rival}


def _node_graph(rows: Sequence[int], cols: Sequence[int], rng):
    """Build a randomized DFS perfect maze over odd/even lattice nodes."""
    nodes = [(r, c) for r in rows for c in cols]
    row_index = {r: i for i, r in enumerate(rows)}
    col_index = {c: i for i, c in enumerate(cols)}
    by_index = {
        (ri, ci): (r, c)
        for ri, r in enumerate(rows)
        for ci, c in enumerate(cols)
    }
    start = rng.choice(nodes)
    stack = [start]
    seen = {start}
    adjacency = {node: set() for node in nodes}
    carved = set(nodes)

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


def _endpoint_pool(adjacency) -> list[tuple[int, int]]:
    leaves = [node for node, neighbors in adjacency.items() if len(neighbors) == 1]
    return leaves if len(leaves) >= 2 else list(adjacency)


def _key_detour_candidates(adjacency):
    """Placements where key detour + locked-door crossing are both mandatory."""
    endpoints = _endpoint_pool(adjacency)
    candidates = []
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if len(main) < 4:
                continue
            main_set = set(main)
            for junction_index in range(1, len(main) - 1):
                junction = main[junction_index]
                for branch_first in (n for n in adjacency[junction] if n not in main_set):
                    component = _component_from(adjacency, branch_first, main_set)
                    if not component:
                        continue
                    key = max(
                        component,
                        key=lambda node: len(_tree_path(adjacency, junction, node)),
                    )
                    detour = len(_tree_path(adjacency, junction, key)) - 1
                    door_a, door_b = main[junction_index], main[junction_index + 1]
                    door = ((door_a[0] + door_b[0]) // 2, (door_a[1] + door_b[1]) // 2)
                    score = (len(main) - 1) + 2 * detour
                    candidates.append((score, start, goal, key, door))
    return candidates


def _unreachable_candidates(adjacency):
    """Placements where the only key is on the far side of its locked door."""
    endpoints = _endpoint_pool(adjacency)
    candidates = []
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if len(main) < 4:
                continue
            for edge_index in range(1, len(main) - 1):
                before, after = main[edge_index], main[edge_index + 1]
                far_component = _component_from(adjacency, after, {before})
                key_options = [node for node in far_component if node != goal]
                if not key_options:
                    continue
                key = max(
                    key_options,
                    key=lambda node: len(_tree_path(adjacency, after, node)),
                )
                door = ((before[0] + after[0]) // 2, (before[1] + after[1]) // 2)
                score = len(main) - 1
                candidates.append((score, start, goal, key, door))
    return candidates


def _key_bypass_candidates(adjacency):
    """Placements where the shortest route ignores a key/door side branch."""
    endpoints = _endpoint_pool(adjacency)
    candidates = []
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if len(main) < 4:
                continue
            main_set = set(main)
            for junction_index in range(1, len(main) - 1):
                junction = main[junction_index]
                for branch_first in (n for n in adjacency[junction] if n not in main_set):
                    component = _component_from(adjacency, branch_first, main_set)
                    for leaf in component:
                        branch = _tree_path(adjacency, junction, leaf)
                        if len(branch) < 3:
                            continue
                        # The key is reachable at the first branch node; the door
                        # is one edge deeper, so neither affects the main route.
                        key = branch[1]
                        door_a, door_b = branch[1], branch[2]
                        door = ((door_a[0] + door_b[0]) // 2, (door_a[1] + door_b[1]) // 2)
                        score = (len(main) - 1) + 2 * (len(branch) - 1)
                        candidates.append((score, start, goal, key, door))
    return candidates


def _pick_by_difficulty(candidates, difficulty: Any, rng):
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


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label, lo, hi in (("grid_h", 7, 13), ("grid_w", 9, 17)):
        value = overrides.get(label)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{label} must be in {lo}..{hi}")

    mode = overrides.get("route_mode")
    if mode is not None:
        if not isinstance(mode, str) or mode not in SCHEDULE_PROFILES:
            raise ValueError(
                "route_mode must be one of " + "|".join(SCHEDULE_PROFILES)
            )


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Every consecutive five examples contain all three semantic branches."""
    del seed
    _difficulty_band(difficulty)
    return _ROUTE_CYCLE[int(sample_index) % len(_ROUTE_CYCLE)]


def _scheduled_choice(ctx, label: str, options: Sequence[Any], scheduled: Any):
    """Record a full-domain exact draw while deterministically scheduling it.

    ``random.choice`` selects the same index as ``randrange`` on a fresh RNG.
    Placing the scheduled value at that index keeps the complete legal option
    set visible to provenance/override tooling without bypassing ``GenCtx``.
    """
    options = tuple(options)
    if scheduled not in options:
        raise ValueError(f"scheduled value {scheduled!r} not in {label} domain")
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)

    chosen_index = ctx.draw_rng(label).randrange(len(options))
    remaining = [option for option in options if option != scheduled]
    arranged: list[Any] = [None] * len(options)
    arranged[chosen_index] = scheduled
    cursor = 0
    for index in range(len(arranged)):
        if arranged[index] is None:
            arranged[index] = remaining[cursor]
            cursor += 1
    return ctx.draw_choice(label, tuple(arranged))


def _scheduled_shape(sample_index: int, band: str) -> tuple[int, int]:
    # Rotate the enlarged slot across the five route slots over 25 scenes.
    # A fixed slot would make size perfectly predict the unreachable branch.
    # Each profile retains 80% canonical-size support; any six-scene window
    # contains at most two enlarged scenes, preserving MIN_STRICT_FRAC.
    index = int(sample_index)
    enlarged_slot = (4 - index // 5) % 5
    if index % 5 != enlarged_slot:
        canonical_widths = (9, 11, 10, 11)
        return 7, canonical_widths[int(sample_index) % len(canonical_widths)]

    extras = {
        "easy": ((8, 12), (9, 13), (8, 14), (10, 12)),
        "medium": ((9, 13), (10, 14), (11, 15), (9, 16)),
        "hard": ((11, 15), (12, 16), (13, 17), (12, 14)),
    }
    cycle = (int(sample_index) // 5) % len(extras[band])
    return extras[band][cycle]


def _lattice_coordinates(length: int, rng) -> list[int]:
    # Odd dimensions have a centered odd lattice.  Even dimensions admit two
    # mirror-equivalent offsets, selected as nuisance variation.
    offset = 1 if length % 2 else rng.choice((1, 2))
    return list(range(offset, length - 1, 2))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, semantically classified maze input."""
    _validate_call(difficulty, overrides)
    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _scheduled_shape(sample_index, band)
    h = int(_scheduled_choice(ctx, "grid_h", tuple(range(7, 14)), scheduled_h))
    w = int(_scheduled_choice(ctx, "grid_w", tuple(range(9, 18)), scheduled_w))
    scheduled_mode = schedule_profile(seed, sample_index, difficulty)
    route_mode = str(
        _scheduled_choice(ctx, "route_mode", SCHEDULE_PROFILES, scheduled_mode)
    )

    candidate_fn = {
        "key_detour": _key_detour_candidates,
        "unreachable": _unreachable_candidates,
        "key_bypass": _key_bypass_candidates,
    }[route_mode]

    for attempt in range(240):
        rng = ctx.draw_rng(f"layout:{band}:{route_mode}:{attempt}")
        rows = _lattice_coordinates(h, rng)
        cols = _lattice_coordinates(w, rng)
        if len(rows) < 3 or len(cols) < 4:
            continue
        adjacency, carved = _node_graph(rows, cols, rng)
        candidates = candidate_fn(adjacency)
        if not candidates:
            continue
        _score, start, goal, key, door = _pick_by_difficulty(
            candidates, difficulty, rng
        )

        grid = full_grid(h, w, 8)
        for r, c in carved:
            grid[r][c] = 0
        grid[start[0]][start[1]] = 2
        grid[goal[0]][goal[1]] = 3
        grid[key[0]][key[1]] = 4
        grid[door[0]][door[1]] = 5

        if rng.randrange(2):
            grid = [list(reversed(row)) for row in grid]
        if rng.randrange(2):
            grid = list(reversed(grid))

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            continue
        observed = observe_overrides(grid)
        if observed != {"grid_h": h, "grid_w": w, "route_mode": route_mode}:
            continue

        truth = rule_mirror(grid)
        if route_mode == "key_detour":
            if truth == _global_key_unlock_rival(grid):
                continue
            if truth == _door_is_wall_rival(grid):
                continue
        elif route_mode == "unreachable":
            if truth != grid or truth == _global_key_unlock_rival(grid):
                continue
        else:  # key_bypass
            if truth == _always_visit_key_rival(grid):
                continue
        return [row[:] for row in grid]

    raise RuntimeError(
        f"could not construct a lawful {route_mode} maze at {h}x{w}"
    )


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the reviewed task manifold, including all canonical inputs."""
    del meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    try:
        _difficulty_band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 13 and 9 <= w <= 17):
        errors.append(f"shape {h}x{w} outside 7..13 by 9..17")

    values = [value for row in grid for value in row]
    illegal = sorted(set(values) - _ALLOWED)
    if illegal:
        errors.append(f"illegal input colors: {illegal}")

    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)):
        errors.append("top and bottom borders must be all color 8")
    if any(grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)):
        errors.append("left and right borders must be all color 8")

    for color, name in ((2, "start"), (3, "goal"), (4, "key"), (5, "door")):
        count = values.count(color)
        if count != 1:
            errors.append(f"expected exactly one {name} color-{color} cell, found {count}")
    if values.count(8) <= values.count(0):
        errors.append("color 8 must be more frequent than color 0")
    if errors:
        return errors

    result = _stateful_search(grid)
    if result.reachable and result.used_key != result.used_door:
        errors.append("shortest route uses only one of key and door")
    if result.reachable:
        traversed_zeros = {
            (r, c) for r, c, _ in result.states if grid[r][c] == 0
        }
        all_zeros = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 0
        }
        if len(traversed_zeros) < 2:
            errors.append("reachable route has fewer than two paintable zero cells")
        if len(all_zeros - traversed_zeros) < 2:
            errors.append("reachable maze lacks unused zero-corridor distractors")
    return errors


def _classify(grid: Sequence[Sequence[int]]) -> str:
    result = _stateful_search(grid)
    if not result.reachable:
        return "unreachable"
    if result.used_key and result.used_door:
        return "key_detour"
    if not result.used_key and not result.used_door:
        return "key_bypass"
    return "partial"


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    mode = _classify(grid)
    if mode not in SCHEDULE_PROFILES:
        raise ValueError(f"grid has unsupported route classification {mode!r}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "route_mode": mode}


def strict_canonical_like(grid) -> list[str]:
    errors = list(self_check(grid))
    if not errors and not (len(grid) == 7 and len(grid[0]) in (9, 10, 11)):
        errors.append("shape is outside the canonical 7x9..11 support")
    return errors


def _witness_mode(mode: str, rivals: Sequence[str]):
    def witness(grid: Sequence[Sequence[int]]) -> bool:
        if self_check(grid) or _classify(grid) != mode:
            return False
        truth = rule_mirror(grid)
        return all(SEMANTIC_RIVALS[name](grid) != truth for name in rivals)

    return witness


SEMANTIC_WITNESSES = {
    "key_detour_requires_possession": _witness_mode(
        "key_detour", ("global_key_unlock", "door_is_wall")
    ),
    "unreachable_key_behind_door": _witness_mode(
        "unreachable", ("global_key_unlock",)
    ),
    "shortest_route_bypasses_key": _witness_mode(
        "key_bypass", ("always_visit_key",)
    ),
}
WITNESS_RIVALS = {
    "key_detour_requires_possession": ["global_key_unlock", "door_is_wall"],
    "unreachable_key_behind_door": ["global_key_unlock"],
    "shortest_route_bypasses_key": ["always_visit_key"],
}


def _pair_errors(pair: Any, label: str, *, output_optional: bool = False) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} must contain an input grid"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if "output" not in pair:
        return [] if output_optional else [f"{label} must contain an output grid"]
    errors = _basic_grid_errors(pair["output"])
    if errors:
        return [f"{label} output: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not match the pinned key-door rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Finite-rival diagnostic for a generated five-demonstration lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query", output_optional=True))
    if reasons:
        return reasons

    modes = {_classify(pair["input"]) for pair in demos}
    missing = set(SCHEDULE_PROFILES) - modes
    if missing:
        reasons.append(f"demonstrations omit route profile(s): {sorted(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
