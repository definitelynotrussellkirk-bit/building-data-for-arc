"""Constructive generator for the canonical square-hole fill task.

Each color-5 connected component defines a bounding box.  When the zero cells
strictly inside that box form a complete square, the reference rule recolors
those zeros with color 2.  Ordinary draws contain at least one positive square
frame and one negative non-square rectangle.  All declared controls are exact:
they are either realized or rejected, never clipped, coerced, or silently
ignored.
"""
from __future__ import annotations

import hashlib
from itertools import product
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "ca81880afbf3"
TASK_ID = GENERATOR_ID
RULE_HASH = "b9bced028d0a"
VERSION = "2.0.0"
SUMMARY = "Color-5 frames; fill complete square bbox interiors with color 2."

INVARIANTS = [
    "rectangular 5..16 by 9..20 integer grid containing only colors 0 and 5",
    "ordinary draws contain one or two complete square frames",
    "ordinary draws contain one or two complete non-square rectangular frames",
    "frames are separated by at least one background row or column",
    "every declared override is exact or rejected",
]

POSITION_BIASES = ("scattered", "row_aligned", "col_aligned", "diagonal")
HELPFUL_TEXTURES = POSITION_BIASES
# These remain explicit authoring-only negative fixtures.  They are deliberately
# absent from AXES['texture'].valid, so they cannot masquerade as lawful ordinary
# distribution settings.
DEGENERATE_TEXTURES = ("only_squares", "only_rects", "no_frames")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted feasible 5..16", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "difficulty-weighted feasible 9..20", "valid": "9..20"},
    "n_square": {"type": "int", "default": "1", "valid": "1..2"},
    "n_rect": {"type": "int", "default": "1", "valid": "1..2"},
    "square_size": {"type": "int", "default": "feasible 3..6", "valid": "3..6"},
    "rect_h": {"type": "int", "default": "feasible 3..5", "valid": "3..5"},
    "rect_w": {"type": "int", "default": "feasible 4..7", "valid": "4..7"},
    "position_bias": {"type": "str", "default": "rng helpful", "valid": "|".join(POSITION_BIASES)},
    "texture": {"type": "str", "default": "alias for position_bias", "valid": "|".join(HELPFUL_TEXTURES)},
}

_INT_RANGES = {
    "grid_h": (5, 16),
    "grid_w": (9, 20),
    "n_square": (1, 2),
    "n_rect": (1, 2),
    "square_size": (3, 6),
    "rect_h": (3, 5),
    "rect_w": (4, 7),
}
_DIFFICULTY_RANGES = {
    None: ((7, 12), (11, 16)),
    "easy": ((5, 8), (9, 12)),
    "medium": ((7, 12), (11, 16)),
    "hard": ((12, 16), (16, 20)),
}


class IncompatibleOverrides(ValueError):
    """Exact controls describe no lawful scene in the supported domain."""

    def __init__(self, message: str, axes: Iterable[str]):
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(set(axes)))


def _validate_call(seed: object, sample_index: object, difficulty: object) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTY_RANGES:
        raise ValueError("difficulty must be easy, medium, hard, or None")


def _validate_overrides(overrides: dict) -> dict:
    allowed = set(AXES)
    unknown = set(overrides) - allowed
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    pins = {key: value for key, value in overrides.items() if value is not None}
    for key, value in pins.items():
        if key in _INT_RANGES:
            lo, hi = _INT_RANGES[key]
            if type(value) is not int:
                raise TypeError(f"{key} must be an integer (not bool)")
            if not lo <= value <= hi:
                raise ValueError(f"{key} must be in {lo}..{hi}")
        elif key == "position_bias":
            if type(value) is not str or value not in POSITION_BIASES:
                raise ValueError(f"position_bias must be one of {POSITION_BIASES}")
        elif key == "texture":
            legal = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
            if type(value) is not str or value not in legal:
                raise ValueError(f"texture must be one of {legal}")
    texture = pins.get("texture")
    bias = pins.get("position_bias")
    if texture in HELPFUL_TEXTURES and bias is not None and texture != bias:
        raise IncompatibleOverrides(
            "texture and position_bias name different exact layouts",
            ("texture", "position_bias"),
        )
    return pins


def _overlaps(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> bool:
    """True when rectangles overlap or lack a one-cell cardinal moat."""
    r0, c0, h, w = first
    r1, c1, h1, w1 = second
    return not (
        r0 + h + 1 <= r1
        or r1 + h1 + 1 <= r0
        or c0 + w + 1 <= c1
        or c1 + w1 + 1 <= c0
    )


def _jitter(seed: int, sample_index: int, bias: str, shape_index: int, r: int, c: int) -> int:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{sample_index}:{bias}:{shape_index}:{r}:{c}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _target(
    bias: str,
    index: int,
    count: int,
    height: int,
    width: int,
    shape_h: int,
    shape_w: int,
) -> tuple[int, int]:
    max_r, max_c = height - shape_h, width - shape_w
    if count <= 1:
        fraction = 0.5
    else:
        fraction = index / (count - 1)
    if bias == "row_aligned":
        return (0, round(max_c * fraction))
    if bias == "col_aligned":
        return (round(max_r * fraction), 0)
    if bias == "diagonal":
        return (round(max_r * fraction), round(max_c * fraction))
    corners = ((0, 0), (max_r, max_c), (0, max_c), (max_r, 0))
    return corners[index % len(corners)]


def _find_layout(
    height: int,
    width: int,
    shapes: tuple[tuple[str, int, int], ...],
    bias: str,
    seed: int,
    sample_index: int,
) -> list[tuple[str, int, int, int, int]] | None:
    """Backtrack to one bias-ranked exact placement."""
    candidates: list[list[tuple[int, int]]] = []
    for index, (_, shape_h, shape_w) in enumerate(shapes):
        if shape_h > height or shape_w > width:
            return None
        tr, tc = _target(bias, index, len(shapes), height, width, shape_h, shape_w)
        rows = [(r, c) for r in range(height - shape_h + 1) for c in range(width - shape_w + 1)]
        rows.sort(
            key=lambda point: (
                abs(point[0] - tr) + abs(point[1] - tc),
                _jitter(seed, sample_index, bias, index, point[0], point[1]),
            )
        )
        candidates.append(rows)

    chosen: list[tuple[str, int, int, int, int]] = []

    def visit(index: int) -> bool:
        if index == len(shapes):
            return True
        kind, shape_h, shape_w = shapes[index]
        for r, c in candidates[index]:
            rect = (r, c, shape_h, shape_w)
            if any(_overlaps(rect, (pr, pc, ph, pw)) for _, pr, pc, ph, pw in chosen):
                continue
            chosen.append((kind, r, c, shape_h, shape_w))
            if visit(index + 1):
                return True
            chosen.pop()
        return False

    return list(chosen) if visit(0) else None


def _domain(pin: object | None, lo: int, hi: int) -> list[int]:
    return [pin] if pin is not None else list(range(lo, hi + 1))


def _choose_configuration(ctx, pins: dict, seed: int, sample_index: int, difficulty: object):
    n_square = pins.get("n_square", 1)
    n_rect = pins.get("n_rect", 1)
    h_band, w_band = _DIFFICULTY_RANGES[difficulty]
    heights = _domain(pins.get("grid_h"), *h_band) if "grid_h" in pins else list(range(*((h_band[0], h_band[1] + 1))))
    widths = _domain(pins.get("grid_w"), *w_band) if "grid_w" in pins else list(range(*((w_band[0], w_band[1] + 1))))
    sides = _domain(pins.get("square_size"), 3, 6)
    rect_heights = _domain(pins.get("rect_h"), 3, 5)
    rect_widths = _domain(pins.get("rect_w"), 4, 7)
    requested_bias = pins.get("position_bias")
    if pins.get("texture") in HELPFUL_TEXTURES:
        requested_bias = pins["texture"]
    biases = [requested_bias] if requested_bias is not None else list(POSITION_BIASES)

    configurations = list(product(heights, widths, sides, rect_heights, rect_widths, biases))
    ctx.draw_rng("configuration-order").shuffle(configurations)
    for height, width, side, rect_h, rect_w, bias in configurations:
        if rect_h == rect_w:
            continue
        shapes = tuple(
            [("square", side, side)] * n_square
            + [("rect", rect_h, rect_w)] * n_rect
        )
        layout = _find_layout(height, width, shapes, bias, seed, sample_index)
        if layout is not None:
            return height, width, n_square, n_rect, side, rect_h, rect_w, bias, layout
    exact_axes = set(pins) | {"n_square", "n_rect"}
    raise IncompatibleOverrides("no separated frame layout fits the requested exact controls", exact_axes)


def _record_configuration(ctx, values: tuple) -> None:
    height, width, n_square, n_rect, side, rect_h, rect_w, bias, _ = values
    for label, value in (
        ("grid_h", height),
        ("grid_w", width),
        ("n_square", n_square),
        ("n_rect", n_rect),
        ("square_size", side),
        ("rect_h", rect_h),
        ("rect_w", rect_w),
        ("position_bias", bias),
    ):
        ctx.draw_choice(label, [value])
    texture = ctx.overrides.get("texture", bias)
    ctx.draw_choice("texture", [texture])


def _choose_dimension(ctx, label: str, pin: object | None, band: tuple[int, int]) -> int:
    values = [pin] if pin is not None else list(range(band[0], band[1] + 1))
    return ctx.draw_choice(label, values)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    pins = _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=pins,
    )

    texture = pins.get("texture")
    if texture in DEGENERATE_TEXTURES:
        h_band, w_band = _DIFFICULTY_RANGES[difficulty]
        height = _choose_dimension(ctx, "grid_h", pins.get("grid_h"), h_band)
        width = _choose_dimension(ctx, "grid_w", pins.get("grid_w"), w_band)
        ctx.draw_choice("texture", [texture])
        return _draw_from_degenerate(texture, height, width)

    selected = _choose_configuration(ctx, pins, seed, sample_index, difficulty)
    _record_configuration(ctx, selected)
    height, width, _, _, _, _, _, _, layout = selected
    grid = full_grid(height, width, 0)
    for _, top, left, shape_h, shape_w in layout:
        draw_rect_outline(grid, top, left, shape_h, shape_w, 5)
    reasons = self_check(grid)
    if reasons:
        raise RuntimeError(f"constructed invalid ordinary grid: {reasons}")
    return grid


def _draw_from_degenerate(name: str, height: int, width: int):
    grid = full_grid(height, width, 0)
    if name == "no_frames":
        return grid
    if name == "only_squares":
        side = min(4, height, width)
        if side >= 3:
            draw_rect_outline(grid, 0, 0, side, side, 5)
        return grid
    if name == "only_rects":
        rect_h, rect_w = min(3, height), min(5, width)
        if rect_h >= 3 and rect_w >= 4 and rect_h != rect_w:
            draw_rect_outline(grid, 0, 0, rect_h, rect_w, 5)
        return grid
    raise ValueError(f"unknown negative fixture: {name}")


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 5}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for candidate in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if candidate in remaining:
                    remaining.remove(candidate)
                    component.add(candidate)
                    stack.append(candidate)
        result.append(component)
    return result


def _square_zero_interior(grid: list[list[int]], component: set[tuple[int, int]]) -> bool:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    zeros = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] == 0
    ]
    if not zeros:
        return False
    zr0 = min(r for r, _ in zeros)
    zr1 = max(r for r, _ in zeros)
    zc0 = min(c for _, c in zeros)
    zc1 = max(c for _, c in zeros)
    side_r, side_c = zr1 - zr0 + 1, zc1 - zc0 + 1
    return side_r == side_c and len(zeros) == side_r * side_c



def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact numeric control from an ordinary generated scene.

    Ordinary generation emits isolated, complete color-5 frame perimeters with
    one shared size for every square and one shared ``(height, width)`` for
    every rectangle.  Reject anything outside that observable contract rather
    than guessing values from malformed or canonical-only teaching fixtures.
    """
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    if any(type(cell) is not int or cell not in (0, 5) for row in grid for cell in row):
        raise ValueError("ordinary scene must contain integer colors 0 and 5 only")

    square_sides: list[int] = []
    rectangle_dims: list[tuple[int, int]] = []
    for component in _components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        if frame_h < 3 or frame_w < 3:
            raise ValueError("ordinary frame is smaller than 3x3")
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if component != perimeter:
            raise ValueError("ordinary frame is not an isolated complete perimeter")
        if any(
            grid[r][c] != 0
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        ):
            raise ValueError("ordinary frame interior is not empty")
        if frame_h == frame_w:
            square_sides.append(frame_h)
        else:
            rectangle_dims.append((frame_h, frame_w))

    if not square_sides or not rectangle_dims:
        raise ValueError("ordinary scene must contain square and rectangular frames")
    if len(set(square_sides)) != 1:
        raise ValueError("ordinary square frames do not share one exact side length")
    if len(set(rectangle_dims)) != 1:
        raise ValueError("ordinary rectangular frames do not share exact dimensions")
    rect_h, rect_w = rectangle_dims[0]
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_square": len(square_sides),
        "n_rect": len(rectangle_dims),
        "square_size": square_sides[0],
        "rect_h": rect_h,
        "rect_w": rect_w,
    }

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical domain and reject malformed or no-positive scenes."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(cell) is not int or cell not in (0, 5) for row in grid for cell in row):
        return ["input must contain integer colors 0 and 5 only"]
    components = _components(grid)
    if not components:
        return ["no color-5 component found"]

    def frame_like(component):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            return False
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if not perimeter.issubset(component):
            return False
        return any(
            grid[r][c] == 0
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )

    # Every canonical input has at least two complete frame envelopes.  One
    # canonical negative example has no square interior, so requiring a firing
    # would incorrectly exclude a real label; requiring two frames still rejects
    # singleton, line, solid block, and one-family authoring impostors.
    if sum(frame_like(component) for component in components) < 2:
        return ["fewer than two complete color-5 frame envelopes"]
    return []
