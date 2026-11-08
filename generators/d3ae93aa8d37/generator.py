"""Generator for arc_additional_puzzle_bank_volume10:M70.

Rule: keep gray (5) walls and red/green endpoints unchanged, then paint the
interior of the canonical shortest orthogonal path cyan (8).

A four-profile schedule makes the lesson contract constructive rather than
probabilistic: every consecutive four generated examples contains horizontal
and vertical wall-forced detours, an unobstructed offset path, and a denser
reachable scene.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d3ae93aa8d37"
VERSION = "2.0.0"
TASK_ID = "d3ae93aa8d37"
SUMMARY = (
    "Exactly one red start and one green goal lie on a 6-30 square/rectangular "
    "zero canvas with optional gray walls. The canonical BFS paints only the "
    "interior of a shortest wall-avoiding orthogonal path cyan. Four scheduled "
    "profiles guarantee obstacle-relevant teaching support in every lesson."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and input colors are limited to 0, 2, 3, and 5",
    "there is exactly one red start and one green goal",
    "the endpoints are at Manhattan distance at least 3",
    "the endpoints remain reachable through non-wall cells",
    "every consecutive four default samples contain a wall-forced detour",
]

PALETTE_KINDS = ("default", "sparse_walls", "medium_walls", "dense_walls")
DEGENERATE_TEXTURES = ("no_red", "no_green", "blocked_path")
HELPFUL_TEXTURES = PALETTE_KINDS
SCENE_PROFILES = ("scheduled", "open_path", "forced_detour", "dense_maze")
POSITION_BIASES = ("scheduled", "varied", "horizontal", "vertical", "offset", "row_aligned")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "6..30"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful wall-density band",
        "valid": "|".join(PALETTE_KINDS),
    },
    "n_walls": {"type": "int", "default": "profile-aware rng", "valid": "0..200"},
    "palette_size": {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias": {
        "type": "str",
        "default": "scheduled horizontal|offset|vertical|offset",
        "valid": "|".join(POSITION_BIASES),
    },
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "distance": {"type": "int", "default": "difficulty-aware Manhattan distance", "valid": "3..58"},
    "scene_profile": {
        "type": "str",
        "default": "scheduled forced|open|forced|dense",
        "valid": "|".join(SCENE_PROFILES),
    },
    "texture": {
        "type": "str",
        "default": "optional alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILE_SCHEDULE = ("forced_detour", "open_path", "forced_detour", "dense_maze")
_GEOMETRY_SCHEDULE = ("horizontal", "offset", "vertical", "offset")


def _validate_difficulty(difficulty: Any) -> str | None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    return difficulty


def _draw_axis_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    *,
    default_lo: int,
    default_hi: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _shortest_path(
    grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]
) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            path: list[tuple[int, int]] = []
            while current is not None:
                path.append(current)
                current = parents[current]
            return list(reversed(path))
        row, column = current
        for dr, dc in _DIRECTIONS:
            neighbor = (row + dr, column + dc)
            nr, nc = neighbor
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and neighbor not in parents
            ):
                parents[neighbor] = current
                queue.append(neighbor)
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    if not grid[0]:
        return ["empty grid"]
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]

    errors: list[str] = []
    if not (6 <= height <= 30 and 6 <= width <= 30):
        errors.append(f"grid dimensions must each be in 6..30; found {height}x{width}")

    invalid = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if type(value) is not int or value not in (0, 2, 3, 5)
    ]
    if invalid:
        errors.append("input cells must be literal integers from {0,2,3,5}")
        return errors

    reds = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 2
    ]
    greens = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 3
    ]
    if len(reds) != 1 or len(greens) != 1:
        errors.append(
            f"expected one red and one green endpoint, found {len(reds)}, {len(greens)}"
        )
        return errors

    start, goal = reds[0], greens[0]
    distance = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    if distance < 3:
        errors.append(f"endpoint Manhattan distance must be at least 3; found {distance}")
    if not _shortest_path([list(row) for row in grid], start, goal):
        errors.append("start and goal are not connected through non-wall cells")
    return errors


def _endpoint_candidates(
    height: int,
    width: int,
    distance: int,
    geometry: str,
    *,
    needs_detour_margin: bool,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    if geometry == "horizontal":
        if distance >= width:
            return []
        rows = range(1, height - 1) if needs_detour_margin else range(height)
        for row in rows:
            for left in range(width - distance):
                a, b = (row, left), (row, left + distance)
                candidates.extend(((a, b), (b, a)))
    elif geometry == "vertical":
        if distance >= height:
            return []
        columns = range(1, width - 1) if needs_detour_margin else range(width)
        for column in columns:
            for top in range(height - distance):
                a, b = (top, column), (top + distance, column)
                candidates.extend(((a, b), (b, a)))
    elif geometry == "offset":
        for row_delta in range(1, min(height, distance)):
            column_delta = distance - row_delta
            if not (1 <= column_delta < width):
                continue
            for top in range(height - row_delta):
                for left in range(width - column_delta):
                    nw, se = (top, left), (top + row_delta, left + column_delta)
                    ne, sw = (top, left + column_delta), (top + row_delta, left)
                    candidates.extend(((nw, se), (se, nw), (ne, sw), (sw, ne)))
    else:
        raise ValueError(f"unsupported endpoint geometry: {geometry}")
    return candidates


def _inclusive_axis(a: int, b: int) -> list[int]:
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def _manhattan_path(
    start: tuple[int, int], goal: tuple[int, int], *, horizontal_first: bool
) -> list[tuple[int, int]]:
    sr, sc = start
    gr, gc = goal
    path = [start]
    if horizontal_first:
        path.extend((sr, column) for column in _inclusive_axis(sc, gc)[1:])
        path.extend((row, gc) for row in _inclusive_axis(sr, gr)[1:])
    else:
        path.extend((row, sc) for row in _inclusive_axis(sr, gr)[1:])
        path.extend((gr, column) for column in _inclusive_axis(sc, gc)[1:])
    return path


def _forced_detour_path(
    start: tuple[int, int], goal: tuple[int, int], rng
) -> tuple[list[tuple[int, int]], tuple[int, int]]:
    sr, sc = start
    gr, gc = goal
    if sr == gr:
        detour_row = sr + rng.choice((-1, 1))
        path = [(sr, sc), (detour_row, sc)]
        path.extend((detour_row, column) for column in _inclusive_axis(sc, gc)[1:])
        path.append((gr, gc))
        direct_columns = _inclusive_axis(sc, gc)[1:-1]
        wall = (sr, direct_columns[len(direct_columns) // 2])
        return path, wall
    if sc == gc:
        detour_column = sc + rng.choice((-1, 1))
        path = [(sr, sc), (sr, detour_column)]
        path.extend((row, detour_column) for row in _inclusive_axis(sr, gr)[1:])
        path.append((gr, gc))
        direct_rows = _inclusive_axis(sr, gr)[1:-1]
        wall = (direct_rows[len(direct_rows) // 2], sc)
        return path, wall
    raise ValueError("forced_detour requires horizontal or vertical endpoints")


def _default_wall_band(
    profile: str,
    palette_kind: str,
    difficulty: str | None,
    area: int,
    available: int,
) -> tuple[int, int]:
    if profile == "open_path":
        lo, hi = 0, min(2, available)
    elif profile == "forced_detour":
        base_hi = 2 if difficulty == "easy" else 5 if difficulty != "hard" else 8
        lo, hi = 1, min(base_hi, available)
    else:
        lo = min(available, max(6, area // 10))
        hi = min(available, max(lo, area // 5))

    if palette_kind == "sparse_walls":
        hi = max(lo, min(hi, lo + 2))
    elif palette_kind == "medium_walls":
        lo = min(hi, max(lo, (lo + hi) // 2))
    elif palette_kind == "dense_walls" and profile != "open_path":
        lo = min(hi, max(lo, hi - max(1, (hi - lo) // 3)))
    return lo, hi


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    difficulty = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        dimension_band = (6, 9)
        distance_band = (3, 5)
    elif difficulty == "hard":
        dimension_band = (14, 24)
        distance_band = (7, 14)
    else:
        dimension_band = (8, 15)
        distance_band = (4, 9)

    height = _draw_axis_int(
        ctx,
        overrides,
        "grid_h",
        default_lo=dimension_band[0],
        default_hi=dimension_band[1],
        lo=6,
        hi=30,
    )
    width = _draw_axis_int(
        ctx,
        overrides,
        "grid_w",
        default_lo=dimension_band[0],
        default_hi=dimension_band[1],
        lo=6,
        hi=30,
    )

    ctx.draw_int_strict("palette_size", 3, 3)
    ctx.draw_int_strict("n_distinct_colors", 3, 3)

    texture = None
    if "texture" in overrides and overrides["texture"] is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    if texture in HELPFUL_TEXTURES:
        if (
            "palette_kind" in overrides
            and overrides["palette_kind"] is not None
            and overrides["palette_kind"] != texture
        ):
            raise ValueError(
                f"texture={texture!r} conflicts with palette_kind={overrides['palette_kind']!r}"
            )
        palette_kind = ctx.draw_choice("palette_kind", (texture,))
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    scheduled_profile = _PROFILE_SCHEDULE[int(sample_index) % EXAMPLES_NEEDED]
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        raw_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
        profile = scheduled_profile if raw_profile == "scheduled" else raw_profile
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled_profile,))

    scheduled_geometry = _GEOMETRY_SCHEDULE[int(sample_index) % EXAMPLES_NEEDED]
    if "position_bias" in overrides and overrides["position_bias"] is not None:
        raw_geometry = ctx.draw_choice("position_bias", POSITION_BIASES)
        geometry = scheduled_geometry if raw_geometry == "scheduled" else raw_geometry
    else:
        geometry = ctx.draw_choice("position_bias", (scheduled_geometry,))
    if geometry == "row_aligned":
        geometry = "horizontal"
    layout_rng = ctx.draw_rng("layout")
    if geometry == "varied":
        geometry = layout_rng.choice(
            ("horizontal", "vertical") if profile == "forced_detour" else ("horizontal", "vertical", "offset")
        )
    if profile == "forced_detour" and geometry not in ("horizontal", "vertical"):
        raise ValueError("forced_detour requires horizontal or vertical position_bias")

    global_max_distance = height + width - 2
    if "distance" in overrides and overrides["distance"] is not None:
        distance = ctx.draw_int_strict("distance", 3, global_max_distance)
    else:
        geometry_max = (
            width - 1
            if geometry == "horizontal"
            else height - 1
            if geometry == "vertical"
            else global_max_distance
        )
        lo = min(distance_band[0], geometry_max)
        hi = min(distance_band[1], geometry_max)
        if hi < 3:
            raise ValueError("grid is too small for endpoint distance >= 3")
        lo = max(3, min(lo, hi))
        distance = ctx.draw_int_strict("distance", lo, hi)

    candidates = _endpoint_candidates(
        height,
        width,
        distance,
        geometry,
        needs_detour_margin=profile == "forced_detour",
    )
    if not candidates:
        raise ValueError(
            f"no endpoint placement for grid={height}x{width}, distance={distance}, "
            f"position_bias={geometry}, scene_profile={profile}"
        )
    start, goal = layout_rng.choice(candidates)

    if profile == "forced_detour":
        reserved_path, mandatory_wall = _forced_detour_path(start, goal, layout_rng)
        mandatory_walls = {mandatory_wall}
    else:
        reserved_path = _manhattan_path(
            start, goal, horizontal_first=bool(layout_rng.randrange(2))
        )
        mandatory_walls = set()

    reserved = set(reserved_path)
    all_cells = {
        (row, column)
        for row in range(height)
        for column in range(width)
    }
    wall_candidates = sorted(all_cells - reserved - {start, goal} - mandatory_walls)
    available = len(wall_candidates) + len(mandatory_walls)
    default_lo, default_hi = _default_wall_band(
        profile, palette_kind, difficulty, height * width, available
    )
    if "n_walls" in overrides and overrides["n_walls"] is not None:
        n_walls = ctx.draw_int_strict("n_walls", 0, 200)
    else:
        n_walls = ctx.draw_int_strict("n_walls", default_lo, default_hi)
    if n_walls < len(mandatory_walls):
        raise ValueError(
            f"scene_profile={profile} requires at least {len(mandatory_walls)} wall"
        )
    if n_walls > available:
        raise ValueError(
            f"n_walls={n_walls} exceeds {available} legal wall positions"
        )

    layout_rng.shuffle(wall_candidates)
    walls = mandatory_walls | set(
        wall_candidates[: n_walls - len(mandatory_walls)]
    )
    grid = full_grid(height, width, 0)
    for row, column in walls:
        grid[row][column] = 5
    grid[start[0]][start[1]] = 2
    grid[goal[0]][goal[1]] = 3

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, height, width)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid shortest-path scene: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name: str, height: int, width: int):
    grid = full_grid(height, width, 0)
    row = min(height - 2, max(1, height // 2))
    if name == "no_red":
        grid[row][width - 2] = 3
        return grid
    if name == "no_green":
        grid[row][1] = 2
        return grid
    if name == "blocked_path":
        grid[1][1] = 2
        grid[1][3] = 3
        for wall in ((0, 1), (2, 1), (1, 0), (1, 2)):
            grid[wall[0]][wall[1]] = 5
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
