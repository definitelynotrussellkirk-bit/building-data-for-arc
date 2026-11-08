"""Generate dense portal mazes that teach ordered checkpoint state.

Selected rule
-------------
Find the shortest path from color 2 to color 3 in the state space
``(row, column, checkpoint_seen)``.  The path is valid only after visiting the
single color-5 checkpoint.  A step onto either member of a two-cell color-6 or
color-7 portal immediately arrives at its partner.  Preserve the input and
paint only traversed color-0 cells with color 4.

The canonical demonstrations also fit a strong wrong rule: draw a shortest
2→3 path first, then a shortest 3→5 path.  Ordinary samples are therefore
constructed as measured counterexamples to that rival, not merely as valid
open grids containing the right colors.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

TASK_ID = "bcac0c8a0478"
GENERATOR_ID = TASK_ID
VERSION = "2.0.0"
RULE_HASH = "076228df68df"

SUMMARY = (
    "Dense color-8 mazes with start 2, goal 3, checkpoint 5, and one or two "
    "required portal pairs (6/7).  The selected BFS tracks whether checkpoint "
    "5 has been visited; generated lessons refute goal-first, direct-path, and "
    "ignore-portals rivals."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

INVARIANTS = [
    "background is color 0 and the complete outer border is color 8",
    "exactly one interior start 2, goal 3, and checkpoint 5",
    "portal colors 6 and 7 occur zero or exactly two times",
    "the checkpoint-constrained state-space route exists",
    "ordinary samples are counterexamples to goal-first and direct-path rivals",
    "every portal color in an ordinary sample is used by the selected route",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..16",
    },
    "use_portal_6": {
        "type": "int",
        "default": "scheduled 0 or 1",
        "valid": "0..1",
    },
    "use_portal_7": {
        "type": "int",
        "default": "scheduled 0 or 1",
        "valid": "0..1",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Exact canonical input profiles: (height, width, distinct input colors).
CANONICAL_PROFILES = {(7, 9, 6), (7, 10, 6), (8, 11, 7)}
# Every default profile is exact-canonical in coarse shape/palette, while its
# maze and marker placements are fresh.  The three profiles also exercise each
# portal mode needed by the rule.
_DEFAULT_PROFILES = (
    (7, 9, 1, 0),
    (7, 10, 0, 1),
    (8, 11, 1, 1),
)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_INPUT_COLORS = {0, 2, 3, 5, 6, 7, 8}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    bounds = {
        "grid_h": (7, 13),
        "grid_w": (9, 16),
        "use_portal_6": (0, 1),
        "use_portal_7": (0, 1),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"override {name!r} must be an integer, got {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _draw_axes(ctx, overrides: dict[str, Any]) -> tuple[int, int, int, int]:
    profile_rng = ctx.draw_rng("canonical_profile")
    base_h, base_w, base_p6, base_p7 = _DEFAULT_PROFILES[
        profile_rng.randrange(len(_DEFAULT_PROFILES))
    ]
    broad_dimensions = ctx.sample_index % 5 == 0
    h = (
        ctx.draw_int("grid_h", 7, 13)
        if "grid_h" in overrides or broad_dimensions
        else ctx.draw_int("grid_h", base_h, base_h)
    )
    w = (
        ctx.draw_int("grid_w", 9, 16)
        if "grid_w" in overrides or broad_dimensions
        else ctx.draw_int("grid_w", base_w, base_w)
    )
    p6 = (
        ctx.draw_int("use_portal_6", 0, 1)
        if "use_portal_6" in overrides
        else ctx.draw_int("use_portal_6", base_p6, base_p6)
    )
    p7 = (
        ctx.draw_int("use_portal_7", 0, 1)
        if "use_portal_7" in overrides
        else ctx.draw_int("use_portal_7", base_p7, base_p7)
    )
    return h, w, p6, p7


def _positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _portal_map(grid: list[list[int]], *, enabled: bool = True) -> dict[tuple[int, int], tuple[int, int]]:
    if not enabled:
        return {}
    result: dict[tuple[int, int], tuple[int, int]] = {}
    for color in (6, 7):
        hits = _positions(grid, color)
        if len(hits) == 2:
            result[hits[0]] = hits[1]
            result[hits[1]] = hits[0]
    return result


def _state_path(grid: list[list[int]], *, portals: bool = True) -> list[tuple[int, int]] | None:
    """Mirror the selected Racket BFS, including its neighbor order."""
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    checkpoints = _positions(grid, 5)
    if not (len(starts) == len(goals) == len(checkpoints) == 1):
        return None
    start, goal, checkpoint = starts[0], goals[0], checkpoints[0]
    portal_map = _portal_map(grid, enabled=portals)
    initial = (start[0], start[1], 0)
    queue = deque([initial])
    previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {initial: None}
    end: tuple[int, int, int] | None = None
    h, w = len(grid), len(grid[0])

    while queue and end is None:
        current = queue.popleft()
        r, c, hit = current
        if (r, c) == goal and hit == 1:
            end = current
            break
        for dr, dc in _CARDINALS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            hit_before_portal = int(hit == 1 or (nr, nc) == checkpoint)
            dest = portal_map.get((nr, nc), (nr, nc))
            hit_after_portal = int(hit_before_portal == 1 or dest == checkpoint)
            state = (dest[0], dest[1], hit_after_portal)
            if state not in previous:
                previous[state] = current
                queue.append(state)

    if end is None:
        return None
    reversed_path: list[tuple[int, int]] = []
    current: tuple[int, int, int] | None = end
    while current is not None:
        reversed_path.append((current[0], current[1]))
        current = previous[current]
    return list(reversed(reversed_path))


def _position_path(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    *,
    portals: bool = True,
) -> list[tuple[int, int]] | None:
    """Racket-order position-only BFS used by executable rival rules."""
    h, w = len(grid), len(grid[0])
    portal_map = _portal_map(grid, enabled=portals)
    queue = deque([start])
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    end: tuple[int, int] | None = None
    while queue and end is None:
        current = queue.popleft()
        if current == goal:
            end = current
            break
        r, c = current
        for dr, dc in _CARDINALS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 8:
                continue
            dest = portal_map.get((nr, nc), (nr, nc))
            if dest not in previous:
                previous[dest] = current
                queue.append(dest)
    if end is None:
        return None
    reversed_path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = end
    while current is not None:
        reversed_path.append(current)
        current = previous[current]
    return list(reversed(reversed_path))


def _paint(grid: list[list[int]], path: list[tuple[int, int]] | None) -> list[list[int]]:
    out = deepcopy(grid)
    if path is None:
        return out
    for r, c in path:
        if out[r][c] == 0:
            out[r][c] = 4
    return out


def _apply_intended(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, _state_path(grid, portals=True))


def _direct_to_goal(grid: list[list[int]]) -> list[list[int]]:
    starts, goals = _positions(grid, 2), _positions(grid, 3)
    if len(starts) != 1 or len(goals) != 1:
        return deepcopy(grid)
    return _paint(grid, _position_path(grid, starts[0], goals[0], portals=True))


def _goal_first_then_checkpoint(grid: list[list[int]]) -> list[list[int]]:
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    checkpoints = _positions(grid, 5)
    if not (len(starts) == len(goals) == len(checkpoints) == 1):
        return deepcopy(grid)
    first = _position_path(grid, starts[0], goals[0], portals=True)
    second = _position_path(grid, goals[0], checkpoints[0], portals=True)
    if first is None or second is None:
        return deepcopy(grid)
    return _paint(_paint(grid, first), second)


def _ignore_portals(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, _state_path(grid, portals=False))


def _used_portal_colors(grid: list[list[int]]) -> set[int]:
    path = _state_path(grid, portals=True) or []
    return {grid[r][c] for r, c in path if grid[r][c] in (6, 7)}


def _perfect_maze(h: int, w: int, rng, *, extra_loops: int) -> list[list[int]]:
    """Carve a randomized spanning-tree maze, then add a few cycle edges."""
    grid = full_grid(h, w, 8)
    nodes = [(r, c) for r in range(1, h - 1, 2) for c in range(1, w - 1, 2)]
    if not nodes:
        raise ValueError(f"grid {h}x{w} has no interior maze nodes")
    start = nodes[rng.randrange(len(nodes))]
    stack = [start]
    visited = {start}
    grid[start[0]][start[1]] = 0
    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in _CARDINALS:
            nxt = (r + 2 * dr, c + 2 * dc)
            if nxt in nodes and nxt not in visited:
                neighbors.append((nxt, (r + dr, c + dc)))
        if not neighbors:
            stack.pop()
            continue
        nxt, between = neighbors[rng.randrange(len(neighbors))]
        grid[between[0]][between[1]] = 0
        grid[nxt[0]][nxt[1]] = 0
        visited.add(nxt)
        stack.append(nxt)

    cycle_walls = []
    for r, c in nodes:
        for dr, dc in ((1, 0), (0, 1)):
            other = (r + 2 * dr, c + 2 * dc)
            between = (r + dr, c + dc)
            if other in visited and grid[between[0]][between[1]] == 8:
                cycle_walls.append(between)
    rng.shuffle(cycle_walls)
    for r, c in cycle_walls[: min(extra_loops, len(cycle_walls))]:
        grid[r][c] = 0
    return grid


def _candidate_from_open_cells(
    base: list[list[int]],
    rng,
    *,
    use_portal_6: int,
    use_portal_7: int,
) -> list[list[int]] | None:
    open_cells = [
        (r, c)
        for r in range(1, len(base) - 1)
        for c in range(1, len(base[0]) - 1)
        if base[r][c] == 0
    ]
    needed = 3 + 2 * use_portal_6 + 2 * use_portal_7
    if len(open_cells) < needed:
        return None
    chosen = rng.sample(open_cells, needed)
    grid = deepcopy(base)
    cursor = 0
    for color in (2, 5, 3):
        r, c = chosen[cursor]
        cursor += 1
        grid[r][c] = color
    for enabled, color in ((use_portal_6, 6), (use_portal_7, 7)):
        if enabled:
            for _ in range(2):
                r, c = chosen[cursor]
                cursor += 1
                grid[r][c] = color
    return grid


def _teaches_rule(grid: list[list[int]], requested_portals: set[int]) -> bool:
    path = _state_path(grid, portals=True)
    if path is None:
        return False
    intended = _paint(grid, path)
    if _used_portal_colors(grid) != requested_portals:
        return False
    if intended == _goal_first_then_checkpoint(grid):
        return False
    if intended == _direct_to_goal(grid):
        return False
    if requested_portals and intended == _ignore_portals(grid):
        return False
    if sum(value == 4 for row in intended for value in row) < 3:
        return False
    if not any(value == 0 for row in grid for value in row):
        return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h, w, use_portal_6, use_portal_7 = _draw_axes(ctx, overrides)
    requested_portals = {
        color
        for enabled, color in ((use_portal_6, 6), (use_portal_7, 7))
        if enabled
    }
    rng = ctx.draw_rng("teaching_layout")
    base_loops = {"easy": 2, "medium": 3, "hard": 4}[band]

    # Topology and placement are both searched.  This is a bounded constructive
    # search over fresh random mazes, not a replay bank.  Every accepted draw is
    # independently checked against the executable rivals above.
    for topology_index in range(24):
        extra_loops = base_loops + (topology_index % 2)
        base = _perfect_maze(h, w, rng, extra_loops=extra_loops)
        for _ in range(320):
            grid = _candidate_from_open_cells(
                base,
                rng,
                use_portal_6=use_portal_6,
                use_portal_7=use_portal_7,
            )
            if grid is not None and _teaches_rule(grid, requested_portals):
                return grid
    raise RuntimeError(
        "could not construct a portal/checkpoint counterexample for "
        f"shape={h}x{w}, portal6={use_portal_6}, portal7={use_portal_7}"
    )


def observe_overrides(grid) -> dict[str, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("cannot observe axes on an empty or malformed grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "use_portal_6": int(len(_positions(grid, 6)) == 2),
        "use_portal_7": int(len(_positions(grid, 7)) == 2),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]
    if any(type(value) is not int for row in grid for value in row):
        errors.append("grid values must be integer ARC colors, not bools or other types")
        return errors
    height = len(grid)
    if not 7 <= height <= 13:
        errors.append(f"height {height} outside supported 7..13")
    if not 9 <= width <= 16:
        errors.append(f"width {width} outside supported 9..16")
    unexpected = sorted({value for row in grid for value in row} - _ALLOWED_INPUT_COLORS)
    if unexpected:
        errors.append(f"unexpected input colors {unexpected}")
    if any(value != 8 for value in grid[0]) or any(value != 8 for value in grid[-1]):
        errors.append("top and bottom borders must be all color 8")
    if any(row[0] != 8 or row[-1] != 8 for row in grid):
        errors.append("left and right borders must be all color 8")
    for color, name in ((2, "start"), (3, "goal"), (5, "checkpoint")):
        hits = _positions(grid, color)
        if len(hits) != 1:
            errors.append(f"expected exactly one {name} color {color}, found {len(hits)}")
        elif not (0 < hits[0][0] < height - 1 and 0 < hits[0][1] < width - 1):
            errors.append(f"{name} color {color} must be interior")
    for color in (6, 7):
        count = len(_positions(grid, color))
        if count not in (0, 2):
            errors.append(f"portal color {color} appears {count} times, expected 0 or 2")
    interior = [
        grid[r][c]
        for r in range(1, height - 1)
        for c in range(1, width - 1)
    ]
    if 8 not in interior:
        errors.append("no interior color-8 wall")
    if 0 not in interior:
        errors.append("no interior color-0 background")
    if not errors and _state_path(grid, portals=True) is None:
        errors.append("no route from start to goal after visiting checkpoint")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in CANONICAL_PROFILES:
        return [f"profile {profile} is outside exact canonical support {sorted(CANONICAL_PROFILES)}"]
    return []


def _safe_disagreement(grid, rival) -> bool:
    try:
        return not self_check(grid) and _apply_intended(grid) != rival(grid)
    except (TypeError, ValueError, IndexError, KeyError):
        return False


def _goal_first_witness(grid) -> bool:
    return _safe_disagreement(grid, _goal_first_then_checkpoint)


def _direct_witness(grid) -> bool:
    return _safe_disagreement(grid, _direct_to_goal)


def _portal_6_witness(grid) -> bool:
    return 6 in _used_portal_colors(grid) and _safe_disagreement(grid, _ignore_portals)


def _portal_7_witness(grid) -> bool:
    return 7 in _used_portal_colors(grid) and _safe_disagreement(grid, _ignore_portals)


SEMANTIC_RIVALS = {
    "goal_first_then_checkpoint": _goal_first_then_checkpoint,
    "direct_to_goal": _direct_to_goal,
    "ignore_portals": _ignore_portals,
}
SEMANTIC_WITNESSES = {
    "goal_first_counterexample": _goal_first_witness,
    "direct_path_counterexample": _direct_witness,
    "portal_6_required": _portal_6_witness,
    "portal_7_required": _portal_7_witness,
}
WITNESS_RIVALS = {
    "goal_first_counterexample": ["goal_first_then_checkpoint"],
    "direct_path_counterexample": ["direct_to_goal"],
    "portal_6_required": ["ignore_portals"],
    "portal_7_required": ["ignore_portals"],
}
CANONICAL_SHORTCUTS = {
    "goal_first_then_checkpoint": SEMANTIC_RIVALS["goal_first_then_checkpoint"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return errors
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output grids")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            errors.append(f"pair {index} invalid input: {input_errors[0]}")
            continue
        if _apply_intended(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} disagrees with selected checkpoint-state rule")
    if errors:
        return errors
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute competitor {name!r}")
    return errors
