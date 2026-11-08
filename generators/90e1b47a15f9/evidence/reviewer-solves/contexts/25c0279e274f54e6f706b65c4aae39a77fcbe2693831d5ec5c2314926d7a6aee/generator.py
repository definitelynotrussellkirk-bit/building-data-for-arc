"""Generator for ARC task 90e1b47a15f9 — shortest path with two keys.

The pinned Racket authority searches ``(row, column, has_key_4, has_key_5)``.
Color 4 unlocks door 6 and color 5 unlocks door 7; walls are color 8.  The
output is an all-zero grid with the first lawful BFS path painted color 9, or
an all-zero grid when no lawful route exists.

The original sampler scattered markers in an open room, so keys and doors were
usually irrelevant.  This reviewed sampler cuts sparse corridor subtrees from
randomized perfect mazes and schedules three semantic profiles:

``two_stage_detour``
    Both keys lie on separate side branches before their matching main-route
    doors.  The lawful route must collect key 4, cross door 6, collect key 5,
    and cross door 7.  Opening every door or allowing either key to open both
    skips a required detour and changes the output.

``unreachable``
    Key 4 is immediately behind door 6 while key 5 is reachable beforehand.
    The canonical answer is all zero, but erasing the locks or allowing either
    key to open both doors reaches the goal.

``bypass``
    Both key/door pairs occupy dead-end side branches.  The true shortest path
    ignores them, refuting the plausible rule that both keys must be collected.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, NamedTuple, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "90e1b47a15f9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e59742fe2660"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "In a color-8 maze, trace the shortest lawful path from start 2 to goal 3 "
    "in (position, key-4-held, key-5-held) state space. Key 4 unlocks door 6 "
    "and key 5 unlocks door 7. Paint every path coordinate 9 on an otherwise "
    "zero grid; return all zeros when the goal is unreachable."
)

INVARIANTS = [
    "the full outer border and unused cells are color-8 walls",
    "there is exactly one start 2, goal 3, key 4, key 5, door 6, and door 7",
    "all non-wall cells form one sparse orthogonal corridor tree",
    "reachable shortest paths use both key/door pairs or bypass both pairs",
    "ordinary lessons cover required, unreachable, and bypass state profiles",
]

SCHEDULE_PROFILES = ("two_stage_detour", "unreachable", "bypass")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical dimensions four times in five; otherwise difficulty-scheduled",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical dimensions four times in five; otherwise difficulty-scheduled",
        "valid": "12..18",
    },
    "route_profile": {
        "type": "str",
        "default": "three-slot semantic schedule",
        "valid": "two_stage_detour|unreachable|bypass",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
SOLID_OUTPUT_JUSTIFICATION = (
    "The pinned rule returns an all-zero output exactly when no lawful "
    "key-state path reaches the goal; self_check admits that branch only "
    "when erasing the locks restores a nonempty route."
)

_ALLOWED = frozenset({0, 2, 3, 4, 5, 6, 7, 8})
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SHAPES = frozenset({(7, 12), (8, 13), (9, 14), (8, 14)})

Point = tuple[int, int]
Grid = Sequence[Sequence[int]]


class _SearchResult(NamedTuple):
    reachable: bool
    states: tuple[tuple[int, int, bool, bool], ...]

    @property
    def coordinates(self) -> tuple[Point, ...]:
        return tuple((r, c) for r, c, _key_a, _key_b in self.states)


class _Placement(NamedTuple):
    score: int
    start: Point
    goal: Point
    key_a: Point
    key_b: Point
    door_a: Point
    door_b: Point
    paths: tuple[tuple[Point, ...], ...]


def _positions(grid: Grid, color: int) -> list[Point]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _stateful_search(
    grid: Grid,
    *,
    door_mode: str = "locked",
    require_both_keys_at_goal: bool = False,
) -> _SearchResult:
    """Mirror the canonical BFS, including U/D/L/R order and key state.

    ``door_mode`` is ``locked``, ``open``, ``wall``, or ``one_key``.  The
    authority places a same-cell key-updated state at the front of the queue;
    retaining that harmless state here also preserves exact canonical tie
    behavior rather than relying on a merely equivalent reachability search.
    """
    if door_mode not in {"locked", "open", "wall", "one_key"}:
        raise ValueError(f"unknown door mode: {door_mode!r}")
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return _SearchResult(False, ())

    start = (starts[0][0], starts[0][1], False, False)
    goal = goals[0]
    queue = deque([start])
    parent: dict[
        tuple[int, int, bool, bool], tuple[int, int, bool, bool] | None
    ] = {start: None}
    end: tuple[int, int, bool, bool] | None = None
    h, w = len(grid), len(grid[0])

    while queue:
        state = queue.popleft()
        r, c, key_a, key_b = state
        if (r, c) == goal and (
            not require_both_keys_at_goal or (key_a and key_b)
        ):
            end = state
            break

        next_key_a = key_a or grid[r][c] == 4
        next_key_b = key_b or grid[r][c] == 5
        updated = (r, c, next_key_a, next_key_b)
        if updated != state and updated not in parent:
            parent[updated] = state
            queue.appendleft(updated)

        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 8:
                continue
            if value in (6, 7):
                if door_mode == "wall":
                    continue
                if door_mode == "locked":
                    if value == 6 and not next_key_a:
                        continue
                    if value == 7 and not next_key_b:
                        continue
                elif door_mode == "one_key" and not (next_key_a or next_key_b):
                    continue
            nxt = (nr, nc, next_key_a, next_key_b)
            if nxt in parent:
                continue
            parent[nxt] = state
            queue.append(nxt)

    if end is None:
        return _SearchResult(False, ())
    reverse_states: list[tuple[int, int, bool, bool]] = []
    current: tuple[int, int, bool, bool] | None = end
    while current is not None:
        reverse_states.append(current)
        current = parent[current]
    return _SearchResult(True, tuple(reversed(reverse_states)))


def _paint_path(grid: Grid, result: _SearchResult) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    if result.reachable:
        for r, c in result.coordinates:
            out[r][c] = 9
    return out


def rule_mirror(grid: Grid) -> list[list[int]]:
    """Python test mirror; the pinned Racket rule remains output authority."""
    structural = _basic_grid_errors(grid)
    if structural:
        raise ValueError("invalid grid for rule_mirror: " + "; ".join(structural))
    return _paint_path(grid, _stateful_search(grid))


def _erase_keys_and_doors_rival(grid: Grid) -> list[list[int]]:
    stripped = [
        [0 if value in (4, 5, 6, 7) else value for value in row]
        for row in grid
    ]
    return _paint_path(stripped, _stateful_search(stripped, door_mode="open"))


def _doors_are_walls_rival(grid: Grid) -> list[list[int]]:
    return _paint_path(grid, _stateful_search(grid, door_mode="wall"))


def _one_key_opens_both_rival(grid: Grid) -> list[list[int]]:
    return _paint_path(grid, _stateful_search(grid, door_mode="one_key"))


def _always_collect_both_rival(grid: Grid) -> list[list[int]]:
    return _paint_path(
        grid,
        _stateful_search(grid, require_both_keys_at_goal=True),
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], list[list[int]]]] = {
    "erase_keys_and_doors": _erase_keys_and_doors_rival,
    "doors_are_walls": _doors_are_walls_rival,
    "one_key_opens_both": _one_key_opens_both_rival,
    "always_collect_both": _always_collect_both_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "erase_keys_and_doors": _erase_keys_and_doors_rival,
    "one_key_opens_both": _one_key_opens_both_rival,
    "always_collect_both": _always_collect_both_rival,
}


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
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for label, lo, hi in (("grid_h", 7, 13), ("grid_w", 12, 18)):
        value = overrides.get(label)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{label} must be in {lo}..{hi}")

    profile = overrides.get("route_profile")
    if profile is not None and (
        not isinstance(profile, str) or profile not in SCHEDULE_PROFILES
    ):
        raise ValueError(
            "route_profile must be one of " + "|".join(SCHEDULE_PROFILES)
        )


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """A period-three schedule leaves every profile after any 6-pair rotation."""
    del seed
    _difficulty_band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: Sequence[Any], scheduled: Any):
    """Expose a full exact-axis domain while deterministically scheduling it."""
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
    canonical = ((7, 12), (8, 13), (9, 14), (8, 14))
    if int(sample_index) % 5 != 4:
        return canonical[int(sample_index) % len(canonical)]
    extras = {
        "easy": ((7, 15), (8, 16), (9, 15)),
        "medium": ((9, 16), (10, 17), (11, 16)),
        "hard": ((11, 18), (12, 17), (13, 18)),
    }
    return extras[band][(int(sample_index) // 5) % len(extras[band])]


def _lattice_coordinates(length: int, rng) -> list[int]:
    offset = 1 if length % 2 else rng.choice((1, 2))
    return list(range(offset, length - 1, 2))


def _node_graph(rows: Sequence[int], cols: Sequence[int], rng):
    """Build a randomized DFS perfect maze over lattice nodes."""
    nodes = [(r, c) for r in rows for c in cols]
    row_index = {r: index for index, r in enumerate(rows)}
    col_index = {c: index for index, c in enumerate(cols)}
    by_index = {
        (ri, ci): (r, c)
        for ri, r in enumerate(rows)
        for ci, c in enumerate(cols)
    }
    start = rng.choice(nodes)
    stack = [start]
    seen = {start}
    adjacency = {node: set() for node in nodes}

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
        stack.append(nxt)
    return adjacency


def _tree_path(adjacency: dict[Point, set[Point]], start: Point, goal: Point) -> list[Point]:
    queue = deque([start])
    parent: dict[Point, Point | None] = {start: None}
    while queue:
        node = queue.popleft()
        if node == goal:
            break
        for nxt in sorted(adjacency[node]):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    if goal not in parent:
        return []
    reverse: list[Point] = []
    current: Point | None = goal
    while current is not None:
        reverse.append(current)
        current = parent[current]
    return list(reversed(reverse))


def _component_from(
    adjacency: dict[Point, set[Point]],
    first: Point,
    blocked: set[Point],
) -> set[Point]:
    queue = deque([first])
    seen = {first}
    while queue:
        node = queue.popleft()
        for nxt in sorted(adjacency[node]):
            if nxt in blocked or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return seen


def _endpoint_pool(adjacency: dict[Point, set[Point]]) -> list[Point]:
    leaves = sorted(node for node, neighbors in adjacency.items() if len(neighbors) == 1)
    return leaves if len(leaves) >= 2 else sorted(adjacency)


def _midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)


def _path_cells(path: Sequence[Point]) -> set[Point]:
    cells = set(path)
    for a, b in zip(path, path[1:]):
        cells.add(_midpoint(a, b))
    return cells


def _branch_paths(
    adjacency: dict[Point, set[Point]], main: Sequence[Point]
) -> list[tuple[int, tuple[Point, ...]]]:
    main_set = set(main)
    options: list[tuple[int, tuple[Point, ...]]] = []
    for index in range(1, len(main) - 1):
        junction = main[index]
        for first in sorted(adjacency[junction] - main_set):
            component = _component_from(adjacency, first, main_set)
            farthest = max(
                sorted(component),
                key=lambda node: (len(_tree_path(adjacency, junction, node)), node),
            )
            path = tuple(_tree_path(adjacency, junction, farthest))
            if len(path) >= 2:
                options.append((index, path))
    return options


def _two_stage_candidates(adjacency: dict[Point, set[Point]]) -> list[_Placement]:
    candidates: list[_Placement] = []
    endpoints = _endpoint_pool(adjacency)
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if len(main) < 5:
                continue
            branches = _branch_paths(adjacency, main)
            for a_index, branch_a in branches:
                for b_index, branch_b in branches:
                    if a_index >= b_index:
                        continue
                    if set(branch_a[1:]) & set(branch_b[1:]):
                        continue
                    door_a = _midpoint(main[a_index], main[a_index + 1])
                    door_b = _midpoint(main[b_index], main[b_index + 1])
                    paths = (tuple(main), branch_a, branch_b)
                    score = len(set().union(*(_path_cells(path) for path in paths)))
                    candidates.append(
                        _Placement(
                            score,
                            start,
                            goal,
                            branch_a[-1],
                            branch_b[-1],
                            door_a,
                            door_b,
                            paths,
                        )
                    )
    return candidates


def _unreachable_candidates(adjacency: dict[Point, set[Point]]) -> list[_Placement]:
    candidates: list[_Placement] = []
    endpoints = _endpoint_pool(adjacency)
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if len(main) < 7:
                continue
            for door_a_index in range(2, len(main) - 3):
                for door_b_index in range(door_a_index + 2, len(main) - 1):
                    key_b = main[door_a_index - 1]
                    key_a = main[door_a_index + 1]
                    door_a = _midpoint(
                        main[door_a_index], main[door_a_index + 1]
                    )
                    door_b = _midpoint(
                        main[door_b_index], main[door_b_index + 1]
                    )
                    paths = (tuple(main),)
                    score = len(_path_cells(main))
                    candidates.append(
                        _Placement(
                            score,
                            start,
                            goal,
                            key_a,
                            key_b,
                            door_a,
                            door_b,
                            paths,
                        )
                    )
    return candidates


def _bypass_candidates(adjacency: dict[Point, set[Point]]) -> list[_Placement]:
    candidates: list[_Placement] = []
    endpoints = _endpoint_pool(adjacency)
    for start in endpoints:
        for goal in endpoints:
            if start == goal:
                continue
            main = _tree_path(adjacency, start, goal)
            if not 3 <= len(main) <= 9:
                continue
            branches = [item for item in _branch_paths(adjacency, main) if len(item[1]) >= 3]

            # Two independent dead-end branches, one key/door pair per branch.
            for a_pos, (_a_index, full_a) in enumerate(branches):
                branch_a = full_a[:3]
                for _b_index, full_b in branches[a_pos + 1 :]:
                    branch_b = full_b[:3]
                    if set(branch_a[1:]) & set(branch_b[1:]):
                        continue
                    paths = (tuple(main), tuple(branch_a), tuple(branch_b))
                    score = len(set().union(*(_path_cells(path) for path in paths)))
                    candidates.append(
                        _Placement(
                            score,
                            start,
                            goal,
                            branch_a[1],
                            branch_b[1],
                            _midpoint(branch_a[1], branch_a[2]),
                            _midpoint(branch_b[1], branch_b[2]),
                            paths,
                        )
                    )

            # One longer dead end can teach both pairs in sequence.
            for _index, full_branch in branches:
                if len(full_branch) < 5:
                    continue
                branch = full_branch[:5]
                paths = (tuple(main), tuple(branch))
                score = len(set().union(*(_path_cells(path) for path in paths)))
                candidates.append(
                    _Placement(
                        score,
                        start,
                        goal,
                        branch[1],
                        branch[3],
                        _midpoint(branch[1], branch[2]),
                        _midpoint(branch[3], branch[4]),
                        paths,
                    )
                )
    return candidates


def _pick_by_difficulty(candidates: Sequence[_Placement], difficulty: Any, rng) -> _Placement:
    ordered = sorted(candidates, key=lambda item: item.score)
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


def _render_placement(h: int, w: int, placement: _Placement, rng) -> list[list[int]]:
    grid = full_grid(h, w, 8)
    carved: set[Point] = set()
    for path in placement.paths:
        carved.update(_path_cells(path))
    for r, c in carved:
        grid[r][c] = 0

    for point, color in (
        (placement.start, 2),
        (placement.goal, 3),
        (placement.key_a, 4),
        (placement.key_b, 5),
        (placement.door_a, 6),
        (placement.door_b, 7),
    ):
        grid[point[0]][point[1]] = color

    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = list(reversed(grid))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, sparse, semantically classified maze."""
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
    w = int(_scheduled_choice(ctx, "grid_w", tuple(range(12, 19)), scheduled_w))
    profile = str(
        _scheduled_choice(
            ctx,
            "route_profile",
            SCHEDULE_PROFILES,
            schedule_profile(seed, sample_index, difficulty),
        )
    )
    candidate_fn = {
        "two_stage_detour": _two_stage_candidates,
        "unreachable": _unreachable_candidates,
        "bypass": _bypass_candidates,
    }[profile]

    for attempt in range(320):
        rng = ctx.draw_rng(f"layout:{band}:{profile}:{attempt}")
        rows = _lattice_coordinates(h, rng)
        cols = _lattice_coordinates(w, rng)
        if len(rows) < 3 or len(cols) < 5:
            continue
        adjacency = _node_graph(rows, cols, rng)
        candidates = candidate_fn(adjacency)
        if not candidates:
            continue
        placement = _pick_by_difficulty(candidates, difficulty, rng)
        grid = _render_placement(h, w, placement, rng)

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            continue
        if _classify(grid) != profile:
            continue
        if observe_overrides(grid) != {
            "grid_h": h,
            "grid_w": w,
            "route_profile": profile,
        }:
            continue

        truth = rule_mirror(grid)
        if profile == "two_stage_detour":
            if truth == _erase_keys_and_doors_rival(grid):
                continue
            if truth == _doors_are_walls_rival(grid):
                continue
            if truth == _one_key_opens_both_rival(grid):
                continue
        elif profile == "unreachable":
            if any(value != 0 for row in truth for value in row):
                continue
            if truth == _erase_keys_and_doors_rival(grid):
                continue
            if truth == _one_key_opens_both_rival(grid):
                continue
        else:
            if truth == _always_collect_both_rival(grid):
                continue
        return [row[:] for row in grid]

    raise RuntimeError(
        f"could not construct a lawful {profile} sparse maze at {h}x{w}"
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


def _nonwall_connected(grid: Grid) -> bool:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 8
    }
    if not cells:
        return False
    start = min(cells)
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _classify(grid: Grid) -> str:
    result = _stateful_search(grid)
    if not result.reachable:
        return "unreachable"
    values = {grid[r][c] for r, c in result.coordinates} & {4, 5, 6, 7}
    if values == {4, 5, 6, 7}:
        return "two_stage_detour"
    if not values:
        return "bypass"
    return "partial"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the reviewed manifold while accepting every canonical input."""
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    try:
        _difficulty_band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 13 and 12 <= w <= 18):
        errors.append(f"shape {h}x{w} outside 7..13 by 12..18")

    values = [value for row in grid for value in row]
    illegal = sorted(set(values) - _ALLOWED)
    if illegal:
        errors.append(f"illegal input colors: {illegal}")
    if set(values) != _ALLOWED:
        errors.append(f"input palette must be exactly {sorted(_ALLOWED)}")

    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)):
        errors.append("top and bottom borders must be all color 8")
    if any(grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)):
        errors.append("left and right borders must be all color 8")

    for color, name in (
        (2, "start"),
        (3, "goal"),
        (4, "key A"),
        (5, "key B"),
        (6, "door A"),
        (7, "door B"),
    ):
        count = values.count(color)
        if count != 1:
            errors.append(f"expected exactly one {name} color-{color}, found {count}")
    if values.count(8) <= max(values.count(color) for color in _ALLOWED - {8}):
        errors.append("wall color 8 must be modal")
    if errors:
        return errors

    if not _nonwall_connected(grid):
        errors.append("all non-wall cells must form one connected corridor graph")

    profile = _classify(grid)
    if profile not in SCHEDULE_PROFILES:
        errors.append(f"unsupported partial key/door route profile: {profile}")
    result = _stateful_search(grid)
    if result.reachable and len(set(result.coordinates)) < 4:
        errors.append("reachable route is too short to demonstrate path painting")
    if profile == "unreachable":
        open_answer = _erase_keys_and_doors_rival(grid)
        if not any(value == 9 for row in open_answer for value in row):
            errors.append("unreachable scene remains unreachable when locks are erased")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    if requested and not errors:
        observed = {
            "grid_h": h,
            "grid_w": w,
            "route_profile": profile,
        }
        for name, expected in requested.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    profile = _classify(grid)
    if profile not in SCHEDULE_PROFILES:
        raise ValueError(f"grid has unsupported route profile {profile!r}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "route_profile": profile,
    }


def strict_canonical_like(grid) -> list[str]:
    errors = list(self_check(grid))
    if not errors and (len(grid), len(grid[0])) not in _CANONICAL_SHAPES:
        errors.append(
            f"shape {len(grid)}x{len(grid[0])} is outside canonical dimension support"
        )
    return errors


def _witness_profile(profile: str, rivals: Sequence[str]):
    def witness(grid: Grid) -> bool:
        try:
            if self_check(grid) or _classify(grid) != profile:
                return False
            truth = rule_mirror(grid)
            return all(SEMANTIC_RIVALS[name](grid) != truth for name in rivals)
        except Exception:
            return False

    return witness


SEMANTIC_WITNESSES = {
    "two_stage_requires_two_keys": _witness_profile(
        "two_stage_detour",
        ("erase_keys_and_doors", "doors_are_walls", "one_key_opens_both"),
    ),
    "unreachable_key_behind_door": _witness_profile(
        "unreachable",
        ("erase_keys_and_doors", "one_key_opens_both"),
    ),
    "shortest_path_bypasses_keys": _witness_profile(
        "bypass",
        ("always_collect_both",),
    ),
}
WITNESS_RIVALS = {
    "two_stage_requires_two_keys": [
        "erase_keys_and_doors",
        "doors_are_walls",
        "one_key_opens_both",
    ],
    "unreachable_key_behind_door": [
        "erase_keys_and_doors",
        "one_key_opens_both",
    ],
    "shortest_path_bypasses_keys": ["always_collect_both"],
}


def _pair_errors(pair: Any, label: str, *, output_optional: bool = False) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} must contain an input grid"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if "output" not in pair:
        return [] if output_optional else [f"{label} must contain an output grid"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not match the pinned two-key rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Check that a five-demo lesson determines the query against named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query", output_optional=True))
    if reasons:
        return reasons

    profiles = {_classify(pair["input"]) for pair in demos}
    missing = set(SCHEDULE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations omit route profile(s): {sorted(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
