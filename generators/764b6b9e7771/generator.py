"""Constructive input generator for ARC task 764b6b9e7771.

Rule authority is unchanged: a beam starts at red (2), travels toward the
cardinal-adjacent blue marker (1), paints empty cells 8, reflects from diagonal
mirror colors 4/6, and stops at a gray wall (5), the grid edge, or a repeated
position+direction state.

The canonical demonstrations never make the beam touch an obstacle.  Generated
lessons therefore use a compact serpentine route in which every requested
mirror is encountered.  Routes with three or more mirrors deliberately mix
left and right relative turns, defeating both the canonical straight-ray
shortcut and the stronger "only the first two mirrors matter" shortcut.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "764b6b9e7771"
TASK_ID = GENERATOR_ID
RULE_HASH = "b28f2ec65f40"
VERSION = "4.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "A red(2) source and adjacent blue(1) heading launch a beam. Empty path "
    "cells become 8; diagonal mirrors 4/6 turn the beam according to their "
    "orientation; gray(5) blocks it. Every requested mirror lies on a compact "
    "serpentine route; 3+ mirror routes mix relative turn directions."
)

INVARIANTS = [
    "exactly one red source and one cardinal-adjacent blue heading marker",
    "every requested mirror is encountered by the beam; none is a dead distractor",
    "routes with at least three mirrors contain both left and right relative turns",
    "n_walls=0 stops at the edge; n_walls>0 includes an on-path wall and stops there",
    "every three consecutive default examples refute all declared canonical-fitting rivals",
    "all advertised axes are exact, pixel-observable, and available in every difficulty band",
]

DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
DELTA_TO_DIRECTION = {delta: name for name, delta in DIRECTIONS.items()}
TURN_SIDES = ("left", "right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 9..18; canonical sizes 9..11 favored",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 12..20; canonical sizes 12..13 favored",
        "valid": "12..20",
    },
    "n_mirrors": {
        "type": "int",
        "default": "cycles 2,3,4,5,6 by sample_index; exact override 2..6",
        "valid": "2..6",
    },
    "n_walls": {
        "type": "int",
        "default": "0..6; connected 4..6-cell blockers favored",
        "valid": "0..6",
    },
    "direction": {
        "type": "str",
        "default": "uniform",
        "valid": "up|down|left|right",
    },
    "turn_side": {
        "type": "str",
        "default": "uniform",
        "valid": "left|right",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_ALLOWED_COLORS = frozenset({0, 1, 2, 4, 5, 6})


def _add(point: tuple[int, int], vector: tuple[int, int], scale: int = 1) -> tuple[int, int]:
    return point[0] + scale * vector[0], point[1] + scale * vector[1]


def _neg(vector: tuple[int, int]) -> tuple[int, int]:
    return -vector[0], -vector[1]


def _right(vector: tuple[int, int]) -> tuple[int, int]:
    """Cardinal vector obtained by turning right in row/column coordinates."""
    return vector[1], -vector[0]


def _inside(point: tuple[int, int], h: int, w: int) -> bool:
    return 0 <= point[0] < h and 0 <= point[1] < w


def _reflect(vector: tuple[int, int], mirror: int) -> tuple[int, int]:
    dr, dc = vector
    if mirror == 4:
        return -dc, -dr
    if mirror == 6:
        return dc, dr
    raise ValueError(f"not a mirror color: {mirror!r}")


def _turned(vector: tuple[int, int], side: str) -> tuple[int, int]:
    right = _right(vector)
    return right if side == "right" else _neg(right)


def _mirror_for_turn(vector: tuple[int, int], side: str) -> int:
    desired = _turned(vector, side)
    for mirror in (4, 6):
        if _reflect(vector, mirror) == desired:
            return mirror
    raise RuntimeError(f"no mirror maps {vector} to a {side} turn")


def _relative_turn(
    before: tuple[int, int], after: tuple[int, int]
) -> str:
    right = _right(before)
    if after == right:
        return "right"
    if after == _neg(right):
        return "left"
    raise ValueError(f"non-cardinal quarter turn: {before!r} -> {after!r}")


def _markers(grid) -> tuple[tuple[int, int], tuple[int, int]]:
    red = []
    blue = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red.append((r, c))
            elif value == 1:
                blue.append((r, c))
    if len(red) != 1 or len(blue) != 1:
        raise ValueError(
            f"expected exactly one red(2) and one blue(1), got {len(red)} and {len(blue)}"
        )
    return red[0], blue[0]


def _trace_report(grid, *, swap_mirrors: bool = False):
    """Execute the rule without mutating ``grid`` and return output + evidence."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    if (dr, dc) not in DELTA_TO_DIRECTION:
        raise ValueError("blue(1) must be cardinal-adjacent to red(2)")

    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    visited: set[tuple[int, int, int, int]] = set()
    traversed: list[tuple[int, int]] = []
    painted: list[tuple[int, int]] = []
    mirrors: list[tuple[int, int, int]] = []
    turn_sides: list[str] = []

    while True:
        state = (r, c, dr, dc)
        if state in visited:
            stop = "loop"
            break
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            stop = "edge"
            break
        cell = grid[nr][nc]
        if cell == 5:
            stop = "wall"
            break
        traversed.append((nr, nc))
        if cell == 0:
            out[nr][nc] = 8
            painted.append((nr, nc))
        if cell in (4, 6):
            mirrors.append((nr, nc, cell))
            use = 10 - cell if swap_mirrors else cell
            before = (dr, dc)
            dr, dc = _reflect(before, use)
            turn_sides.append(_relative_turn(before, (dr, dc)))
        r, c = nr, nc

    return out, {
        "painted": tuple(painted),
        "mirrors": tuple(mirrors),
        "turn_sides": tuple(turn_sides),
        "stop": stop,
        "states": len(visited),
        "traversed": tuple(traversed),
    }


def _trace(grid):
    """Backward-compatible compact trace result used by older local probes."""
    out, report = _trace_report(grid)
    return out, len(report["painted"])


def _intended_output(grid):
    return _trace_report(grid)[0]


def _distance_to_edge(point: tuple[int, int], vector: tuple[int, int], h: int, w: int) -> int:
    distance = 0
    while _inside(_add(point, vector, distance + 1), h, w):
        distance += 1
    return distance


def _turn_sequence(first_side: str, n_mirrors: int) -> tuple[str, ...]:
    """R,R,L,L,... (or its mirror), making a compact non-self-crossing snake."""
    opposite = "left" if first_side == "right" else "right"
    return tuple(
        first_side if (index // 2) % 2 == 0 else opposite
        for index in range(n_mirrors)
    )


def _route_geometry(
    start: tuple[int, int],
    initial: tuple[int, int],
    first_side: str,
    n_mirrors: int,
):
    """Return arrow, route mirrors, final direction, and traversed route cells."""
    position = start
    direction = initial
    mirrors: list[tuple[tuple[int, int], int, str]] = []
    traversed: list[tuple[int, int]] = []
    for side in _turn_sequence(first_side, n_mirrors):
        midpoint = _add(position, direction)
        mirror = _add(position, direction, 2)
        traversed.extend((midpoint, mirror))
        color = _mirror_for_turn(direction, side)
        mirrors.append((mirror, color, side))
        direction = _turned(direction, side)
        position = mirror
    return _add(start, initial), tuple(mirrors), direction, tuple(traversed)


def _placement_bounds(
    offsets: set[tuple[int, int]], h: int, w: int
) -> tuple[int, int, int, int] | None:
    """Inclusive source-position bounds that keep all relative offsets in-grid."""
    row_lo = max(-dr for dr, _ in offsets)
    row_hi = min(h - 1 - dr for dr, _ in offsets)
    col_lo = max(-dc for _, dc in offsets)
    col_hi = min(w - 1 - dc for _, dc in offsets)
    if row_lo > row_hi or col_lo > col_hi:
        return None
    return row_lo, row_hi, col_lo, col_hi


@lru_cache(maxsize=32768)
def _candidate_layouts(
    h: int,
    w: int,
    direction: str,
    turn_side: str,
    n_mirrors: int,
    n_walls: int,
) -> tuple[
    tuple[
        int | None,
        tuple[int, int] | None,
        int,
        int,
        int,
        int,
    ],
    ...,
]:
    """Return compact families covering every legal concrete route placement.

    A family stores wall distance/orientation plus an inclusive rectangle of
    valid source positions.  This is equivalent to enumerating every concrete
    layout but keeps exhaustive override checks fast and memory-bounded.
    """
    initial = DIRECTIONS[direction]
    _, mirrors, final, traversed = _route_geometry(
        (0, 0), initial, turn_side, n_mirrors
    )
    occupied = {(0, 0), *traversed}
    if len(occupied) != len(traversed) + 1:
        return ()
    last_mirror = mirrors[-1][0]

    # A final ray must not run back into the already constructed route.
    occupied_ray_distances = set()
    for cell in occupied:
        delta = cell[0] - last_mirror[0], cell[1] - last_mirror[1]
        distance = None
        if final[0] and delta[1] == 0 and delta[0] * final[0] > 0:
            distance = delta[0] * final[0]
        elif final[1] and delta[0] == 0 and delta[1] * final[1] > 0:
            distance = delta[1] * final[1]
        if distance is not None:
            occupied_ray_distances.add(distance)
    if occupied_ray_distances:
        return ()

    families = []
    if n_walls == 0:
        # Keeping the second post-mirror cell in-grid guarantees a visible
        # final leg before the beam exits the edge.
        required = set(occupied)
        required.add(_add(last_mirror, final, 2))
        bounds = _placement_bounds(required, h, w)
        if bounds is not None:
            families.append((None, None, *bounds))
        return tuple(families)

    perpendicular = _right(final)
    wall_steps = (perpendicular,) if n_walls == 1 else (
        perpendicular,
        _neg(perpendicular),
    )
    for wall_distance in range(2, 8):
        blocker = _add(last_mirror, final, wall_distance)
        for wall_step in wall_steps:
            wall_cells = {
                _add(blocker, wall_step, index)
                for index in range(n_walls)
            }
            if wall_cells & occupied:
                continue
            required = set(occupied) | wall_cells
            bounds = _placement_bounds(required, h, w)
            if bounds is not None:
                families.append((wall_distance, wall_step, *bounds))
    return tuple(families)


def _choose_layout(ctx, families):
    """Choose uniformly over all concrete source positions in all families."""
    weighted = []
    total = 0
    for family in families:
        _distance, _step, row_lo, row_hi, col_lo, col_hi = family
        count = (row_hi - row_lo + 1) * (col_hi - col_lo + 1)
        total += count
        weighted.append((total, family))
    if total <= 0:
        raise RuntimeError("constructive route family has no concrete placement")
    pick = ctx.draw_rng("route_layout").randrange(total)
    previous = 0
    for cumulative, family in weighted:
        if pick < cumulative:
            distance, step, row_lo, row_hi, col_lo, col_hi = family
            local = pick - previous
            width = col_hi - col_lo + 1
            start = row_lo + local // width, col_lo + local % width
            return start, distance, step
        previous = cumulative
    raise RuntimeError("weighted layout choice fell through")


def _weighted_int_options(
    lo: int,
    hi: int,
    *,
    common: tuple[int, ...] = (),
    difficulty: str | None = None,
    easy: tuple[int, ...] = (),
    medium: tuple[int, ...] = (),
    hard: tuple[int, ...] = (),
) -> tuple[int, ...]:
    options = list(range(lo, hi + 1))
    options.extend(common)
    if difficulty == "easy":
        options.extend(easy)
    elif difficulty == "medium":
        options.extend(medium)
    elif difficulty == "hard":
        options.extend(hard)
    return tuple(options)


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES or (
        difficulty is not None and type(difficulty) is not str
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        expected = AXES[name]["type"]
        if expected == "int" and type(value) is not int:
            raise TypeError(f"{name} must be an int, not {type(value).__name__}")
        if expected == "str" and type(value) is not str:
            raise TypeError(f"{name} must be a str, not {type(value).__name__}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = ctx.draw_choice(
        "grid_h",
        _weighted_int_options(
            9,
            18,
            common=(9, 9, 10, 10, 11, 11),
            difficulty=difficulty,
            easy=(9, 10, 11),
            medium=(10, 11, 12),
            hard=(11, 14, 16, 18),
        ),
    )
    w = ctx.draw_choice(
        "grid_w",
        _weighted_int_options(
            12,
            20,
            common=(12, 12, 12, 13, 13, 13),
            difficulty=difficulty,
            easy=(12, 13),
            medium=(12, 13, 15),
            hard=(13, 17, 19, 20),
        ),
    )
    scheduled_mirrors = 2 + (int(sample_index) % 5)
    if "n_mirrors" in overrides and overrides["n_mirrors"] is not None:
        n_mirrors = ctx.draw_int("n_mirrors", 2, 6)
    else:
        n_mirrors = ctx.draw_int(
            "n_mirrors", scheduled_mirrors, scheduled_mirrors
        )
    n_walls = ctx.draw_choice(
        "n_walls",
        _weighted_int_options(
            0,
            6,
            common=(4, 5, 5, 6, 6),
            difficulty=difficulty,
            easy=(0, 1, 4),
            medium=(3, 4, 5),
            hard=(5, 6, 6),
        ),
    )
    direction = ctx.draw_choice("direction", tuple(DIRECTIONS))
    turn_side = ctx.draw_choice("turn_side", TURN_SIDES)

    candidates = _candidate_layouts(
        h, w, direction, turn_side, n_mirrors, n_walls
    )
    if not candidates:
        raise RuntimeError(
            "advertised override combination has no constructive route: "
            f"{h=} {w=} {direction=} {turn_side=} "
            f"{n_mirrors=} {n_walls=}"
        )
    start, wall_distance, wall_step = _choose_layout(ctx, candidates)

    initial = DIRECTIONS[direction]
    arrow, mirrors, final, _ = _route_geometry(
        start, initial, turn_side, n_mirrors
    )
    grid = full_grid(h, w, 0)
    grid[start[0]][start[1]] = 2
    grid[arrow[0]][arrow[1]] = 1
    for (mr, mc), color, _side in mirrors:
        if grid[mr][mc] != 0:
            raise RuntimeError("constructive mirror placement collision")
        grid[mr][mc] = color

    if n_walls:
        if wall_distance is None or wall_step is None:
            raise RuntimeError("wall route omitted exact wall placement")
        blocker = _add(mirrors[-1][0], final, wall_distance)
        for index in range(n_walls):
            wr, wc = _add(blocker, wall_step, index)
            if grid[wr][wc] != 0:
                raise RuntimeError("constructive wall placement collision")
            grid[wr][wc] = 5

    expected_axes = {
        "grid_h": h,
        "grid_w": w,
        "n_mirrors": n_mirrors,
        "n_walls": n_walls,
        "direction": direction,
        "turn_side": turn_side,
    }
    if observe_overrides(grid) != expected_axes:
        raise RuntimeError("generated pixels do not match recorded exact axes")

    _, report = _trace_report(grid)
    expected_stop = "edge" if n_walls == 0 else "wall"
    expected_turns = _turn_sequence(turn_side, n_mirrors)
    if (
        report["stop"] != expected_stop
        or len(report["mirrors"]) != n_mirrors
        or report["turn_sides"] != expected_turns
    ):
        raise RuntimeError(f"constructed route failed: {report}")
    return grid


def observe_overrides(grid):
    """Recover every exact public axis from returned pixels alone."""
    start, arrow = _markers(grid)
    delta = arrow[0] - start[0], arrow[1] - start[1]
    if delta not in DELTA_TO_DIRECTION:
        raise ValueError("blue(1) must be cardinal-adjacent to red(2)")
    _, report = _trace_report(grid)
    if not report["mirrors"]:
        raise ValueError("turn_side is unobservable because the route hits no mirror")
    first_color = report["mirrors"][0][2]
    after = _reflect(delta, first_color)
    right = _right(delta)
    if after == right:
        turn_side = "right"
    elif after == _neg(right):
        turn_side = "left"
    else:
        raise ValueError("first mirror did not produce a cardinal quarter-turn")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_mirrors": sum(value in (4, 6) for row in grid for value in row),
        "n_walls": sum(value == 5 for row in grid for value in row),
        "direction": DELTA_TO_DIRECTION[delta],
        "turn_side": turn_side,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a lawful rule input, including canonical examples.

    Canonical examples intentionally do not require interacting obstacles, so
    interaction-specific curriculum guarantees live in generation tests and
    semantic witnesses rather than narrowing this lawful-input validator.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in _ALLOWED_COLORS for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,4,5,6"]
    if len(grid) > 30 or width > 30:
        return [f"grid too large: {len(grid)}x{width}"]

    errors = []
    try:
        start, arrow = _markers(grid)
    except ValueError as exc:
        return [str(exc)]
    delta = arrow[0] - start[0], arrow[1] - start[1]
    if delta not in DELTA_TO_DIRECTION:
        errors.append("blue(1) must be cardinal-adjacent to red(2)")
    mirror_count = sum(value in (4, 6) for row in grid for value in row)
    if mirror_count == 0:
        errors.append("expected at least one mirror cell (4 or 6)")
    if errors:
        return errors
    try:
        _, report = _trace_report(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [f"beam trace failed: {exc}"]
    if not report["painted"]:
        errors.append("beam paints no empty cell")
    return errors


def strict_canonical_like(grid):
    """Lawful inputs for the pinned rule; canonical demonstrations must pass."""
    return self_check(grid)


def _straight_to_edge(grid):
    """Rival: ignore mirrors and walls, preserving only the launch direction."""
    start, arrow = _markers(grid)
    dr, dc = arrow[0] - start[0], arrow[1] - start[1]
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    r, c = start
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w):
            return out
        if grid[r][c] == 0:
            out[r][c] = 8


def _stop_at_first_obstacle(grid):
    """Rival: draw the launch ray and treat either mirror as a blocker."""
    start, arrow = _markers(grid)
    dr, dc = arrow[0] - start[0], arrow[1] - start[1]
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    r, c = arrow
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            return out
        out[r][c] = 8


def _swapped_mirrors(grid):
    """Rival: assign the two diagonal reflection formulas to opposite colors."""
    return _trace_report(grid, swap_mirrors=True)[0]


def _first_two_mirrors_only(grid):
    """Rival: reflect at only the first two encountered mirrors."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    visited: set[tuple[int, int, int, int]] = set()
    mirror_index = 0
    while True:
        state = (r, c, dr, dc)
        if state in visited:
            return out
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
            return out
        cell = grid[nr][nc]
        if cell == 0:
            out[nr][nc] = 8
        elif cell in (4, 6):
            mirror_index += 1
            if mirror_index <= 2:
                dr, dc = _reflect((dr, dc), cell)
        r, c = nr, nc


def _repeat_first_turn_side(grid):
    """Rival: every mirror repeats the first mirror's relative turn."""
    start, arrow = _markers(grid)
    r, c = start
    dr, dc = arrow[0] - r, arrow[1] - c
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    visited: set[tuple[int, int, int, int]] = set()
    first_side: str | None = None
    while True:
        state = (r, c, dr, dc)
        if state in visited:
            return out
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
            return out
        cell = grid[nr][nc]
        if cell == 0:
            out[nr][nc] = 8
        elif cell in (4, 6):
            before = (dr, dc)
            if first_side is None:
                after = _reflect(before, cell)
                first_side = _relative_turn(before, after)
                dr, dc = after
            else:
                dr, dc = _turned(before, first_side)
        r, c = nr, nc


def _has_all_mirrors_interact(grid) -> bool:
    try:
        _, report = _trace_report(grid)
    except (TypeError, ValueError, IndexError):
        return False
    total = sum(value in (4, 6) for row in grid for value in row)
    return total >= 2 and len(report["mirrors"]) == total


def _has_mixed_turn_route(grid) -> bool:
    try:
        _, report = _trace_report(grid)
    except (TypeError, ValueError, IndexError):
        return False
    total = sum(value in (4, 6) for row in grid for value in row)
    return (
        total >= 3
        and len(report["mirrors"]) == total
        and set(report["turn_sides"]) == {"left", "right"}
    )


SEMANTIC_WITNESSES = {
    "all_mirrors_interact": _has_all_mirrors_interact,
    "mixed_turn_route": _has_mixed_turn_route,
}
SEMANTIC_RIVALS = {
    "straight_to_edge": _straight_to_edge,
    "stop_at_first_obstacle": _stop_at_first_obstacle,
    "swapped_mirrors": _swapped_mirrors,
    "first_two_mirrors_only": _first_two_mirrors_only,
    "repeat_first_turn_side": _repeat_first_turn_side,
}
WITNESS_RIVALS = {
    "all_mirrors_interact": [
        "straight_to_edge",
        "stop_at_first_obstacle",
        "swapped_mirrors",
    ],
    "mixed_turn_route": [
        "first_two_mirrors_only",
        "repeat_first_turn_side",
    ],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite-rival claim: every named competitor must fail on a demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demonstration {index} is missing input/output")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                errors.append(f"declared rival survives all demos: {name}")
        except Exception as exc:
            errors.append(f"rival {name} raised {type(exc).__name__}: {exc}")
    return errors
