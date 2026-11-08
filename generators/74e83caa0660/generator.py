"""Generator for ARC task 74e83caa0660: complete diagonal pairs into Xs.

Each active color appears at the two opposite corners of a disjoint 3x3 box.
The canonical rule fills both diagonals of every such box.  The generator's
public axes are deliberately small and exact: canvas height/width, pair count,
and the mix of main/anti-diagonal input pairs.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "74e83caa0660"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "68e47a26ff0a"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Place 1..8 distinct colors as pairs of opposite corners of disjoint 3x3 "
    "boxes on a black canvas. Each pair may use the main or anti diagonal. "
    "The canonical transformation completes both diagonals of each box, "
    "turning every two-corner clue into a five-cell X of the same color."
)

INVARIANTS = [
    "background is 0 and the canvas is a strict 5..30 rectangle",
    "every active color appears exactly twice",
    "each same-color pair occupies opposite corners of an exact 3x3 box",
    "the reserved 3x3 boxes are pairwise disjoint",
    "the canonical output draws both diagonals of each reserved box",
]

HELPFUL_TEXTURES = ("mixed", "main_only", "anti_only")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng, enlarged only when an exact n_pairs override needs room",
        "valid": "5..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng, enlarged only when an exact n_pairs override needs room",
        "valid": "5..30",
    },
    "n_pairs": {
        "type": "int",
        "default": "easy 2; medium/None 2..4; hard 3..4",
        "valid": "1..8",
    },
    "texture": {
        "type": "str",
        "default": "rng mixed|main_only|anti_only",
        "valid": "mixed|main_only|anti_only",
    },
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_DIFFICULTY_DIMS = {
    "easy": ((8, 9), (10, 11)),
    "medium": ((9, 11), (11, 14)),
    "hard": ((10, 13), (13, 17)),
}
_DIFFICULTY_COUNTS = {
    "easy": (2, 2),
    "medium": (2, 4),
    "hard": (3, 4),
}

Grid = list[list[int]]
Cell = tuple[int, int]


def _validate_request(difficulty: object, overrides: dict[str, object]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _strict_draw_int(ctx, label: str, lo: int, hi: int) -> int:
    """Draw an exact integer; reject bool/float/string override coercion."""
    return ctx.draw_int_strict(label, lo, hi)


def _capacity(height: int, width: int) -> int:
    return (height // 3) * (width // 3)


def _required_extent(pair_count: int, slots_other_axis: int) -> int:
    if slots_other_axis <= 0:
        return 31
    needed_slots = (pair_count + slots_other_axis - 1) // slots_other_axis
    return 3 * needed_slots


def _draw_dimensions(ctx, pair_count: int, band: str, overrides: dict[str, object]) -> tuple[int, int]:
    """Draw dimensions while preserving exact explicit count requests.

    An explicit canvas stays exact.  An unspecified dimension may expand within
    the declared 5..30 range so an explicit high pair count remains constructible.
    """
    (base_h_lo, base_h_hi), (base_w_lo, base_w_hi) = _DIFFICULTY_DIMS[band]
    has_h = overrides.get("grid_h") is not None
    has_w = overrides.get("grid_w") is not None

    if has_h and has_w:
        height = _strict_draw_int(ctx, "grid_h", 5, 30)
        width = _strict_draw_int(ctx, "grid_w", 5, 30)
    elif has_h:
        height = _strict_draw_int(ctx, "grid_h", 5, 30)
        required_w = _required_extent(pair_count, height // 3)
        if required_w > 30:
            raise ValueError(
                f"grid_h={height} supports at most {_capacity(height, 30)} disjoint 3x3 boxes"
            )
        width = _strict_draw_int(
            ctx,
            "grid_w",
            max(base_w_lo, required_w),
            max(base_w_hi, required_w),
        )
    elif has_w:
        width = _strict_draw_int(ctx, "grid_w", 5, 30)
        required_h = _required_extent(pair_count, width // 3)
        if required_h > 30:
            raise ValueError(
                f"grid_w={width} supports at most {_capacity(30, width)} disjoint 3x3 boxes"
            )
        height = _strict_draw_int(
            ctx,
            "grid_h",
            max(base_h_lo, required_h),
            max(base_h_hi, required_h),
        )
    else:
        height = _strict_draw_int(ctx, "grid_h", base_h_lo, base_h_hi)
        required_w = _required_extent(pair_count, height // 3)
        if required_w > 30:
            raise ValueError("requested pair count cannot fit within a 30x30 canvas")
        width = _strict_draw_int(
            ctx,
            "grid_w",
            max(base_w_lo, required_w),
            max(base_w_hi, required_w),
        )

    capacity = _capacity(height, width)
    if pair_count > capacity:
        raise ValueError(
            f"grid {height}x{width} supports at most {capacity} disjoint 3x3 boxes, "
            f"not n_pairs={pair_count}"
        )
    return height, width


def _pair_orientation(cells: Iterable[Cell]) -> str:
    first, second = sorted(cells)
    return "main" if second[1] > first[1] else "anti"


def observe_overrides(grid: Grid) -> dict[str, object]:
    """Recover every declared output-observable axis from one returned grid."""
    by_color: dict[int, list[Cell]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    orientations = {_pair_orientation(cells) for cells in by_color.values() if len(cells) == 2}
    texture = (
        "mixed" if orientations == {"main", "anti"}
        else "main_only" if orientations == {"main"}
        else "anti_only" if orientations == {"anti"}
        else "invalid"
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_pairs": len(by_color),
        "texture": texture,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input in the exact opposite-corner grammar."""
    _validate_request(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    if overrides.get("n_pairs") is not None:
        pair_count = _strict_draw_int(ctx, "n_pairs", 1, 8)
    else:
        lo, hi = _DIFFICULTY_COUNTS[band]
        pair_count = _strict_draw_int(ctx, "n_pairs", lo, hi)

    height, width = _draw_dimensions(ctx, pair_count, band, overrides)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    if pair_count == 1 and overrides.get("texture") == "mixed":
        raise ValueError("mixed texture requires at least two pairs")
    rng = ctx.draw_rng("layout")

    row_slots, col_slots = height // 3, width // 3
    row_margin, col_margin = height - 3 * row_slots, width - 3 * col_slots
    row_offset = rng.randint(0, row_margin)
    col_offset = rng.randint(0, col_margin)
    boxes = [
        (row_offset + 3 * row_slot, col_offset + 3 * col_slot)
        for row_slot in range(row_slots)
        for col_slot in range(col_slots)
    ]
    rng.shuffle(boxes)
    boxes = boxes[:pair_count]

    colors = list(range(1, 10))
    rng.shuffle(colors)
    colors = colors[:pair_count]

    if texture == "main_only":
        orientations = ["main"] * pair_count
    elif texture == "anti_only":
        orientations = ["anti"] * pair_count
    else:
        start = rng.randrange(2)
        orientations = ["main" if (start + index) % 2 == 0 else "anti" for index in range(pair_count)]
        if pair_count == 1:
            orientations[0] = rng.choice(("main", "anti"))

    grid = full_grid(height, width, 0)
    for color, (top, left), orientation in zip(colors, boxes, orientations):
        if orientation == "main":
            endpoints = ((top, left), (top + 2, left + 2))
        else:
            endpoints = ((top, left + 2), (top + 2, left))
        for r, c in endpoints:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid diagonal-pair grid: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate strict types, opposite-corner geometry and disjoint 3x3 boxes."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a nonempty list rectangle"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append(f"grid dimensions must be in 5..30, got {height}x{width}")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        return errors + ["grid must be rectangular with exact integer colors 0..9"]

    by_color: dict[int, list[Cell]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    if not by_color:
        return errors + ["no non-zero diagonal pairs found"]
    if len(by_color) > 8:
        errors.append(f"expected at most 8 active colors, found {len(by_color)}")

    reserved: set[Cell] = set()
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times instead of exactly twice")
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        if r1 - r0 != 2 or abs(c1 - c0) != 2:
            errors.append(f"color {color} is not at opposite corners of an exact 3x3 box")
            continue
        left = min(c0, c1)
        box = {(r, c) for r in range(r0, r0 + 3) for c in range(left, left + 3)}
        if box & reserved:
            errors.append(f"color {color}'s 3x3 box overlaps another reserved box")
        reserved.update(box)
    return errors
