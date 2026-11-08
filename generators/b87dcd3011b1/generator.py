"""Generator for ``b87dcd3011b1`` — shortest paths through paired portals.

The canonical rule starts at color 2, reaches color 3, treats color 8 as walls,
and treats every exactly-paired color in {4,5,6} as an immediate teleport.  The
shortest route's background cells are painted color 7.

Lawful generated scenes contain a complete wall barrier between start and goal,
so at least one portal pair is semantically necessary rather than decorative.
Every declared axis is exact, live, and valid across every difficulty band.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b87dcd3011b1"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "0cc1f5e794c7"

SUMMARY = (
    "An 8..30 rectangular maze has one start(2), one goal(3), a complete gray "
    "wall barrier(8), one to three paired portals colored 4/5/6, and up to eight "
    "extra walls. Start and goal lie on opposite sides and no ordinary route "
    "crosses the barrier; at least one portal pair is required."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular 8..30 grid with exact integer colors from {0,2,3,4,5,6,8}",
    "exactly one color-2 start and one color-3 goal",
    "exactly one complete horizontal or vertical color-8 barrier",
    "start and goal are on opposite sides of the barrier",
    "one to three portal colors from 4/5/6 occur exactly twice each",
    "at least one portal pair crosses the barrier",
    "a route exists with all paired portals and no route exists without portals",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 8..30", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..30", "valid": "8..30"},
    "n_portals": {"type": "int", "default": "difficulty-aware 1..3", "valid": "1..3"},
    "barrier_orientation": {
        "type": "str",
        "default": "keyed vertical|horizontal",
        "valid": "vertical|horizontal",
    },
    "extra_walls": {"type": "int", "default": "difficulty-aware 0..8", "valid": "0..8"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
_PORTAL_COLORS = (4, 5, 6)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = ((9, 11), (9, 12), (11, 13))

Grid = list[list[int]]
Cell = tuple[int, int]


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    integer_bounds = {
        "grid_h": (8, 30),
        "grid_w": (8, 30),
        "n_portals": (1, 3),
        "extra_walls": (0, 8),
    }
    for name, (low, high) in integer_bounds.items():
        if name in overrides:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(f"{name} override must be an exact integer (not bool)")
            if not low <= value <= high:
                raise ValueError(f"{name} override must be in {low}..{high}")
    if "barrier_orientation" in overrides:
        value = overrides["barrier_orientation"]
        if type(value) is not str:
            raise TypeError("barrier_orientation override must be text")
        if value not in ("vertical", "horizontal"):
            raise ValueError("barrier_orientation must be 'vertical' or 'horizontal'")


def _difficulty_ranges(difficulty: Any) -> dict[str, tuple[int, int]]:
    if difficulty == "easy":
        return {"grid_h": (8, 11), "grid_w": (8, 13), "n_portals": (1, 1), "extra_walls": (0, 2)}
    if difficulty == "medium":
        return {"grid_h": (10, 18), "grid_w": (10, 20), "n_portals": (1, 2), "extra_walls": (1, 5)}
    if difficulty == "hard":
        return {"grid_h": (14, 30), "grid_w": (14, 30), "n_portals": (2, 3), "extra_walls": (3, 8)}
    return {"grid_h": (8, 20), "grid_w": (8, 22), "n_portals": (1, 3), "extra_walls": (0, 6)}


def _draw_integer_axis(ctx, name: str, global_bounds: tuple[int, int], default_bounds: tuple[int, int], overrides: dict[str, Any]) -> int:
    low, high = global_bounds if name in overrides else default_bounds
    return ctx.draw_choice(name, tuple(range(low, high + 1)))


def _portal_positions(grid: Grid) -> dict[int, tuple[Cell, Cell]]:
    found: dict[int, tuple[Cell, Cell]] = {}
    for color in _PORTAL_COLORS:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) == 2:
            found[color] = (cells[0], cells[1])
    return found


def _shortest_path(grid: Grid, *, portal_mode: str = "all_pairs") -> list[Cell] | None:
    """Return the canonical BFS state path; stepping on an active portal jumps."""
    if portal_mode not in {"all_pairs", "none"}:
        raise ValueError(f"unknown portal_mode {portal_mode!r}")
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    starts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    goals = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(starts) != 1 or len(goals) != 1:
        return None
    start, goal = starts[0], goals[0]
    pairs = _portal_positions(grid) if portal_mode == "all_pairs" else {}
    exits = {a: b for pair in pairs.values() for a, b in (pair, pair[::-1])}

    queue: deque[Cell] = deque([start])
    previous: dict[Cell, Cell | None] = {start: None}
    while queue and goal not in previous:
        row, col = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = row + dr, col + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            nxt = exits.get((nr, nc), (nr, nc))
            if nxt not in previous:
                previous[nxt] = (row, col)
                queue.append(nxt)
    if goal not in previous:
        return None
    path: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def _paint_path(grid: Grid, path: list[Cell] | None) -> Grid:
    """Return the rule output for a precomputed BFS path."""
    output = [row[:] for row in grid]
    if path is None:
        return output
    for row, col in path:
        if output[row][col] == 0:
            output[row][col] = 7
    return output


def solve(grid: Grid) -> Grid:
    """Apply the canonical all-paired-portals shortest-path rule."""
    return _paint_path(grid, _shortest_path(grid, portal_mode="all_pairs"))


def _solve_without_portals(grid: Grid) -> Grid:
    """Plausible wrong rule: search while treating portal cells as ordinary."""
    return _paint_path(grid, _shortest_path(grid, portal_mode="none"))


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the task-level manifold shared by authority and generated rows.

    This intentionally describes the semantic rule rather than the generator's
    narrower one-barrier construction: the third authority example contains a
    crossed pair of complete barriers, but it has the same paired-portal path
    semantics.
    """
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be nonempty lists"]
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (3 <= height <= 30 and 3 <= width <= 30):
        return [f"grid dimensions {height}x{width} outside 3..30"]
    allowed = {0, 2, 3, 4, 5, 6, 8}
    if any(type(cell) is not int or cell not in allowed for row in grid for cell in row):
        return ["cells must be exact integers from {0,2,3,4,5,6,8}"]
    if sum(row.count(2) for row in grid) != 1:
        return ["expected exactly one start color 2"]
    if sum(row.count(3) for row in grid) != 1:
        return ["expected exactly one goal color 3"]
    portal_counts = {
        color: sum(row.count(color) for row in grid) for color in _PORTAL_COLORS
    }
    if any(count not in (0, 2) for count in portal_counts.values()):
        return [f"portal colors must be absent or paired: {portal_counts}"]
    if not any(count == 2 for count in portal_counts.values()):
        return ["expected at least one paired portal color"]
    if _shortest_path(grid, portal_mode="all_pairs") is None:
        return ["goal must be reachable with paired portals"]
    if solve(grid) == _solve_without_portals(grid):
        return ["paired portals must change the shortest-path output"]
    return []


def _portal_required_witness(grid: Any) -> bool:
    return (
        strict_canonical_like(grid) == []
        and _shortest_path(grid, portal_mode="none") is None
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "no_portals": _solve_without_portals,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "portal_required": _portal_required_witness,
}
WITNESS_RIVALS = {
    "portal_required": ["no_portals"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require correct labels and a demonstration that refutes no teleporting."""
    reasons: list[str] = []
    if type(demos) is not list or not demos:
        return ["lesson must contain at least one demonstration"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if type(pair) is not dict or "input" not in pair:
            reasons.append(f"{role} is missing an input grid")
            continue
        semantic_errors = strict_canonical_like(pair["input"])
        if semantic_errors:
            reasons.append(f"{role} input is not canonical-like: {semantic_errors[0]}")
            continue
        expected = solve(pair["input"])
        if pair.get("output", expected) != expected:
            reasons.append(f"{role} output does not match the paired-portal BFS rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = True
        for demo in demos:
            try:
                if competitor(demo["input"]) != demo["output"]:
                    survives = False
                    break
            except Exception:
                survives = False
                break
        if not survives:
            continue
        try:
            rival_query = competitor(query["input"])
            expected_query = solve(query["input"])
        except Exception:
            continue
        if rival_query != expected_query:
            reasons.append(
                f"named rival {name!r} matches every demo but changes the query answer"
            )
    return reasons


def _barrier(grid: Grid) -> tuple[str, int] | None:
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(rows) == 1 and not cols:
        return "horizontal", rows[0]
    if len(cols) == 1 and not rows:
        return "vertical", cols[0]
    return None


def _semantic_separators(grid: Grid) -> list[tuple[str, int]]:
    """Return wall/portal separator lines allowed by the authority examples."""
    h, w = len(grid), len(grid[0])
    line_values = {4, 5, 6, 8}
    separators: list[tuple[str, int]] = []
    for row in range(h):
        values = grid[row]
        if 8 in values and all(value in line_values for value in values):
            separators.append(("horizontal", row))
    for col in range(w):
        values = [grid[row][col] for row in range(h)]
        if 8 in values and all(value in line_values for value in values):
            separators.append(("vertical", col))
    return separators


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    """Recover every declared axis from a valid generated grid."""
    h = len(grid)
    w = len(grid[0]) if h and isinstance(grid[0], list) else 0
    result: dict[str, int | str] = {"grid_h": h, "grid_w": w}
    if not h or not w or any(not isinstance(row, list) or len(row) != w for row in grid):
        return result
    result["n_portals"] = sum(sum(row.count(color) for row in grid) == 2 for color in _PORTAL_COLORS)
    barrier = _barrier(grid)
    if barrier is not None:
        orientation, _ = barrier
        result["barrier_orientation"] = orientation
        barrier_cells = h if orientation == "vertical" else w
        result["extra_walls"] = sum(row.count(8) for row in grid) - barrier_cells
    return result


def _side_cells(height: int, width: int, orientation: str, barrier_index: int) -> tuple[list[Cell], list[Cell]]:
    if orientation == "vertical":
        low = [(r, c) for r in range(height) for c in range(0, barrier_index)]
        high = [(r, c) for r in range(height) for c in range(barrier_index + 1, width)]
    else:
        low = [(r, c) for r in range(0, barrier_index) for c in range(width)]
        high = [(r, c) for r in range(barrier_index + 1, height) for c in range(width)]
    return low, high


def _construct(height: int, width: int, n_portals: int, orientation: str, extra_walls: int, rng) -> Grid:
    for _attempt in range(128):
        grid = full_grid(height, width, 0)
        if orientation == "vertical":
            barrier_index = rng.choice(list(range(3, width - 3)))
            for row in range(height):
                grid[row][barrier_index] = 8
        else:
            barrier_index = rng.choice(list(range(3, height - 3)))
            for col in range(width):
                grid[barrier_index][col] = 8

        low, high = _side_cells(height, width, orientation, barrier_index)
        # Avoid pinning semantic roles to one side or one color.
        if rng.randrange(2):
            start_pool, goal_pool = low, high
        else:
            start_pool, goal_pool = high, low
        start = rng.choice(start_pool)
        goal = rng.choice(goal_pool)
        used = {start, goal}
        grid[start[0]][start[1]] = 2
        grid[goal[0]][goal[1]] = 3

        portal_colors = rng.sample(list(_PORTAL_COLORS), n_portals)
        valid = True
        for color in portal_colors:
            left_choices = [p for p in low if p not in used]
            right_choices = [p for p in high if p not in used]
            if not left_choices or not right_choices:
                valid = False
                break
            first = rng.choice(left_choices)
            second = rng.choice(right_choices)
            used.update((first, second))
            grid[first[0]][first[1]] = color
            grid[second[0]][second[1]] = color
        if not valid:
            continue

        free = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == 0
        ]
        if len(free) < extra_walls:
            continue
        for row, col in rng.sample(free, extra_walls):
            grid[row][col] = 8

        if not self_check(grid):
            return grid
    raise ValueError("could not realize a portal-required barrier maze")


def self_check(grid: Grid, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the shared authority/generated portal-maze grammar."""
    del difficulty, meta
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    starts = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    goals = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    start, goal = starts[0], goals[0]
    separates = False
    for orientation, index in _semantic_separators(grid):
        if orientation == "vertical":
            separates = (start[1] < index) != (goal[1] < index)
        else:
            separates = (start[0] < index) != (goal[0] < index)
        if separates:
            break
    if not separates:
        return [
            "expected a complete wall/portal separator with start and goal on opposite sides"
        ]
    return []


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _difficulty_ranges(difficulty)
    anchor_axes = {"grid_h", "grid_w", "n_portals"}
    canonical_anchor = (
        not (anchor_axes & set(overrides))
        and sample_index % EXAMPLES_NEEDED == 0
    )
    if canonical_anchor:
        profile_height, profile_width = ctx.draw_rng("canonical-profile").choice(
            _CANONICAL_PROFILES
        )
        height = ctx.draw_choice("grid_h", (profile_height,))
        width = ctx.draw_choice("grid_w", (profile_width,))
        portals = ctx.draw_choice("n_portals", (1,))
    else:
        height = _draw_integer_axis(ctx, "grid_h", (8, 30), defaults["grid_h"], overrides)
        width = _draw_integer_axis(ctx, "grid_w", (8, 30), defaults["grid_w"], overrides)
        portals = _draw_integer_axis(ctx, "n_portals", (1, 3), defaults["n_portals"], overrides)
    extra = _draw_integer_axis(ctx, "extra_walls", (0, 8), defaults["extra_walls"], overrides)
    orientation = ctx.draw_choice("barrier_orientation", ("vertical", "horizontal"))
    return _construct(height, width, portals, orientation, extra, ctx.draw_rng("layout"))
