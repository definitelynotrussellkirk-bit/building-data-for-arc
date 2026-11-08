"""Generator for ARC task 204c79678d9d — key/door shortest path.

The input is a wall-dense maze with one start (2), goal (3), key (5), and
locked door (6).  The Racket oracle performs a stateful BFS: the goal is only
accepted after the key has been collected, and the door is passable only in
that state.  Background cells on the chosen path are painted 4.

Ordinary lessons alternate two complementary scene families:

* ``traversed`` — the key is in a side branch and the accepting path returns
  to the main corridor before traversing the door.
* ``blocking_shortcut`` — the door lies on a tempting short route, while the
  accepting path must use an open bypass and detour to the key; the door is not
  used in the answer.

Together they reject the common shortcuts "visit the key but ignore door
state", "treat the door as a wall", and "paint the geometric shortest path".
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "204c79678d9d"
TASK_ID = "204c79678d9d"
VERSION = "4.0.0"
RULE_HASH = "ceebeab4f15a"  # sha256[:12] of normalized canonical program_solution
EXAMPLES_NEEDED = 3

SUMMARY = (
    "In a wall-dense color-8 maze, find a stateful shortest route from the "
    "single start 2 to the single goal 3. The goal is accepted only after "
    "visiting key 5, and door 6 is passable only after that visit. Preserve "
    "all markers and walls; paint only traversed background-0 cells yellow 4. "
    "Lessons alternate a canonical key-detour/door-traversal case and a "
    "locked-door-shortcut case whose correct path bypasses the door."
)

INVARIANTS = [
    "the rectangular grid uses only colors 0,2,3,5,6,8 and has an all-8 border",
    "there is exactly one interior start 2, goal 3, key 5, and door 6",
    "a key-aware accepting path exists and paints at least two background cells",
    "the wall color 8 is modal and some open distractor cells remain unpainted",
    "the direct geometric path is not the official answer",
]

ORIENTATIONS = ("horizontal", "vertical")
DOOR_ROLES = ("traversed", "blocking_shortcut")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..12; every third sample anchors h=7",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 8..14; anchors cycle w=8,9,10",
        "valid": "8..14",
    },
    "orientation": {
        "type": "enum",
        "default": "alternates by sample_index",
        "valid": "horizontal|vertical",
    },
    "door_role": {
        "type": "enum",
        "default": "two traversed then two blocking_shortcut samples",
        "valid": "traversed|blocking_shortcut",
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED = {0, 2, 3, 5, 6, 8}


def _draw_int_axis(ctx, label: str, lo: int, hi: int, fixed: int | None) -> int:
    """Draw an exact axis while keeping scheduled defaults in provenance."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if fixed is not None:
        return ctx.draw_int(label, fixed, fixed)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_choice_axis(ctx, label: str, options, fixed: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (fixed,))


def _carve_horizontal(
    h: int, w: int, door_role: str, reverse: bool, variant: int = 0
) -> list[list[int]]:
    """Build a wall-filled horizontal teaching scene for every legal size."""
    g = full_grid(h, w, 8)
    top, bottom = 1, h - 2
    left, right = 1, w - 2
    door_options = list(range(left + 2, right - 1))
    door_c = door_options[variant % len(door_options)]

    def carve_row(r: int, c0: int, c1: int) -> None:
        for c in range(min(c0, c1), max(c0, c1) + 1):
            g[r][c] = 0

    def carve_col(c: int, r0: int, r1: int) -> None:
        for r in range(min(r0, r1), max(r0, r1) + 1):
            g[r][c] = 0

    if door_role == "traversed":
        # Direct top corridor plus a key-bearing dead-end branch before the door.
        branch_options = list(range(left + 1, door_c))
        branch_c = branch_options[(variant // len(door_options)) % len(branch_options)]
        dead_depth = 1 + ((variant // 7) % min(2, bottom - top))
        carve_row(top, left, right)
        carve_col(branch_c, top, bottom)
        # A variable goal-side dead end makes "paint every open cell" visibly
        # wrong and gives canonical-sized anchors several seeded realizations.
        carve_col(right, top, min(bottom, top + dead_depth))
        start = (top, left)
        goal = (top, right)
        key = (bottom, branch_c)
        door = (top, door_c)
    elif door_role == "blocking_shortcut":
        # A rectangular bypass leaves the top route shorter only if the locked
        # door is incorrectly treated as open.  The key sits in a side branch
        # off the bypass, so "goal without key" is a different answer too.
        carve_row(top, left, right)
        carve_row(bottom, left, right)
        carve_col(left, top, bottom)
        carve_col(right, top, bottom)
        # Put the key on the far-side ascent.  With the real locked door the
        # search must take the lower bypass before collecting it.  A rival that
        # opens the door from the start instead crosses the top, reaches the
        # goal-side column, descends to the key, and returns — a visibly
        # different painted route at every declared size.
        start = (top, left)
        goal = (top, right)
        key = (bottom - 1, right)
        door = (top, door_c)
    else:  # guarded by draw_choice, retained for direct callers
        raise ValueError(f"unknown door_role: {door_role!r}")

    g[start[0]][start[1]] = 2
    g[goal[0]][goal[1]] = 3
    g[key[0]][key[1]] = 5
    g[door[0]][door[1]] = 6

    if reverse:
        g = [list(reversed(row)) for row in g]
    return g


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    dimensions_overridden = any(
        name in overrides and overrides[name] is not None
        for name in ("grid_h", "grid_w")
    )
    canonical_anchor = not dimensions_overridden and sample_index % 3 == 0
    anchor_w = (8, 9, 10)[(sample_index // 3) % 3]
    h = _draw_int_axis(ctx, "grid_h", 7, 12, 7 if canonical_anchor else None)
    w = _draw_int_axis(ctx, "grid_w", 8, 14, anchor_w if canonical_anchor else None)

    orientation_default = ORIENTATIONS[sample_index % 2]
    role_default = DOOR_ROLES[(sample_index // 2) % 2]
    orientation = _draw_choice_axis(
        ctx, "orientation", ORIENTATIONS, orientation_default
    )
    door_role = _draw_choice_axis(ctx, "door_role", DOOR_ROLES, role_default)
    reverse = bool(ctx.draw_rng("direction").randint(0, 1))
    layout_variant = ctx.draw_rng("layout_variant").randrange(0, 2**31)

    if orientation == "horizontal":
        grid = _carve_horizontal(h, w, door_role, reverse, layout_variant)
    else:
        # Build the same semantic graph sideways, then transpose.  The helper's
        # minimum width is seven, so every declared h/w boundary is supported.
        grid = _transpose(_carve_horizontal(w, h, door_role, reverse, layout_variant))

    realized_meta = {
        "overrides": {
            "grid_h": h,
            "grid_w": w,
            "orientation": orientation,
            "door_role": door_role,
        }
    }
    errors = self_check(grid, meta=realized_meta)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a nonempty sequence"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (3 <= len(grid) <= 30 and 3 <= w <= 30):
        return ["grid dimensions must be within ARC bounds"]
    bad = [
        (r, c, v)
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if not isinstance(v, int) or isinstance(v, bool) or v not in _ALLOWED
    ]
    return [f"unexpected value {bad[0][2]!r} at {bad[0][:2]}"] if bad else []


def _positions(grid, value: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell == value
    ]


def _stateful_path(
    grid,
    *,
    require_key_at_goal: bool = True,
    door_mode: str = "locked_until_key",
) -> list[tuple[int, int, int]] | None:
    """Mirror the canonical Racket BFS, including its neighbour order."""
    starts = _positions(grid, 2)
    goals = _positions(grid, 3)
    keys = _positions(grid, 5)
    if len(starts) != 1 or len(goals) != 1 or len(keys) != 1:
        return None
    start, goal, key = starts[0], goals[0], keys[0]
    first = (start[0], start[1], int(start == key))
    queue = deque([first])
    prev: dict[tuple[int, int, int], tuple[int, int, int] | None] = {first: None}
    end = None
    h, w = len(grid), len(grid[0])
    while queue:
        r, c, has_key = queue.popleft()
        if (r, c) == goal and (has_key or not require_key_at_goal):
            end = (r, c, has_key)
            break
        for dr, dc in _DIR4:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 8:
                continue
            if value == 6:
                if door_mode == "always_blocked":
                    continue
                if door_mode == "locked_until_key" and not has_key:
                    continue
            next_has_key = int(bool(has_key) or (nr, nc) == key)
            state = (nr, nc, next_has_key)
            if state not in prev:
                prev[state] = (r, c, has_key)
                queue.append(state)
    if end is None:
        return None
    states = []
    cur = end
    while cur is not None:
        states.append(cur)
        cur = prev[cur]
    states.reverse()
    return states


def _paint_path(grid, path) -> list[list[int]]:
    out = [list(row) for row in grid]
    if path is None:
        return out
    for r, c, _ in path:
        if out[r][c] == 0:
            out[r][c] = 4
    return out


def rule_mirror(grid) -> list[list[int]]:
    return _paint_path(grid, _stateful_path(grid))


def _rival_direct(grid) -> list[list[int]]:
    """Geometric shortest path: door open and goal does not require key."""
    return _paint_path(
        grid,
        _stateful_path(grid, require_key_at_goal=False, door_mode="always_open"),
    )


def _rival_visit_key_door_open(grid) -> list[list[int]]:
    """Visit key before finishing, but ignore the door's locked state."""
    return _paint_path(
        grid,
        _stateful_path(grid, require_key_at_goal=True, door_mode="always_open"),
    )


def _rival_door_wall(grid) -> list[list[int]]:
    """Treat the door as permanently impassable."""
    return _paint_path(
        grid,
        _stateful_path(grid, require_key_at_goal=True, door_mode="always_blocked"),
    )


def _rival_paint_all_open(grid) -> list[list[int]]:
    return [[4 if value == 0 else value for value in row] for row in grid]


def _passable_connected(grid) -> bool:
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 8}
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _analysis(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    marker_positions = {value: _positions(grid, value) for value in (2, 3, 5, 6)}
    path = _stateful_path(grid)
    official = _paint_path(grid, path)
    door = marker_positions[6][0] if len(marker_positions[6]) == 1 else None
    path_positions = {(r, c) for r, c, _ in path} if path else set()
    start = marker_positions[2][0] if len(marker_positions[2]) == 1 else None
    goal = marker_positions[3][0] if len(marker_positions[3]) == 1 else None
    orientation = None
    if start is not None and goal is not None:
        orientation = (
            "horizontal"
            if abs(goal[1] - start[1]) >= abs(goal[0] - start[0])
            else "vertical"
        )
    return {
        "errors": errors,
        "h": h,
        "w": w,
        "markers": marker_positions,
        "path": path,
        "path_positions": path_positions,
        "official": official,
        "door_role": (
            "traversed" if door is not None and door in path_positions
            else "blocking_shortcut"
        ),
        "orientation": orientation,
        "palette": {v for row in grid for v in row},
        "counts": {v: sum(row.count(v) for row in grid) for v in _ALLOWED},
    }


def observe_overrides(grid) -> dict[str, Any]:
    info = _analysis(grid)
    if info.get("errors") or info.get("orientation") is None:
        return {}
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "orientation": info["orientation"],
        "door_role": info["door_role"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    for c in range(w):
        if grid[0][c] != 8 or grid[h - 1][c] != 8:
            errors.append("outer top/bottom border must be all color 8")
            break
    for r in range(h):
        if grid[r][0] != 8 or grid[r][w - 1] != 8:
            errors.append("outer left/right border must be all color 8")
            break
    for value, name in ((2, "start"), (3, "goal"), (5, "key"), (6, "door")):
        cells = _positions(grid, value)
        if len(cells) != 1:
            errors.append(f"expected exactly one {name}({value}), found {len(cells)}")
        elif cells[0][0] in (0, h - 1) or cells[0][1] in (0, w - 1):
            errors.append(f"{name}({value}) must be interior")
    if errors:
        return errors
    if not _passable_connected(grid):
        errors.append("all non-wall cells must form one connected corridor graph")

    info = _analysis(grid)
    path = info["path"]
    if path is None:
        errors.append("no accepting key-aware path from start to goal")
        return errors
    official = info["official"]
    painted = sum(value == 4 for row in official for value in row)
    zeros = sum(value == 0 for row in grid for value in row)
    if painted < 2:
        errors.append(f"path paints only {painted} background cells")
    if painted >= zeros:
        errors.append("no unpainted open distractor cells remain")
    if info["counts"][8] <= max(
        count for color, count in info["counts"].items() if color != 8
    ):
        errors.append("wall color 8 must be modal")
    if official == _rival_direct(grid):
        errors.append("direct geometric shortest path is not rebutted")

    requested = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    observed = observe_overrides(grid)
    for name, expected in requested.items():
        if name in AXES and expected is not None and observed.get(name) != expected:
            errors.append(
                f"override {name}={expected!r} realized as {observed.get(name)!r}"
            )

    # Canonical bank examples only promise the task rule and structural
    # profile.  Generated examples additionally promise a named teaching role,
    # so enforce the stronger counterfactual only when metadata requests it.
    requested_role = requested.get("door_role")
    if requested_role == "blocking_shortcut":
        if official == _rival_visit_key_door_open(grid):
            errors.append("locked door does not change the key-visiting answer")
    elif requested_role == "traversed":
        door = _positions(grid, 6)[0]
        key = _positions(grid, 5)[0]
        path_cells = [(r, c) for r, c, _ in path]
        if door not in path_cells or key not in path_cells:
            errors.append("traversed scene must visit key and door")
        elif path_cells.index(key) > path_cells.index(door):
            errors.append("door is traversed before key collection")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    info = _analysis(grid)
    if info["h"] != 7 or info["w"] not in (8, 9, 10):
        errors.append(
            f"canonical profile requires h=7 and w in 8..10, got {info['h']}x{info['w']}"
        )
    if info["palette"] != {0, 2, 3, 5, 6, 8}:
        errors.append(f"canonical palette mismatch: {sorted(info['palette'])}")
    return errors


MIN_STRICT_FRAC = 0.30


def _door_traversed(grid) -> bool:
    try:
        return not self_check(grid) and _analysis(grid)["door_role"] == "traversed"
    except Exception:
        return False


def _door_blocks_shortcut(grid) -> bool:
    try:
        return (
            not self_check(grid)
            and _analysis(grid)["door_role"] == "blocking_shortcut"
            and rule_mirror(grid) != _rival_visit_key_door_open(grid)
        )
    except Exception:
        return False


def _orientation_is(name: str) -> Callable[[Any], bool]:
    def predicate(grid) -> bool:
        try:
            return not self_check(grid) and _analysis(grid)["orientation"] == name
        except Exception:
            return False
    return predicate


def _key_changes_answer(grid) -> bool:
    try:
        return not self_check(grid) and rule_mirror(grid) != _rival_direct(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "door_traversed_after_key": _door_traversed,
    "locked_door_blocks_shortcut": _door_blocks_shortcut,
    "key_requirement_changes_answer": _key_changes_answer,
    "horizontal_layout": _orientation_is("horizontal"),
    "vertical_layout": _orientation_is("vertical"),
}


_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "direct_geometric_shortest_path": _rival_direct,
    "visit_key_but_door_always_open": _rival_visit_key_door_open,
    "door_is_permanent_wall": _rival_door_wall,
    "paint_all_open_cells": _rival_paint_all_open,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        expected = rule_mirror(pair["input"])
        if expected != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the pinned rule")
    if reasons:
        return reasons

    # Consecutive sample schedules intentionally put both roles and both
    # orientations in every 3-demo lesson.  Check the realized evidence rather
    # than trusting the schedule.
    demo_roles = {_analysis(pair["input"])["door_role"] for pair in demos}
    if demo_roles != set(DOOR_ROLES):
        reasons.append(f"demos cover door roles {sorted(demo_roles)}, need both")
    demo_orientations = {_analysis(pair["input"])["orientation"] for pair in demos}
    if demo_orientations != set(ORIENTATIONS):
        reasons.append(
            f"demos cover orientations {sorted(demo_orientations)}, need both"
        )

    query_input, query_output = query["input"], query["output"]
    for name, rival in _RIVALS.items():
        matches_every_demo = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        if matches_every_demo and rival(query_input) != query_output:
            reasons.append(
                f"rival {name!r} fits every demo but changes the query answer"
            )
    return reasons
