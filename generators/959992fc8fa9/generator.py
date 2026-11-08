"""Generator for ARC task 45bbe264 / content hash 959992fc8fa9.

Each sparse source pixel paints its complete row and column.  A cell reached by
one source color keeps that color; a cell reached by two or more *different*
source colors becomes red (2).  Generated inputs keep source pixels in unique
rows and columns, matching every canonical example, while an explicit repeated-
color branch supplies lawful non-red intersections that rebut the shortcut
"paint every crossing red".
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "959992fc8fa9"
VERSION = "2.0.0"
TASK_ID = "959992fc8fa9"
RULE_HASH = "1d9c05259f79"
SUMMARY = (
    "Sparse pixels paint full row/column crosses; only intersections reached "
    "by different colors become red (2)."
)

INVARIANTS = [
    "background is 0 and input never contains red 2",
    "there are 2..5 sparse source pixels using at least two colors",
    "source pixels occupy pairwise-distinct rows and pairwise-distinct columns",
    "color multiplicity is all-distinct or exactly one repeated pair",
    "at most one source pixel is in a corner",
    "at least one different-color pair makes the red-intersection branch fire",
]

COLOR_PATTERNS = ("all_distinct", "one_repeat")
ALLOWED_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed choice within 6..18",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed choice within 6..18",
        "valid": "6..18",
    },
    "n_pixels": {
        "type": "int",
        "default": "difficulty-aware keyed choice within 2..5",
        "valid": "2..5",
    },
    "color_pattern": {
        "type": "str",
        "default": "sample-index schedule over all_distinct|one_repeat",
        "valid": "all_distinct|one_repeat",
    },
    "anchor_corner": {
        "type": "bool",
        "default": "sample-index schedule, usually false",
        "valid": "true|false",
    },
}

_BAND_SIZES = {
    "easy": tuple(range(6, 11)),
    "medium": tuple(range(9, 15)),
    "hard": tuple(range(13, 19)),
}
_BAND_COUNTS = {
    "easy": (2, 3),
    "medium": (2, 3, 4),
    "hard": (3, 4, 5),
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for label, lo, hi in (("grid_h", 6, 18), ("grid_w", 6, 18), ("n_pixels", 2, 5)):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{label} must be in {lo}..{hi}")

    pattern = overrides.get("color_pattern")
    if pattern is not None and pattern not in COLOR_PATTERNS:
        raise ValueError("color_pattern must be all_distinct or one_repeat")
    corner = overrides.get("anchor_corner")
    if corner is not None and type(corner) is not bool:
        raise ValueError("anchor_corner must be boolean")
    if pattern == "one_repeat" and overrides.get("n_pixels") == 2:
        raise ValueError("color_pattern=one_repeat requires n_pixels >= 3")


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)):
        return grid
    return [list(row) if isinstance(row, (list, tuple)) else row for row in grid]


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    errors = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}

    height = len(grid)
    bad_values = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("grid values must be integer ARC colors 0..9")

    pixels = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    counts = Counter(value for _, _, value in pixels)
    rows = [row for row, _, _ in pixels]
    cols = [col for _, col, _ in pixels]
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    corner_count = sum((row, col) in corners for row, col, _ in pixels)

    if not 6 <= height <= 18 or not 6 <= width <= 18:
        errors.append("grid dimensions must each be in 6..18")
    if not 2 <= len(pixels) <= 5:
        errors.append(f"expected 2..5 source pixels; got {len(pixels)}")
    if 2 in counts:
        errors.append("input must not contain red 2")
    if len(counts) < 2:
        errors.append("source pixels must use at least two colors")
    if len(set(rows)) != len(rows):
        errors.append("source pixels must occupy pairwise-distinct rows")
    if len(set(cols)) != len(cols):
        errors.append("source pixels must occupy pairwise-distinct columns")
    if corner_count > 1:
        errors.append("at most one source pixel may occupy a corner")

    multiplicities = sorted(counts.values(), reverse=True)
    if multiplicities and not (
        all(value == 1 for value in multiplicities)
        or (
            multiplicities[0] == 2
            and all(value == 1 for value in multiplicities[1:])
        )
    ):
        errors.append(
            "color multiplicity must be all-distinct or exactly one repeated pair"
        )

    color_pattern = None
    if multiplicities and all(value == 1 for value in multiplicities):
        color_pattern = "all_distinct"
    elif (
        multiplicities
        and multiplicities[0] == 2
        and all(value == 1 for value in multiplicities[1:])
    ):
        color_pattern = "one_repeat"

    return {
        "errors": errors,
        "grid": grid,
        "height": height,
        "width": width,
        "pixels": pixels,
        "counts": counts,
        "color_pattern": color_pattern,
        "anchor_corner": corner_count == 1,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding lessons; accept every canonical input."""
    del difficulty, meta
    return list(_analyze_scene(grid)["errors"])


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned input grid."""
    scene = _analyze_scene(grid)
    if scene["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(scene["errors"]))
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "n_pixels": len(scene["pixels"]),
        "color_pattern": scene["color_pattern"],
        "anchor_corner": scene["anchor_corner"],
    }


def rule_mirror(grid):
    """Small test-only mirror; production outputs remain Racket-authoritative."""
    height = len(grid)
    width = len(grid[0])
    pixels = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            colors = {
                value
                for source_row, source_col, value in pixels
                if row == source_row or col == source_col
            }
            if len(colors) == 1:
                output[row][col] = next(iter(colors))
            elif len(colors) > 1:
                output[row][col] = 2
    return output


def _band(difficulty):
    return difficulty if difficulty in ("easy", "hard") else "medium"


def _draw_axis_choice(ctx, label, default_options, all_options, overrides):
    options = all_options if label in overrides else default_options
    return ctx.draw_choice(label, tuple(options))


def _default_color_pattern(sample_index, band, requested_n):
    if requested_n == 2:
        return "all_distinct"
    period = {"easy": 4, "medium": 2, "hard": 3}[band]
    return "one_repeat" if sample_index % period else "all_distinct"


def _pick_positions(height, width, n_pixels, anchor_corner, rng):
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    for _ in range(512):
        if anchor_corner:
            anchor = rng.choice(tuple(sorted(corners)))
            remaining_rows = [row for row in range(height) if row != anchor[0]]
            remaining_cols = [col for col in range(width) if col != anchor[1]]
            rows = rng.sample(remaining_rows, n_pixels - 1)
            cols = rng.sample(remaining_cols, n_pixels - 1)
            rng.shuffle(cols)
            positions = [anchor] + list(zip(rows, cols))
            if sum(position in corners for position in positions) != 1:
                continue
        else:
            rows = rng.sample(range(height), n_pixels)
            cols = rng.sample(range(width), n_pixels)
            rng.shuffle(cols)
            positions = list(zip(rows, cols))
            if any(position in corners for position in positions):
                continue

        row_span = max(row for row, _ in positions) - min(row for row, _ in positions)
        col_span = max(col for _, col in positions) - min(col for _, col in positions)
        if n_pixels >= 3 and (row_span < 2 or col_span < 2):
            continue
        return positions
    raise RuntimeError("could not place a valid sparse source-pixel layout")


def _pick_colors(n_pixels, color_pattern, rng):
    palette = list(ALLOWED_COLORS)
    rng.shuffle(palette)
    if color_pattern == "all_distinct":
        colors = palette[:n_pixels]
    else:
        colors = palette[: n_pixels - 1] + [palette[0]]
        rng.shuffle(colors)
    return colors


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
    band = _band(difficulty)

    height = _draw_axis_choice(
        ctx, "grid_h", _BAND_SIZES[band], tuple(range(6, 19)), overrides
    )
    width = _draw_axis_choice(
        ctx, "grid_w", _BAND_SIZES[band], tuple(range(6, 19)), overrides
    )

    requested_n = overrides.get("n_pixels")
    if "color_pattern" in overrides:
        pattern_options = COLOR_PATTERNS
    else:
        pattern_options = (
            _default_color_pattern(sample_index, band, requested_n),
        )
    color_pattern = ctx.draw_choice("color_pattern", pattern_options)

    if color_pattern == "one_repeat" and requested_n == 2:
        raise ValueError("color_pattern=one_repeat requires n_pixels >= 3")
    default_counts = tuple(
        value for value in _BAND_COUNTS[band] if color_pattern != "one_repeat" or value >= 3
    )
    n_pixels = _draw_axis_choice(
        ctx, "n_pixels", default_counts, tuple(range(2, 6)), overrides
    )
    if color_pattern == "one_repeat" and n_pixels < 3:
        raise ValueError("color_pattern=one_repeat requires n_pixels >= 3")

    if "anchor_corner" in overrides:
        corner_options = (False, True)
    else:
        corner_options = (sample_index % 5 == 4,)
    anchor_corner = ctx.draw_choice("anchor_corner", corner_options)

    positions = _pick_positions(
        height,
        width,
        n_pixels,
        anchor_corner,
        ctx.draw_rng("placement"),
    )
    colors = _pick_colors(
        n_pixels,
        color_pattern,
        ctx.draw_rng("palette_assignment"),
    )
    grid = full_grid(height, width, 0)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid
