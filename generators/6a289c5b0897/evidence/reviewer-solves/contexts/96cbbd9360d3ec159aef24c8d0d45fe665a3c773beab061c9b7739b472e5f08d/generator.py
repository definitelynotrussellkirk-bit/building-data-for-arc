"""Generator for 6a289c5b0897 — ordered shortest path through gray walls.

The canonical Racket rule locates the one non-zero, non-gray color that occurs
exactly twice, starts at its first row-major occurrence, and performs BFS with
neighbor order up, down, left, right through colors 0 and the endpoint color.
It paints that one parent-selected shortest path on a fresh black grid.

The public examples contain shortest-path ties even though the prose calls the
path unique.  This generator therefore teaches both unique paths and deliberate
ties where the Racket neighbor order is observable.  In particular, generated
tie scenes refute a different BFS order that nevertheless reproduces every
canonical pair.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a289c5b0897"
TASK_ID = "6a289c5b0897"
VERSION = "4.0.0"
RULE_HASH = "d0e77b114425"

SUMMARY = (
    "A 4..6 by 5..8 maze uses black 0 as open space and gray 5 as walls. "
    "Exactly two cells share one endpoint color. Paint the BFS shortest path "
    "selected from the first row-major endpoint using neighbor order up, down, "
    "left, right; clear every other cell to black. The curriculum alternates "
    "unique routes with tied shortest routes that make that order observable."
)

INVARIANTS = [
    "input colors are 0, gray 5, and exactly one endpoint color",
    "the endpoint color is one of 1,2,3,4,6,7,8 and appears exactly twice",
    "at least three gray walls are present, so gray cannot be mistaken for an endpoint pair",
    "all non-wall cells form one 4-connected region containing both endpoints",
    "the authoritative path starts at the first row-major endpoint",
    "BFS neighbor order is up, down, left, right and is load-bearing on tied lessons",
    "the output is a fresh black grid containing only the selected path",
]

AXES = {
    "h": {
        "type": "int",
        "default": "scheduled over 4..6 with canonical 5-row anchors",
        "valid": "4..6",
    },
    "w": {
        "type": "int",
        "default": "scheduled over 5..8 with canonical 5/6-column anchors",
        "valid": "5..8",
    },
    "color": {
        "type": "int",
        "default": "keyed choice from 1|2|3|4|6|7|8",
        "valid": "1|2|3|4|6|7|8",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Cell = tuple[int, int]
Grid = list[list[int]]

_ENDPOINT_COLORS = (1, 2, 3, 4, 6, 7, 8)
# Exact order used by the selected Racket authority.
_DIRS: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
# This order reproduces all four canonical pairs, but differs on generated tie
# witnesses.  It is therefore a genuine canonical-fitting shortcut.
_ALT_DIRS: tuple[Cell, ...] = ((1, 0), (0, 1), (0, -1), (-1, 0))

# Half the default schedule uses canonical 5x5 / 5x6 shapes; the remainder
# widens morphology.  Even offsets preserve the tie/unique alternation.
_SHAPE_SCHEDULE: tuple[tuple[int, int], ...] = (
    (5, 5),
    (5, 6),
    (4, 7),
    (6, 8),
    (5, 6),
    (5, 5),
    (4, 8),
    (6, 7),
)

SCHEDULE_PROFILES = ("tied", "unique")


def _neighbors(cell: Cell, h: int, w: int, order: Iterable[Cell] = _DIRS):
    r, c = cell
    for dr, dc in order:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _bfs_distances(grid: Grid, start: Cell, allowed: set[int]) -> dict[Cell, int]:
    h, w = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for nxt in _neighbors(cell, h, w):
            if nxt in distances or grid[nxt[0]][nxt[1]] not in allowed:
                continue
            distances[nxt] = distances[cell] + 1
            queue.append(nxt)
    return distances


def _ordered_path(
    grid: Grid,
    start: Cell,
    goal: Cell,
    allowed: set[int],
    order: Iterable[Cell] = _DIRS,
) -> list[Cell]:
    """Return the parent-selected BFS path for one explicit neighbor order."""
    h, w = len(grid), len(grid[0])
    parent: dict[Cell, Cell | None] = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in _neighbors(cell, h, w, order):
            if nxt in parent or grid[nxt[0]][nxt[1]] not in allowed:
                continue
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


def _shortest_path_stats(
    grid: Grid, start: Cell, goal: Cell, allowed: set[int]
) -> tuple[int, set[Cell], dict[Cell, int], dict[Cell, int]]:
    """Return (path count capped at 2, all-shortest union, forward, reverse)."""
    forward = _bfs_distances(grid, start, allowed)
    if goal not in forward:
        return 0, set(), forward, {}
    reverse = _bfs_distances(grid, goal, allowed)
    total = forward[goal]
    shortest_cells = {
        cell
        for cell, distance in forward.items()
        if cell in reverse and distance + reverse[cell] == total
    }

    by_distance: dict[int, list[Cell]] = {}
    for cell in shortest_cells:
        by_distance.setdefault(forward[cell], []).append(cell)
    ways: dict[Cell, int] = {start: 1}
    h, w = len(grid), len(grid[0])
    for distance in range(total):
        for cell in by_distance.get(distance, ()):  # deterministic count only
            for nxt in _neighbors(cell, h, w):
                if nxt not in shortest_cells or forward.get(nxt) != distance + 1:
                    continue
                ways[nxt] = min(2, ways.get(nxt, 0) + ways.get(cell, 0))
    return ways.get(goal, 0), shortest_cells, forward, reverse


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


def _row_first_cells(start: Cell, goal: Cell) -> list[Cell]:
    """A common wrong rule: ignore walls, move vertically, then horizontally."""
    r, c = start
    cells = [(r, c)]
    if goal[0] != r:
        step = 1 if goal[0] > r else -1
        while r != goal[0]:
            r += step
            cells.append((r, c))
    if goal[1] != c:
        step = 1 if goal[1] > c else -1
        while c != goal[1]:
            c += step
            cells.append((r, c))
    return cells


def _analyze(grid) -> dict[str, object]:
    """Total validator/analyzer for canonical and generated inputs."""
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"]}
    h = len(grid)
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be rectangular lists"]}

    errors: list[str] = []
    if not 4 <= h <= 6:
        errors.append(f"grid height {h} outside 4..6")
    if not 5 <= w <= 8:
        errors.append(f"grid width {w} outside 5..8")

    by_color: dict[int, list[Cell]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            by_color.setdefault(value, []).append((r, c))
    if any("invalid ARC color" in error for error in errors):
        return {"errors": errors}

    extra_colors = sorted(color for color in by_color if color not in (0, 5))
    if len(extra_colors) != 1:
        errors.append(
            "expected exactly one non-zero non-gray endpoint color, got "
            f"{extra_colors}"
        )
        return {"errors": errors}
    color = extra_colors[0]
    if color not in _ENDPOINT_COLORS:
        errors.append(f"endpoint color {color} is not allowed")
    endpoints = sorted(by_color[color])
    if len(endpoints) != 2:
        errors.append(
            f"expected endpoint color {color} exactly twice, got {len(endpoints)}"
        )
        return {"errors": errors}

    walls = set(by_color.get(5, ()))
    zeros = set(by_color.get(0, ()))
    if len(walls) < 3:
        errors.append(
            f"expected at least three gray walls (and not a gray pair), got {len(walls)}"
        )
    if len(zeros) < 2:
        errors.append(f"expected at least two open black cells, got {len(zeros)}")

    start, goal = endpoints
    allowed = {0, color}
    path = _ordered_path(grid, start, goal, allowed, _DIRS)
    if not path:
        errors.append("endpoints are disconnected through colors 0 and endpoint color")
        return {
            "errors": errors,
            "h": h,
            "w": w,
            "color": color,
            "endpoints": endpoints,
            "walls": walls,
            "zeros": zeros,
        }

    path_count, shortest_cells, forward, reverse = _shortest_path_stats(
        grid, start, goal, allowed
    )
    walkable = zeros | set(endpoints)
    if len(forward) != len(walkable):
        errors.append(
            f"all non-wall cells must be connected; {len(walkable) - len(forward)} are isolated"
        )

    path_cells = set(path)
    off_path_zeros = zeros - path_cells
    return {
        "errors": errors,
        "h": h,
        "w": w,
        "color": color,
        "endpoints": endpoints,
        "start": start,
        "goal": goal,
        "walls": walls,
        "zeros": zeros,
        "wall_count": len(walls),
        "walkable_count": len(walkable),
        "path": path,
        "path_cells": path_cells,
        "path_distance": len(path) - 1,
        "shortest_path_count": path_count,
        "shortest_cells": shortest_cells,
        "turns": _turn_count(path),
        "off_path_zero_count": len(off_path_zeros),
        "forward_distances": forward,
        "reverse_distances": reverse,
        "wall_density": len(walls) / (h * w),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return reasons when a grid is outside the supported rule domain."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "h": int(analysis["h"]),
        "w": int(analysis["w"]),
        "color": int(analysis["color"]),
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    h = int(analysis["h"])
    w = int(analysis["w"])
    return {
        **observe_overrides(grid),
        "path_distance": analysis["path_distance"],
        "shortest_path_count": analysis["shortest_path_count"],
        "tied_shortest_paths": int(analysis["shortest_path_count"]) >= 2,
        "unique_shortest_path": analysis["shortest_path_count"] == 1,
        "turns": analysis["turns"],
        "off_path_zero_count": analysis["off_path_zero_count"],
        "wall_count": analysis["wall_count"],
        "canonical_shape": (h, w) in {(5, 5), (5, 6)},
    }


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return "tied" if sample_index % 2 == 0 else "unique"


def _draw_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use full legal bounds for overrides; otherwise pin the schedule value."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for label in ("h", "w", "color"):
        if label not in overrides or overrides[label] is None:
            continue
        value = overrides[label]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"override {label!r} must be an exact integer, got {value!r}")
    if "h" in overrides and overrides["h"] is not None and not 4 <= overrides["h"] <= 6:
        raise ValueError(f"override 'h' outside 4..6: {overrides['h']!r}")
    if "w" in overrides and overrides["w"] is not None and not 5 <= overrides["w"] <= 8:
        raise ValueError(f"override 'w' outside 5..8: {overrides['w']!r}")
    if (
        "color" in overrides
        and overrides["color"] is not None
        and overrides["color"] not in _ENDPOINT_COLORS
    ):
        raise ValueError(
            f"override 'color' must be one of {_ENDPOINT_COLORS}, got {overrides['color']!r}"
        )


def _all_free_connected(grid: Grid) -> bool:
    free = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    ]
    if not free:
        return False
    return len(_bfs_distances(grid, free[0], {0})) == len(free)


def _candidate_info(grid: Grid, start: Cell, goal: Cell, profile: str):
    allowed = {0}
    path = _ordered_path(grid, start, goal, allowed, _DIRS)
    if not path:
        return None
    distance = len(path) - 1
    count, shortest_cells, _forward, _reverse = _shortest_path_stats(
        grid, start, goal, allowed
    )
    if profile == "tied":
        if count < 2 or shortest_cells == set(path):
            return None
        alternate = _ordered_path(grid, start, goal, allowed, _ALT_DIRS)
        if not alternate or set(alternate) == set(path):
            return None
    elif profile == "unique":
        if count != 1:
            return None
    else:  # internal contract guard
        raise ValueError(f"unknown schedule profile: {profile!r}")

    if _turn_count(path) < 1:
        return None
    if len([cell for cell in shortest_cells if cell not in path]) < (1 if profile == "tied" else 0):
        return None
    if set(_row_first_cells(start, goal)) == set(path):
        return None
    free_count = sum(value == 0 for row in grid for value in row)
    if free_count - len(path) < 2:
        return None
    return {
        "start": start,
        "goal": goal,
        "path": path,
        "distance": distance,
        "turns": _turn_count(path),
        "shortest_path_count": count,
    }


def _select_candidate(candidates, difficulty, rng):
    candidates = sorted(
        candidates,
        key=lambda item: (item["distance"], item["turns"], item["start"], item["goal"]),
    )
    third = max(1, len(candidates) // 3)
    if difficulty == "easy":
        pool = candidates[:third]
    elif difficulty == "hard":
        pool = candidates[-third:]
    else:
        begin = max(0, (len(candidates) - third) // 2)
        pool = candidates[begin:begin + third]
    return rng.choice(pool)


def _build_grid(
    h: int,
    w: int,
    color: int,
    profile: str,
    difficulty,
    rng,
) -> Grid:
    density_ranges = {
        None: (0.18, 0.36),
        "easy": (0.15, 0.28),
        "medium": (0.21, 0.36),
        "hard": (0.27, 0.43),
    }
    density_lo, density_hi = density_ranges[difficulty]
    min_distance = {None: 4, "easy": 3, "medium": 4, "hard": 5}[difficulty]
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    n_total = h * w

    for _attempt in range(128):
        density = rng.uniform(density_lo, density_hi)
        n_walls = max(3, min(n_total - 8, round(n_total * density)))
        order = list(all_cells)
        rng.shuffle(order)
        walls = set(order[:n_walls])
        grid = full_grid(h, w, 0)
        for r, c in walls:
            grid[r][c] = 5
        if not _all_free_connected(grid):
            continue

        free = [cell for cell in all_cells if cell not in walls]
        pairs = list(combinations(free, 2))
        rng.shuffle(pairs)
        candidates = []
        for start, goal in pairs:
            # combinations over row-major free cells exactly mirrors find-color
            # endpoint ordering after the chosen color is painted.
            info = _candidate_info(grid, start, goal, profile)
            if info is None or info["distance"] < min_distance:
                continue
            candidates.append(info)
            if len(candidates) >= 24:
                break
        if not candidates:
            continue

        chosen = _select_candidate(candidates, difficulty, rng)
        result = [row[:] for row in grid]
        for r, c in (chosen["start"], chosen["goal"]):
            result[r][c] = color
        return result

    raise ValueError(
        f"could not construct a {profile} ordered-path lesson at {h}x{w} "
        f"for difficulty {difficulty!r}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_overrides(overrides)

    band_offset = {None: 0, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    default_h, default_w = _SHAPE_SCHEDULE[
        (sample_index + band_offset) % len(_SHAPE_SCHEDULE)
    ]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_axis(ctx, overrides, "h", default_h, 4, 6)
    w = _draw_axis(ctx, overrides, "w", default_w, 5, 8)
    color = ctx.draw_choice("color", _ENDPOINT_COLORS)
    profile = schedule_profile(seed, sample_index, difficulty)
    grid = _build_grid(h, w, color, profile, difficulty, ctx.draw_rng("maze"))

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid ordered-path lesson: " + "; ".join(errors))
    analysis = _analyze(grid)
    if profile == "tied" and int(analysis["shortest_path_count"]) < 2:
        raise AssertionError("scheduled tied route was not tied")
    if profile == "unique" and analysis["shortest_path_count"] != 1:
        raise AssertionError("scheduled unique route was not unique")

    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise AssertionError(
                f"axis {axis!r} requested {value!r} but grid observes {observed.get(axis)!r}"
            )
    return grid


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected Racket authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(int(analysis["h"]), int(analysis["w"]), 0)
    color = int(analysis["color"])
    for r, c in analysis["path"]:
        out[r][c] = color
    return out


def _paint_all_shortest_cells(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid] if isinstance(grid, list) else []
    out = full_grid(int(analysis["h"]), int(analysis["w"]), 0)
    color = int(analysis["color"])
    for r, c in analysis["shortest_cells"]:
        out[r][c] = color
    return out


def _alternate_bfs_order(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid] if isinstance(grid, list) else []
    out = full_grid(int(analysis["h"]), int(analysis["w"]), 0)
    color = int(analysis["color"])
    path = _ordered_path(
        grid,
        analysis["start"],
        analysis["goal"],
        {0, color},
        _ALT_DIRS,
    )
    for r, c in path:
        out[r][c] = color
    return out


def _ignore_walls_row_first(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid] if isinstance(grid, list) else []
    out = full_grid(int(analysis["h"]), int(analysis["w"]), 0)
    color = int(analysis["color"])
    for r, c in _row_first_cells(analysis["start"], analysis["goal"]):
        out[r][c] = color
    return out


def _paint_all_open_cells(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid] if isinstance(grid, list) else []
    color = int(analysis["color"])
    return [
        [color if value in (0, color) else 0 for value in row]
        for row in grid
    ]


def _preserve_input(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid] if isinstance(grid, list) else []
    out = [row[:] for row in grid]
    color = int(analysis["color"])
    for r, c in analysis["path"]:
        out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "alternate_bfs_order": _alternate_bfs_order,
    "paint_all_shortest_cells": _paint_all_shortest_cells,
    "ignore_walls_row_first": _ignore_walls_row_first,
    "paint_all_open_cells": _paint_all_open_cells,
    "preserve_input": _preserve_input,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only include shortcuts that genuinely reproduce every canonical pair.
CANONICAL_SHORTCUTS = {
    "alternate_bfs_order": _alternate_bfs_order,
}


def _witness(grid, predicate) -> bool:
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(predicate(observables))


SEMANTIC_WITNESSES = {
    "tied_shortest_paths": lambda grid: _witness(
        grid, lambda obs: obs["tied_shortest_paths"]
    ),
    "unique_shortest_path": lambda grid: _witness(
        grid, lambda obs: obs["unique_shortest_path"]
    ),
    "ordered_tie_break": lambda grid: (
        not self_check(grid)
        and int(_analyze(grid)["shortest_path_count"]) >= 2
        and _alternate_bfs_order(grid) != rule_mirror(grid)
    ),
    "off_path_background": lambda grid: _witness(
        grid, lambda obs: int(obs["off_path_zero_count"]) >= 2
    ),
    "gray_walls_cleared": lambda grid: _witness(
        grid, lambda obs: int(obs["wall_count"]) >= 3
    ),
}

WITNESS_RIVALS = {
    "tied_shortest_paths": ["alternate_bfs_order", "paint_all_shortest_cells"],
    "unique_shortest_path": ["paint_all_open_cells", "preserve_input"],
    "ordered_tie_break": ["alternate_bfs_order"],
    "off_path_background": ["paint_all_open_cells"],
    "gray_walls_cleared": ["preserve_input"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared rival that the demonstrations leave live."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is unlawful: " + "; ".join(query_errors)]
    try:
        query_truth = rule_mirror(query_input)
    except ValueError as exc:  # defensive; self_check already ran
        return [f"query rule mirror failed: {exc}"]

    if not isinstance(demos, list):
        return ["demos must be a list"]
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} is unlawful: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo_input)
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the ordered BFS rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query"
                )
    return reasons
