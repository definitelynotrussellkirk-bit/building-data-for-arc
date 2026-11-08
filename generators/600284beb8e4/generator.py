"""Generator for 600284beb8e4 — overlap of two rectangular borders.

The input contains one color-2 border and one color-3 border.  The canonical
rule fills the intersection of their bounding rectangles with color 8.

The original implementation fixed color 2 north/west of color 3.  This repair
constructively covers both color orders plus crossed wide/tall roles, so a
positional shortcut cannot replace bounding-box intersection.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "600284beb8e4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "0460c3a13fef"
SUMMARY = "Color-2 and color-3 border rectangles define an overlap mask."

RELATIVE_POSITIONS = (
    "2_north",
    "2_south",
    "2_west",
    "2_east",
    "2_horizontal",
    "2_vertical",
)
EDGE_MODES = ("interior", "boundary")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "8..18"},
    "relative_position": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(RELATIVE_POSITIONS),
    },
    "edge_mode": {"type": "str", "default": "rng", "valid": "|".join(EDGE_MODES)},
}

INVARIANTS = [
    "one recoverable color-2 rectangular border",
    "one recoverable color-3 rectangular border",
    "the two border bounding boxes have a non-empty intersection",
    "both color-role orders and crossed wide/tall roles occur",
]

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIMENSION_BANDS = {
    None: ((8, 16), (8, 18)),
    "easy": ((8, 10), (8, 11)),
    "medium": ((10, 13), (11, 15)),
    "hard": ((14, 16), (16, 18)),
}


def _require_exact_int(name: str, value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise TypeError(f"{name} must be an exact integer >= {minimum}; bool is forbidden")
    return value


def _validate_request(seed: object, sample_index: object, difficulty: object, overrides: dict) -> None:
    _require_exact_int("seed", seed)
    _require_exact_int("sample_index", sample_index)
    if difficulty not in _ALLOWED_DIFFICULTIES or (
        difficulty is not None and type(difficulty) is not str
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an exact integer; bool is forbidden")
    for name in ("relative_position", "edge_mode"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} override must be a string")


def _draw_dimension(ctx, name: str, band: tuple[int, int], full: tuple[int, int]) -> int:
    # Exact overrides are legal across every difficulty band.  Difficulty only
    # changes the default sampling envelope.
    bounds = full if ctx.overrides.get(name) is not None else band
    return ctx.draw_int_strict(name, *bounds)


def _draw_border(
    grid: list[list[int]], top: int, left: int, bottom: int, right: int, color: int
) -> None:
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def _rectangles(
    h: int, w: int, relative_position: str, edge_mode: str
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    margin = 0 if edge_mode == "boundary" else 1
    top, left, bottom, right = margin, margin, h - 1 - margin, w - 1 - margin
    mid_r = (top + bottom) // 2
    mid_c = (left + right) // 2

    upper = (top, left, min(bottom, mid_r + 1), right)
    lower = (max(top, mid_r - 1), left, bottom, right)
    west = (top, left, bottom, min(right, mid_c + 1))
    east = (top, max(left, mid_c - 1), bottom, right)
    horizontal = (max(top, mid_r - 1), left, min(bottom, mid_r + 1), right)
    vertical = (top, max(left, mid_c - 1), bottom, min(right, mid_c + 1))

    if relative_position == "2_north":
        return upper, lower
    if relative_position == "2_south":
        return lower, upper
    if relative_position == "2_west":
        return west, east
    if relative_position == "2_east":
        return east, west
    if relative_position == "2_horizontal":
        return horizontal, vertical
    if relative_position == "2_vertical":
        return vertical, horizontal
    raise ValueError(f"unknown relative_position: {relative_position!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_band, w_band = _DIMENSION_BANDS[difficulty]
    h = _draw_dimension(ctx, "grid_h", h_band, (8, 16))
    w = _draw_dimension(ctx, "grid_w", w_band, (8, 18))
    relative_position = ctx.draw_choice("relative_position", RELATIVE_POSITIONS)
    edge_mode = ctx.draw_choice("edge_mode", EDGE_MODES)

    rect2, rect3 = _rectangles(h, w, relative_position, edge_mode)
    grid = full_grid(h, w, 0)
    _draw_border(grid, *rect2, 2)
    _draw_border(grid, *rect3, 3)
    problems = self_check(grid)
    if problems:  # Construction bugs must fail loudly instead of leaking data.
        raise AssertionError("constructed invalid overlap scene: " + "; ".join(problems))
    return grid


def _shape(grid: object) -> tuple[int, int] | None:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return None
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return None
    return len(grid), width


def _cells(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = _cells(grid, color)
    if not cells:
        raise ValueError(f"missing color {color}")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    shape = _shape(grid)
    if shape is None:
        return ["grid must be a nonempty rectangular list of lists"]
    h, w = shape
    errors: list[str] = []
    if not (1 <= h <= 30 and 1 <= w <= 30):
        errors.append("grid dimensions must be in 1..30")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an exact integer color 0..9")
                return errors
            if value not in (0, 2, 3):
                errors.append(f"unexpected color {value}; canonical inputs use only 0,2,3")
                return errors

    boxes: dict[int, tuple[int, int, int, int]] = {}
    for color in (2, 3):
        try:
            box = _bbox(grid, color)
        except ValueError:
            errors.append(f"missing color-{color} border")
            continue
        boxes[color] = box
        top, left, bottom, right = box
        if bottom - top < 2 or right - left < 2:
            errors.append(f"color-{color} border must span at least 3x3")
            continue
        perimeter = _perimeter(box)
        own = set(_cells(grid, color))
        if not own <= perimeter:
            errors.append(f"color-{color} occurs inside its recovered rectangle")
        missing = [(r, c) for r, c in perimeter if grid[r][c] == 0]
        if missing:
            errors.append(f"color-{color} recovered perimeter has {len(missing)} zero gap(s)")

    if set(boxes) == {2, 3}:
        a, b = boxes[2], boxes[3]
        r0, c0 = max(a[0], b[0]), max(a[1], b[1])
        r1, c1 = min(a[2], b[2]), min(a[3], b[3])
        if r0 > r1 or c0 > c1:
            errors.append("the two recovered bounding rectangles are disjoint")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    shape = _shape(grid)
    if shape is None:
        raise ValueError("grid must be rectangular")
    h, w = shape
    b2, b3 = _bbox(grid, 2), _bbox(grid, 3)
    r0, c0 = max(b2[0], b3[0]), max(b2[1], b3[1])
    r1, c1 = min(b2[2], b3[2]), min(b2[3], b3[3])
    output = full_grid(h, w, 0)
    if r0 <= r1 and c0 <= c1:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = 8
    return output


def north_south_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """The retained audit rival: assume 2 is north and 3 is south."""
    h, w = len(grid), len(grid[0])
    b2, b3 = _bbox(grid, 2), _bbox(grid, 3)
    r0, r1 = b3[0], b2[2]
    c0, c1 = max(b2[1], b3[1]), min(b2[3], b3[3])
    output = full_grid(h, w, 0)
    if r0 <= r1 and c0 <= c1:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = 8
    return output


def observe_controls(grid: list[list[int]]) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid scene: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    b2, b3 = _bbox(grid, 2), _bbox(grid, 3)
    h2, w2 = b2[2] - b2[0] + 1, b2[3] - b2[1] + 1
    h3, w3 = b3[2] - b3[0] + 1, b3[3] - b3[1] + 1
    if h2 < h3 and w2 > w3:
        relation = "2_horizontal"
    elif h2 > h3 and w2 < w3:
        relation = "2_vertical"
    elif b2[0] < b3[0] and b2[2] < b3[2]:
        relation = "2_north"
    elif b2[0] > b3[0] and b2[2] > b3[2]:
        relation = "2_south"
    elif b2[1] < b3[1] and b2[3] < b3[3]:
        relation = "2_west"
    elif b2[1] > b3[1] and b2[3] > b3[3]:
        relation = "2_east"
    else:
        raise ValueError(f"unrecognized rectangle relation: {b2!r} versus {b3!r}")
    boundary = any(
        box[0] == 0 or box[1] == 0 or box[2] == h - 1 or box[3] == w - 1
        for box in (b2, b3)
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "relative_position": relation,
        "edge_mode": "boundary" if boundary else "interior",
    }
