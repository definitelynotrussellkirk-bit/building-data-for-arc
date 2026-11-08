"""Semantic generator for 3b75d3395ebb — flood isolated framed rooms.

Color 5 draws two or three hollow rectangular rooms on a zero background.
Every visible room contains exactly one distinct non-{0,5} seed.  The selected
Racket rule treats the color-5 connected components as objects: a component is
flooded only when that entire component is exactly one rectangle perimeter.
Consequently isolated rooms fill, while rooms whose walls touch another room
belong to a larger non-rectangular wall object and stay unchanged.

The default four-step curriculum cycles isolated, mixed, isolated, connected.
With EXAMPLES_NEEDED=2, every sliding lesson contains evidence both for a real
flood and for the connected-wall exception, while an isolated-only example in
every window also refutes the "fill only the first isolated room" shortcut.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3b75d3395ebb"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5907a72891fa"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 2
# The true rule has a decisive lawful no-op branch when room walls touch.
ALLOW_IDENTITY_OUTPUT = True

SUMMARY = (
    "Two or three hollow color-5 rectangular rooms each contain one distinct "
    "colored seed. Flood a room interior with its seed only when that room's "
    "wall is an isolated color-5 connected component; touching rooms remain "
    "unchanged because their merged wall component is not one rectangle."
)

INVARIANTS = [
    "the grid is rectangular, uses ARC colors 0..9, and has background 0",
    "there are exactly two or three visible color-5 rectangular rooms",
    "every room has one distinct non-{0,5} seed and no color-5 interior cells",
    "every color-5 cell belongs to at least one visible room perimeter",
    "isolated wall components are exact rectangle perimeters and flood",
    "edge-touching room walls merge into a non-rectangular component and do not flood",
]

SCENE_PROFILES = ("isolated_only", "connected_only", "mixed")
_PROFILE_SCHEDULE = ("isolated_only", "mixed", "isolated_only", "connected_only")
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile prior with difficulty-aware expansion",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile prior with difficulty-aware expansion",
        "valid": "11..16",
    },
    "scene_profile": {
        "type": "str",
        "default": "isolated/mixed/isolated/connected sliding schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_WALL = 5
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SIGNATURES = {
    (10, 12, 4),
    (11, 11, 4),
    (12, 12, 5),
    (11, 13, 5),
}

Rect = tuple[int, int, int, int]
Cell = tuple[int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic curriculum branch for one ordinary draw."""
    del seed
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return _PROFILE_SCHEDULE[
        (int(sample_index) + _BAND_OFFSET[difficulty]) % len(_PROFILE_SCHEDULE)
    ]


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, lower, upper in (("grid_h", 10, 14), ("grid_w", 11, 16)):
        value = overrides.get(name)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper
        ):
            raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"scene_profile must be one of {', '.join(SCENE_PROFILES)}")


def _perimeter(rect: Rect) -> frozenset[Cell]:
    r1, c1, r2, c2 = rect
    return frozenset(
        [(r1, col) for col in range(c1, c2 + 1)]
        + [(r2, col) for col in range(c1, c2 + 1)]
        + [(row, c1) for row in range(r1 + 1, r2)]
        + [(row, c2) for row in range(r1 + 1, r2)]
    )


def _interior(rect: Rect) -> tuple[Cell, ...]:
    r1, c1, r2, c2 = rect
    return tuple(
        (row, col)
        for row in range(r1 + 1, r2)
        for col in range(c1 + 1, c2)
    )


def _rect_sort_key(rect: Rect) -> tuple[int, int, int, int]:
    return rect


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _wall_components(grid: list[list[int]]) -> list[frozenset[Cell]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == _WALL
    }
    components: list[frozenset[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(frozenset(component))
    return sorted(components, key=lambda cells: min(cells))


def _component_rect(component: frozenset[Cell]) -> Rect | None:
    if not component:
        return None
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    rect = min(rows), min(cols), max(rows), max(cols)
    r1, c1, r2, c2 = rect
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    return rect if component == _perimeter(rect) else None


def _find_visual_rooms(grid: list[list[int]]) -> list[Rect]:
    """Enumerate full color-5 rectangle perimeters with exactly one seed."""
    height, width = len(grid), len(grid[0])
    rooms: list[Rect] = []
    for r1 in range(height - 2):
        for r2 in range(r1 + 2, height):
            for c1 in range(width - 2):
                for c2 in range(c1 + 2, width):
                    rect = (r1, c1, r2, c2)
                    if any(grid[row][col] != _WALL for row, col in _perimeter(rect)):
                        continue
                    inside = _interior(rect)
                    if any(grid[row][col] == _WALL for row, col in inside):
                        continue
                    seeds = [
                        (row, col)
                        for row, col in inside
                        if grid[row][col] not in (0, _WALL)
                    ]
                    if len(seeds) == 1:
                        rooms.append(rect)
    return sorted(set(rooms), key=_rect_sort_key)


def _profile_from_counts(room_count: int, eligible_count: int) -> str | None:
    if room_count <= 0:
        return None
    if eligible_count == room_count:
        return "isolated_only"
    if eligible_count == 0:
        return "connected_only"
    return "mixed"


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append(f"grid dimensions must be 8..30, found {height}x{width}")

    rooms = _find_visual_rooms(normalized)
    if not 2 <= len(rooms) <= 3:
        errors.append(f"expected 2 or 3 visible seeded rooms, found {len(rooms)}")

    seeds = [
        (row, col, normalized[row][col])
        for row in range(height)
        for col in range(width)
        if normalized[row][col] not in (0, _WALL)
    ]
    if len(seeds) != len(rooms):
        errors.append(f"expected one seed per room, found {len(seeds)} seeds for {len(rooms)} rooms")
    seed_colors = [color for _, _, color in seeds]
    if len(seed_colors) != len(set(seed_colors)):
        errors.append("room seed colors must be distinct")

    for row, col, _color in seeds:
        memberships = [rect for rect in rooms if (row, col) in _interior(rect)]
        if len(memberships) != 1:
            errors.append(f"seed at {(row, col)} belongs to {len(memberships)} visible rooms")

    room_walls = set().union(*(_perimeter(rect) for rect in rooms)) if rooms else set()
    wall_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == _WALL
    }
    stray_walls = wall_cells - room_walls
    if stray_walls:
        errors.append(f"{len(stray_walls)} color-5 cells do not belong to a room perimeter")

    components = _wall_components(normalized)
    component_rects = [rect for component in components if (rect := _component_rect(component))]
    eligible_rooms = sorted(set(component_rects) & set(rooms), key=_rect_sort_key)
    profile = _profile_from_counts(len(rooms), len(eligible_rooms))
    output = rule_mirror(normalized)
    changed_cells = sum(
        normalized[row][col] != output[row][col]
        for row in range(height)
        for col in range(width)
    )
    palette = sorted({value for row in normalized for value in row})
    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": height,
        "grid_w": width,
        "rooms": rooms,
        "room_count": len(rooms),
        "seeds": seeds,
        "seed_colors": seed_colors,
        "wall_components": components,
        "wall_component_count": len(components),
        "eligible_rooms": eligible_rooms,
        "eligible_count": len(eligible_rooms),
        "connected_room_count": max(0, len(rooms) - len(eligible_rooms)),
        "scene_profile": profile,
        "changed_cells": changed_cells,
        "palette": palette,
        "palette_size": len(palette),
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected connected-component Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    source = [list(row) for row in grid]
    output = deepcopy(source)
    for component in _wall_components(source):
        rect = _component_rect(component)
        if rect is None:
            continue
        seeds = [
            (row, col)
            for row, col in _interior(rect)
            if source[row][col] not in (0, _WALL)
        ]
        if len(seeds) != 1:
            continue
        seed_row, seed_col = seeds[0]
        color = source[seed_row][seed_col]
        for row, col in _interior(rect):
            output[row][col] = color
    return output


def _fill_all_visual_frames(grid: Any) -> list[list[int]]:
    """Plausible rival: flood every visible rectangle, ignoring wall objects."""
    source = [list(row) for row in grid]
    output = deepcopy(source)
    for rect in _find_visual_rooms(source):
        seed = next(
            (row, col)
            for row, col in _interior(rect)
            if source[row][col] not in (0, _WALL)
        )
        color = source[seed[0]][seed[1]]
        for row, col in _interior(rect):
            output[row][col] = color
    return output


def _identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _fill_only_first_isolated(grid: Any) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = deepcopy(source)
    eligible = set(_analyze(source).get("eligible_rooms", []))
    for rect in _find_visual_rooms(source):
        if rect not in eligible:
            continue
        seed = next(
            (row, col)
            for row, col in _interior(rect)
            if source[row][col] not in (0, _WALL)
        )
        color = source[seed[0]][seed[1]]
        for row, col in _interior(rect):
            output[row][col] = color
        break
    return output


SEMANTIC_RIVALS = {
    "identity": _identity,
    "fill_every_visible_frame": _fill_all_visual_frames,
    "fill_only_first_isolated": _fill_only_first_isolated,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical inputs and the generated room/wall grammar."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["scene_profile"] is None:
        errors.append("could not classify isolated versus connected room walls")
    if isinstance(meta, dict):
        requested: dict[str, Any] = {}
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
        if requested:
            observed = observe_overrides(grid)
            for axis, expected in requested.items():
                if axis in AXES and expected is not None and observed[axis] != expected:
                    errors.append(
                        f"override {axis} requested {expected!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked canonical height/width/palette profiles."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    signature = (analysis["grid_h"], analysis["grid_w"], analysis["palette_size"])
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked (height,width,palette) profile {signature} is not canonical"]
    return []


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "scene_profile": analysis["scene_profile"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe invalid scene")
    return {
        **observe_overrides(grid),
        "room_count": analysis["room_count"],
        "eligible_count": analysis["eligible_count"],
        "connected_room_count": analysis["connected_room_count"],
        "wall_component_count": analysis["wall_component_count"],
        "changed_cells": analysis["changed_cells"],
        "palette_size": analysis["palette_size"],
    }


def _witness(predicate):
    def wrapped(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis.get("errors") and bool(predicate(analysis, grid))

    return wrapped


SEMANTIC_WITNESSES = {
    "isolated_room_floods": _witness(
        lambda analysis, grid: analysis["eligible_count"] >= 1 and rule_mirror(grid) != _identity(grid)
    ),
    "connected_rooms_stay_unfilled": _witness(
        lambda analysis, grid: analysis["connected_room_count"] >= 1
        and rule_mirror(grid) != _fill_all_visual_frames(grid)
    ),
    "mixed_change_and_no_change": _witness(
        lambda analysis, _grid: analysis["scene_profile"] == "mixed"
        and analysis["eligible_count"] >= 1
        and analysis["connected_room_count"] >= 1
    ),
    "multiple_isolated_rooms": _witness(
        lambda analysis, _grid: analysis["eligible_count"] >= 2
    ),
}

WITNESS_RIVALS = {
    "isolated_room_floods": ["identity"],
    "connected_rooms_stay_unfilled": ["fill_every_visible_frame"],
    "mixed_change_and_no_change": ["identity", "fill_every_visible_frame"],
    "multiple_isolated_rooms": ["fill_only_first_isolated"],
}


def _draw_axis_int(ctx, label: str, lo: int, hi: int, default: tuple[int, int] | int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    if isinstance(default, int):
        return ctx.draw_int(label, default, default)
    return ctx.draw_int_diff(label, default[0], default[1])


def _draw_axis_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _default_size(profile: str, difficulty, seed: int, sample_index: int) -> tuple[int | tuple[int, int], int | tuple[int, int]]:
    """Return exact canonical anchors most draws, broader ranges every fifth draw."""
    anchor = int(sample_index) % 5 != 4
    if anchor:
        choices = (
            ((10, 12), (11, 11))
            if profile != "mixed"
            else ((12, 12), (11, 13))
        )
        pair = choices[(int(seed) + int(sample_index) + _BAND_OFFSET[difficulty]) % len(choices)]
        return pair[0], pair[1]
    if difficulty == "easy":
        return (10, 11), (11, 13)
    if difficulty == "hard":
        return (12, 14), (13, 16)
    return (10, 13), (11, 15)


def _rect_compatible(first: Rect, second: Rect) -> bool:
    p_first, p_second = _perimeter(first), _perimeter(second)
    i_first, i_second = set(_interior(first)), set(_interior(second))
    return not (
        p_first & p_second
        or i_first & i_second
        or p_first & i_second
        or p_second & i_first
    )


def _perimeters_edge_touch(first: Rect, second: Rect) -> bool:
    second_cells = _perimeter(second)
    return any(
        (row + dr, col + dc) in second_cells
        for row, col in _perimeter(first)
        for dr, dc in _CARDINAL
    )


def _perimeters_separated(rect: Rect, others: Iterable[Rect]) -> bool:
    cells = _perimeter(rect)
    other_cells = set().union(*(_perimeter(other) for other in others))
    if not other_cells:
        return True
    return all(
        abs(row - orow) + abs(col - ocol) > 1
        for row, col in cells
        for orow, ocol in other_cells
    )


def _random_rect(rng, height: int, width: int) -> Rect:
    rect_h = rng.randint(4, min(6, height))
    rect_w = rng.randint(4, min(6, width))
    r1 = rng.randint(0, height - rect_h)
    c1 = rng.randint(0, width - rect_w)
    return r1, c1, r1 + rect_h - 1, c1 + rect_w - 1


def _connected_pair(rng, height: int, width: int) -> tuple[Rect, Rect]:
    for _ in range(512):
        h1 = rng.randint(4, min(6, height))
        w1 = rng.randint(4, min(6, width))
        h2 = rng.randint(4, min(6, height))
        w2 = rng.randint(4, min(6, width))
        side = rng.choice(("right", "left", "down", "up"))
        if side in ("right", "left"):
            if w1 + w2 > width:
                continue
            c1 = rng.randint(0, width - w1 - w2)
            if side == "right":
                ca, cb = c1, c1 + w1
            else:
                cb, ca = c1, c1 + w2
            ra = rng.randint(0, height - h1)
            low = max(0, ra - h2 + 2)
            high = min(height - h2, ra + h1 - 2)
            if low > high:
                continue
            rb = rng.randint(low, high)
            first = (ra, ca, ra + h1 - 1, ca + w1 - 1)
            second = (rb, cb, rb + h2 - 1, cb + w2 - 1)
        else:
            if h1 + h2 > height:
                continue
            r1 = rng.randint(0, height - h1 - h2)
            if side == "down":
                ra, rb = r1, r1 + h1
            else:
                rb, ra = r1, r1 + h2
            ca = rng.randint(0, width - w1)
            low = max(0, ca - w2 + 2)
            high = min(width - w2, ca + w1 - 2)
            if low > high:
                continue
            cb = rng.randint(low, high)
            first = (ra, ca, ra + h1 - 1, ca + w1 - 1)
            second = (rb, cb, rb + h2 - 1, cb + w2 - 1)
        if _rect_compatible(first, second) and _perimeters_edge_touch(first, second):
            return first, second
    # Fits every declared 10x11-or-larger canvas.
    return (0, 0, 4, 4), (5, 1, 9, 4)


def _isolated_pair(rng, height: int, width: int) -> tuple[Rect, Rect]:
    for _ in range(512):
        first = _random_rect(rng, height, width)
        second = _random_rect(rng, height, width)
        if _rect_compatible(first, second) and _perimeters_separated(second, (first,)):
            return first, second
    return (0, 0, 3, 3), (0, width - 4, 3, width - 1)


def _mixed_triple(rng, height: int, width: int) -> tuple[Rect, Rect, Rect]:
    for _ in range(256):
        first, second = _connected_pair(rng, height, width)
        for _ in range(256):
            third = _random_rect(rng, height, width)
            if (
                _rect_compatible(third, first)
                and _rect_compatible(third, second)
                and _perimeters_separated(third, (first, second))
            ):
                return first, second, third
    return (0, 0, 4, 4), (5, 1, 9, 4), (1, width - 4, 4, width - 1)


def _draw_scene(rects: tuple[Rect, ...], height: int, width: int, rng) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for rect in rects:
        for row, col in _perimeter(rect):
            grid[row][col] = _WALL
    colors = rng.sample(_SEED_COLORS, len(rects))
    for rect, color in zip(rects, colors):
        row, col = rng.choice(_interior(rect))
        grid[row][col] = color
    return grid


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
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile = _draw_axis_choice(ctx, "scene_profile", SCENE_PROFILES, scheduled_profile)
    default_h, default_w = _default_size(profile, difficulty, seed, sample_index)
    height = _draw_axis_int(ctx, "grid_h", 10, 14, default_h)
    width = _draw_axis_int(ctx, "grid_w", 11, 16, default_w)
    rng = ctx.draw_rng("layout")

    for _ in range(128):
        if profile == "isolated_only":
            rects = _isolated_pair(rng, height, width)
        elif profile == "connected_only":
            rects = _connected_pair(rng, height, width)
        else:
            rects = _mixed_triple(rng, height, width)
        grid = _draw_scene(tuple(rects), height, width, rng)
        analysis = _analyze(grid)
        if not analysis.get("errors") and analysis["scene_profile"] == profile:
            return grid
    raise RuntimeError(
        f"could not construct {profile} scene on {height}x{width} after 128 attempts"
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named plausible rival survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstration pairs"]
    reasons: list[str] = []
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
        profiles.add(observe_overrides(pair["input"])["scene_profile"])

    if not ({"isolated_only", "mixed"} & profiles):
        reasons.append("demonstrations contain no positive flood witness")
    if not ({"connected_only", "mixed"} & profiles):
        reasons.append("demonstrations contain no connected-wall no-fill witness")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is invalid: " + "; ".join(query_errors))
        return reasons
    query_expected = rule_mirror(query["input"])
    if query["output"] != query_expected:
        reasons.append("query output disagrees with the selected rule")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query_expected:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Near-miss scenes that the structural checker must reject."""
    base = generate(
        39173,
        1,
        difficulty="medium",
        grid_h=11,
        grid_w=13,
        scene_profile="mixed",
    )
    analysis = _analyze(base)
    rooms = analysis["rooms"]
    seeds = analysis["seeds"]

    broken_wall = deepcopy(base)
    wall_row, wall_col = next(iter(_perimeter(rooms[0])))
    broken_wall[wall_row][wall_col] = 0

    missing_seed = deepcopy(base)
    seed_row, seed_col, _ = seeds[0]
    missing_seed[seed_row][seed_col] = 0

    duplicate_seed = deepcopy(base)
    open_cell = next(
        (row, col)
        for row, col in _interior(rooms[0])
        if duplicate_seed[row][col] == 0
    )
    duplicate_seed[open_cell[0]][open_cell[1]] = next(
        color for color in _SEED_COLORS if color not in analysis["seed_colors"]
    )

    stray_seed = deepcopy(base)
    outside = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base[0]))
        if base[row][col] == 0
        and all((row, col) not in _interior(rect) for rect in rooms)
    )
    stray_seed[outside[0]][outside[1]] = next(
        color for color in _SEED_COLORS if color not in analysis["seed_colors"]
    )

    stray_wall = deepcopy(base)
    stray_wall[outside[0]][outside[1]] = _WALL

    return [
        ("broken_rectangle_perimeter", broken_wall),
        ("room_missing_seed", missing_seed),
        ("room_with_two_seeds", duplicate_seed),
        ("seed_outside_every_room", stray_seed),
        ("wall_cell_outside_every_perimeter", stray_wall),
    ]
