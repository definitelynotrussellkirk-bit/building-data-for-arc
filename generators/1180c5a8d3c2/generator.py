"""Generator for ARC task 7c008303.

A full cyan row and column split the input into four quadrants.  One corner
quadrant is exactly a 2x2 color key.  The diagonally opposite quadrant holds a
binary green mask.  The output is that mask's quadrant, with each green cell
recolored by the key entry for the corresponding top-left/top-right/
bottom-left/bottom-right half of the output.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1180c5a8d3c2"
TASK_ID = "1180c5a8d3c2"
VERSION = "3.0.0"
RULE_HASH = "7a1d0bb73f12"

SUMMARY = (
    "A single full color-8 row and column partition the input into four "
    "quadrants. One corner quadrant is exactly a filled 2x2 key using three "
    "or four colors outside {0,3,8}; the diagonally opposite quadrant is a "
    "0/3 mask and the two remaining quadrants are empty. Crop the mask "
    "quadrant. Each green cell in its top-left, top-right, bottom-left, or "
    "bottom-right half becomes the matching key color; mask zeros remain 0."
)

INVARIANTS = [
    "exactly one full color-8 row and one full color-8 column form the divider",
    "the key quadrant is exactly 2x2, fully colored, and uses three or four colors outside {0,3,8}",
    "the diagonally opposite quadrant contains only 0 and 3; the other two quadrants are all 0",
    "each of the mask's four positional regions contains both a green witness and a zero witness",
    "the output shape is the mask-quadrant shape and all four key positions affect the answer",
]

COUNTER_HYPOTHESES = [
    "return the marker quadrant or the 2x2 key itself",
    "copy the mask without recoloring it",
    "use one modal key color for every green cell",
    "map colors by absolute input position rather than position within the cropped mask",
    "assume the key is always in one fixed corner",
    "assume all four key colors are distinct",
    "infer the answer from green-cell count or texture alone",
]

KEY_CORNERS = ("tl", "tr", "bl", "br")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed within 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed within 8..14",
        "valid": "8..14",
    },
    "key_corner": {
        "type": "str",
        "default": "uniform",
        "valid": "|".join(KEY_CORNERS),
    },
    "repeat_key": {
        "type": "bool",
        "default": "uniform",
        "valid": "true|false",
    },
}

# No texture mode is part of the lawful task grammar.  In particular, malformed
# no-cross/no-pattern grids are mutation fixtures, not training examples.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _quadrants(h: int, w: int, cross_r: int, cross_c: int):
    return {
        "tl": (0, 0, cross_r, cross_c),
        "tr": (0, cross_c + 1, cross_r, w),
        "bl": (cross_r + 1, 0, h, cross_c),
        "br": (cross_r + 1, cross_c + 1, h, w),
    }


def _opposite(corner: str) -> str:
    return {"tl": "br", "tr": "bl", "bl": "tr", "br": "tl"}[corner]


def _region_cells(height: int, width: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Cells for the four positional key regions, in key row-major order."""
    half_h = height // 2
    half_w = width // 2
    row_ranges = ((0, half_h), (half_h, height))
    col_ranges = ((0, half_w), (half_w, width))
    regions: list[tuple[tuple[int, int], ...]] = []
    for r_lo, r_hi in row_ranges:
        for c_lo, c_hi in col_ranges:
            regions.append(
                tuple((r, c) for r in range(r_lo, r_hi) for c in range(c_lo, c_hi))
            )
    return tuple(regions)


def _key_and_mask_bounds(h: int, w: int, key_corner: str):
    if key_corner == "tl":
        cross_r, cross_c = 2, 2
        key_bounds = (0, 0, 2, 2)
    elif key_corner == "tr":
        cross_r, cross_c = 2, w - 3
        key_bounds = (0, w - 2, 2, w)
    elif key_corner == "bl":
        cross_r, cross_c = h - 3, 2
        key_bounds = (h - 2, 0, h, 2)
    else:
        cross_r, cross_c = h - 3, w - 3
        key_bounds = (h - 2, w - 2, h, w)
    mask_bounds = _quadrants(h, w, cross_r, cross_c)[_opposite(key_corner)]
    return cross_r, cross_c, key_bounds, mask_bounds


def _make_key(ctx, repeat_key: bool) -> tuple[int, int, int, int]:
    colors = list(
        ctx.draw_distinct_colors("key_colors", n=4, exclude={0, 3, 8})
    )
    if repeat_key:
        rng = ctx.draw_rng("key_repeat_layout")
        source, target = rng.sample(range(4), 2)
        colors[target] = colors[source]
    return tuple(colors)


def _make_mask(ctx, height: int, width: int) -> list[list[int]]:
    """Create a varied mask with positive and negative evidence in every region."""
    if height < 5 or width < 5:
        raise ValueError("mask quadrant must be at least 5x5")
    rng = ctx.draw_rng("mask_layout")
    regions = _region_cells(height, width)

    forced_green: set[tuple[int, int]] = set()
    forced_zero: set[tuple[int, int]] = set()
    for region in regions:
        # With the 5x5 minimum, every region has at least four cells.
        green, zero = rng.sample(list(region), 2)
        forced_green.add(green)
        forced_zero.add(zero)

    if ctx.difficulty == "easy":
        density = rng.uniform(0.28, 0.38)
    elif ctx.difficulty == "hard":
        density = rng.uniform(0.43, 0.56)
    else:
        density = rng.uniform(0.34, 0.48)

    area = height * width
    target = round(area * density)
    target = max(len(forced_green), min(target, area - len(forced_zero)))
    eligible = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in forced_green and (r, c) not in forced_zero
    ]
    rng.shuffle(eligible)
    green_cells = forced_green | set(eligible[: target - len(forced_green)])
    return [
        [3 if (r, c) in green_cells else 0 for c in range(width)]
        for r in range(height)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh, lawful task input."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 14)
    w = ctx.draw_int_diff("grid_w", 8, 14)
    key_corner = ctx.draw_choice("key_corner", KEY_CORNERS)
    repeat_key = ctx.draw_choice("repeat_key", (False, True))
    key = _make_key(ctx, repeat_key)

    cross_r, cross_c, key_bounds, mask_bounds = _key_and_mask_bounds(
        h, w, key_corner
    )
    g = full_grid(h, w, 0)
    for c in range(w):
        g[cross_r][c] = 8
    for r in range(h):
        g[r][cross_c] = 8

    kr1, kc1, kr2, kc2 = key_bounds
    key_index = 0
    for r in range(kr1, kr2):
        for c in range(kc1, kc2):
            g[r][c] = key[key_index]
            key_index += 1

    mr1, mc1, mr2, mc2 = mask_bounds
    mask = _make_mask(ctx, mr2 - mr1, mc2 - mc1)
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            g[mr1 + r][mc1 + c] = value
    return g


def _analysis(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse the task grammar once for self_check and override observation."""
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return None, ["grid rows must be non-empty lists"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return None, ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["grid cells must be integer ARC colors 0..9"]

    h = len(grid)
    full_rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(full_rows) != 1 or len(full_cols) != 1:
        return None, [
            "expected exactly one full color-8 cross row and column; "
            f"rows={full_rows}, cols={full_cols}"
        ]
    cross_r, cross_c = full_rows[0], full_cols[0]
    if any(
        grid[r][c] == 8 and r != cross_r and c != cross_c
        for r in range(h)
        for c in range(w)
    ):
        return None, ["color 8 may appear only on the divider row or column"]

    roles: dict[str, str] = {}
    key_values: tuple[int, ...] | None = None
    mask_corner: str | None = None
    mask_bounds: tuple[int, int, int, int] | None = None
    errors: list[str] = []
    for corner, bounds in _quadrants(h, w, cross_r, cross_c).items():
        r1, c1, r2, c2 = bounds
        height, width = r2 - r1, c2 - c1
        values = tuple(grid[r][c] for r in range(r1, r2) for c in range(c1, c2))
        if not values:
            errors.append(f"{corner} quadrant is empty-sized")
            continue
        if height == 2 and width == 2 and all(v not in (0, 3, 8) for v in values):
            if len(set(values)) not in (3, 4):
                errors.append(
                    f"{corner} key must use three or four distinct colors, got {len(set(values))}"
                )
            roles[corner] = "key"
            key_values = values
        elif all(v == 0 for v in values):
            roles[corner] = "empty"
        elif all(v in (0, 3) for v in values) and any(v == 3 for v in values):
            roles[corner] = "mask"
            mask_corner = corner
            mask_bounds = bounds
        else:
            roles[corner] = "invalid"
            errors.append(f"{corner} quadrant violates key/mask/empty grammar")

    key_corners = [corner for corner, role in roles.items() if role == "key"]
    mask_corners = [corner for corner, role in roles.items() if role == "mask"]
    empty_corners = [corner for corner, role in roles.items() if role == "empty"]
    if len(key_corners) != 1:
        errors.append(f"expected one exact 2x2 key quadrant, found {key_corners}")
    if len(mask_corners) != 1:
        errors.append(f"expected one 0/3 mask quadrant, found {mask_corners}")
    if len(empty_corners) != 2:
        errors.append(f"expected two empty quadrants, found {empty_corners}")
    if len(key_corners) == 1 and len(mask_corners) == 1:
        if _opposite(key_corners[0]) != mask_corners[0]:
            errors.append("the key and mask quadrants must be diagonally opposite")

    region_counts: list[dict[str, int]] = []
    if mask_bounds is not None:
        r1, c1, r2, c2 = mask_bounds
        mask_h, mask_w = r2 - r1, c2 - c1
        if mask_h < 5 or mask_w < 5:
            errors.append(f"mask quadrant must be at least 5x5, got {mask_h}x{mask_w}")
        else:
            for index, region in enumerate(_region_cells(mask_h, mask_w)):
                green = sum(grid[r1 + r][c1 + c] == 3 for r, c in region)
                zero = len(region) - green
                region_counts.append({"green": green, "zero": zero, "area": len(region)})
                if green == 0:
                    errors.append(f"mask key-region {index} has no green branch witness")
                if zero == 0:
                    errors.append(f"mask key-region {index} has no zero/background witness")

    if errors:
        return None, errors
    assert key_values is not None and mask_corner is not None and mask_bounds is not None
    key_corner = key_corners[0]
    return {
        "grid_h": h,
        "grid_w": w,
        "cross_r": cross_r,
        "cross_c": cross_c,
        "key_corner": key_corner,
        "mask_corner": mask_corner,
        "key_values": key_values,
        "repeat_key": len(set(key_values)) == 3,
        "mask_bounds": mask_bounds,
        "region_counts": region_counts,
    }, []


def observe_overrides(grid) -> dict[str, int | str | bool]:
    """Recover every declared axis exactly from a returned grid."""
    parsed, errors = _analysis(grid)
    if errors or parsed is None:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": parsed["grid_h"],
        "grid_w": parsed["grid_w"],
        "key_corner": parsed["key_corner"],
        "repeat_key": parsed["repeat_key"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or shortcut-friendly lessons; accept all canonical inputs."""
    _ = difficulty, meta
    _parsed, errors = _analysis(grid)
    return errors
