"""Generator for the crossed-strand woven-rectangle task ``f3e14006``.

A unique fullest row and column carry two colors apiece: a frequent base color
and exactly two special markers.  Their intersection contains one of the two
base colors and therefore selects horizontal or vertical weaving priority.
Both strands may span the whole grid or form one contiguous partial cross.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea61d17502dd"
TASK_ID = "ea61d17502dd"
RULE_HASH = "b956a6f1bc99"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A unique fullest row and column form two marked strands. Each has a base "
    "color and two special markers; the base color at their crossing selects "
    "horizontal or vertical priority for the canonical woven rectangle."
)

INVARIANTS = [
    "all non-background cells lie on one contiguous horizontal or vertical strand",
    "the unique fullest row and column each contain one base and exactly two special markers",
    "the four strand colors are distinct",
    "the crossing cell is one strand's base color and selects weaving priority",
]

PRIMARIES = ("horizontal", "vertical")
SPAN_MODES = ("full", "partial")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware five-shape schedule",
        "valid": "10..25",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware five-shape schedule",
        "valid": "10..15",
    },
    "primary": {
        "type": "str",
        "default": "four-step semantic schedule",
        "valid": "|".join(PRIMARIES),
    },
    "span_mode": {
        "type": "str",
        "default": "four-step semantic schedule",
        "valid": "|".join(SPAN_MODES),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_SHAPE_SCHEDULES = {
    None: ((10, 10), (12, 12), (15, 15), (25, 15), (18, 13)),
    "easy": ((10, 10), (12, 12), (11, 10), (10, 12), (12, 11)),
    "medium": ((12, 12), (15, 15), (14, 13), (13, 14), (15, 12)),
    "hard": ((25, 15), (15, 15), (20, 15), (18, 14), (22, 13)),
}
_SEMANTIC_SCHEDULE = (
    ("horizontal", "full"),
    ("vertical", "full"),
    ("horizontal", "partial"),
    ("vertical", "partial"),
)


def _validate_request(difficulty, overrides):
    if difficulty not in _SHAPE_SCHEDULES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override key(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 10, 25), ("grid_w", 10, 15)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "primary" in overrides and overrides["primary"] not in PRIMARIES:
        raise ValueError(f"primary must be one of {PRIMARIES!r}")
    if "span_mode" in overrides and overrides["span_mode"] not in SPAN_MODES:
        raise ValueError(f"span_mode must be one of {SPAN_MODES!r}")


def _partial_span(size, crossing, rng):
    """Return a non-full contiguous span with crossing strictly inside it."""
    length = rng.randint(6, size - 2)
    low_start = max(0, crossing - length + 2)
    high_start = min(crossing - 1, size - length)
    if low_start > high_start:  # guarded by size>=10 and crossing in 2..size-3
        raise AssertionError("no legal partial span")
    start = rng.randint(low_start, high_start)
    return start, start + length - 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)

    shape_schedule = _SHAPE_SCHEDULES[difficulty]
    default_h, default_w = shape_schedule[sample_index % len(shape_schedule)]
    default_primary, default_span_mode = _SEMANTIC_SCHEDULE[
        sample_index % len(_SEMANTIC_SCHEDULE)
    ]
    effective = {
        "grid_h": default_h,
        "grid_w": default_w,
        "primary": default_primary,
        "span_mode": default_span_mode,
    }
    effective.update(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 10, 25)
    width = ctx.draw_int("grid_w", 10, 15)
    primary = ctx.draw_choice("primary", PRIMARIES)
    span_mode = ctx.draw_choice("span_mode", SPAN_MODES)
    horizontal_base, horizontal_special, vertical_base, vertical_special = (
        ctx.draw_distinct_colors("strand_colors", n=4, exclude={0})
    )

    rng = ctx.draw_rng("strand_geometry")
    strand_row = rng.randint(2, height - 3)
    strand_col = rng.randint(2, width - 3)
    if span_mode == "full":
        horizontal_start, horizontal_end = 0, width - 1
        vertical_start, vertical_end = 0, height - 1
    else:
        horizontal_start, horizontal_end = _partial_span(width, strand_col, rng)
        vertical_start, vertical_end = _partial_span(height, strand_row, rng)

    grid = full_grid(height, width, 0)
    for col_index in range(horizontal_start, horizontal_end + 1):
        grid[strand_row][col_index] = horizontal_base
    for row_index in range(vertical_start, vertical_end + 1):
        grid[row_index][strand_col] = vertical_base

    left_marker = rng.choice(range(horizontal_start, strand_col))
    right_marker = rng.choice(range(strand_col + 1, horizontal_end + 1))
    grid[strand_row][left_marker] = horizontal_special
    grid[strand_row][right_marker] = horizontal_special

    upper_marker = rng.choice(range(vertical_start, strand_row))
    lower_marker = rng.choice(range(strand_row + 1, vertical_end + 1))
    grid[upper_marker][strand_col] = vertical_special
    grid[lower_marker][strand_col] = vertical_special

    grid[strand_row][strand_col] = (
        horizontal_base if primary == "horizontal" else vertical_base
    )
    return grid


def _line_roles(values, label, errors):
    counts = Counter(values)
    if len(counts) != 2:
        errors.append(f"{label} strand must contain exactly two colors")
        return None
    ordered = counts.most_common()
    if ordered[0][1] == ordered[1][1]:
        errors.append(f"{label} strand has no unique base color")
        return None
    base, base_count = ordered[0]
    special, special_count = ordered[1]
    if special_count != 2:
        errors.append(
            f"{label} strand must contain exactly two special markers, found {special_count}"
        )
    if base_count <= special_count:
        errors.append(f"{label} base color must be more frequent than its special color")
    return base, special


def _analysis(grid):
    errors = []
    facts = {}
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list of rows"], "facts": facts}
    if not all(isinstance(row_values, list) and row_values for row_values in grid):
        return {"errors": ["every row must be a nonempty list"], "facts": facts}
    width = len(grid[0])
    if any(len(row_values) != width for row_values in grid):
        return {"errors": ["ragged grid"], "facts": facts}
    height = len(grid)
    if not (10 <= height <= 25 and 10 <= width <= 15):
        errors.append(f"grid shape must be within 10..25 by 10..15, got {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row_values in grid
        for value in row_values
    ):
        return {
            "errors": errors + ["grid colors must be integers 0..9 (not booleans)"],
            "facts": facts,
        }

    palette = {value for row_values in grid for value in row_values}
    if 0 not in palette:
        errors.append("expected background color 0")
    nonzero_palette = palette - {0}
    if len(nonzero_palette) != 4:
        errors.append(
            f"expected exactly four strand colors, found {len(nonzero_palette)}"
        )

    row_nonzero_counts = [
        sum(value != 0 for value in row_values) for row_values in grid
    ]
    col_nonzero_counts = [
        sum(grid[row_index][col_index] != 0 for row_index in range(height))
        for col_index in range(width)
    ]
    fullest_row_count = max(row_nonzero_counts)
    fullest_col_count = max(col_nonzero_counts)
    fullest_rows = [
        row_index
        for row_index, count in enumerate(row_nonzero_counts)
        if count == fullest_row_count
    ]
    fullest_cols = [
        col_index
        for col_index, count in enumerate(col_nonzero_counts)
        if count == fullest_col_count
    ]
    if len(fullest_rows) != 1 or fullest_row_count < 6:
        errors.append(
            "expected one unique horizontal strand with at least six cells; "
            f"rows={fullest_rows}, count={fullest_row_count}"
        )
    if len(fullest_cols) != 1 or fullest_col_count < 6:
        errors.append(
            "expected one unique vertical strand with at least six cells; "
            f"cols={fullest_cols}, count={fullest_col_count}"
        )
    if (
        len(fullest_rows) != 1
        or len(fullest_cols) != 1
        or fullest_row_count < 6
        or fullest_col_count < 6
    ):
        return {"errors": errors, "facts": facts}

    strand_row, strand_col = fullest_rows[0], fullest_cols[0]
    off_strand = [
        (row_index, col_index)
        for row_index, row_values in enumerate(grid)
        for col_index, value in enumerate(row_values)
        if value != 0 and row_index != strand_row and col_index != strand_col
    ]
    if off_strand:
        errors.append(f"non-background cells occur off the two strands: {off_strand[:3]}")

    horizontal_positions = [
        col_index for col_index in range(width) if grid[strand_row][col_index] != 0
    ]
    vertical_positions = [
        row_index for row_index in range(height) if grid[row_index][strand_col] != 0
    ]
    if horizontal_positions != list(
        range(horizontal_positions[0], horizontal_positions[-1] + 1)
    ):
        errors.append("horizontal strand must be contiguous")
    if vertical_positions != list(
        range(vertical_positions[0], vertical_positions[-1] + 1)
    ):
        errors.append("vertical strand must be contiguous")
    if strand_col not in horizontal_positions or strand_row not in vertical_positions:
        errors.append("the two strands must intersect")

    horizontal_full = len(horizontal_positions) == width
    vertical_full = len(vertical_positions) == height
    if horizontal_full != vertical_full:
        errors.append("horizontal and vertical spans must both be full or both be partial")
    span_mode = "full" if horizontal_full and vertical_full else "partial"

    horizontal_values = [
        grid[strand_row][col_index]
        for col_index in horizontal_positions
        if col_index != strand_col
    ]
    vertical_values = [
        grid[row_index][strand_col]
        for row_index in vertical_positions
        if row_index != strand_row
    ]
    horizontal_roles = _line_roles(horizontal_values, "horizontal", errors)
    vertical_roles = _line_roles(vertical_values, "vertical", errors)
    if horizontal_roles is None or vertical_roles is None:
        return {"errors": errors, "facts": facts}
    horizontal_base, horizontal_special = horizontal_roles
    vertical_base, vertical_special = vertical_roles
    if len({horizontal_base, horizontal_special, vertical_base, vertical_special}) != 4:
        errors.append("horizontal and vertical base/special colors must all be distinct")

    crossing = grid[strand_row][strand_col]
    if crossing == horizontal_base:
        primary = "horizontal"
    elif crossing == vertical_base:
        primary = "vertical"
    else:
        errors.append("crossing cell must contain one of the two base colors")
        primary = None

    horizontal_marker_cols = [
        col_index
        for col_index in horizontal_positions
        if col_index != strand_col
        and grid[strand_row][col_index] == horizontal_special
    ]
    vertical_marker_rows = [
        row_index
        for row_index in vertical_positions
        if row_index != strand_row
        and grid[row_index][strand_col] == vertical_special
    ]

    facts.update(
        {
            "grid_h": height,
            "grid_w": width,
            "strand_row": strand_row,
            "strand_col": strand_col,
            "horizontal_base": horizontal_base,
            "horizontal_special": horizontal_special,
            "vertical_base": vertical_base,
            "vertical_special": vertical_special,
            "horizontal_marker_cols": horizontal_marker_cols,
            "vertical_marker_rows": vertical_marker_rows,
            "primary": primary,
            "span_mode": span_mode,
        }
    )
    return {"errors": errors, "facts": facts}


def rule_mirror(grid, *, force_primary=None):
    """Independent Python mirror of the selected canonical Racket rule.

    ``force_primary`` is intentionally private to semantic rivals: it changes
    only the priority decision while retaining every other inferred role.
    """
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if force_primary is None:
        primary = facts["primary"]
    elif force_primary in PRIMARIES:
        primary = force_primary
    else:
        raise ValueError(f"force_primary must be one of {PRIMARIES!r}")

    strand_row = facts["strand_row"]
    horizontal_markers = facts["horizontal_marker_cols"]
    vertical_markers = facts["vertical_marker_rows"]
    min_row = min([strand_row, *vertical_markers])
    max_row = max([strand_row, *vertical_markers])
    min_col = min(horizontal_markers)
    max_col = max(horizontal_markers)
    near_vertical = min(
        vertical_markers, key=lambda row_index: abs(row_index - strand_row)
    )
    far_vertical = max(
        vertical_markers, key=lambda row_index: abs(row_index - strand_row)
    )

    horizontal_base = facts["horizontal_base"]
    horizontal_special = facts["horizontal_special"]
    vertical_base = facts["vertical_base"]
    vertical_special = facts["vertical_special"]
    horizontal_primary = primary == "horizontal"

    height, width = facts["grid_h"], facts["grid_w"]
    output = full_grid(height, width, 0)
    band_low, band_high = sorted((near_vertical, far_vertical))
    for row_index in range(min_row, max_row + 1):
        warp_row = (row_index - min_row) % 2 == 0
        for col_index in range(min_col, max_col + 1):
            warp_col = (col_index - min_col) % 2 == 0
            if warp_row:
                in_band = band_low <= row_index <= band_high
                if in_band:
                    if warp_col:
                        value = vertical_special
                    elif row_index == near_vertical and horizontal_primary:
                        value = horizontal_base
                    else:
                        value = vertical_base
                elif warp_col:
                    value = horizontal_special
                else:
                    value = vertical_base
            elif horizontal_primary:
                value = horizontal_base
            elif warp_col:
                value = horizontal_base
            else:
                value = vertical_base
            output[row_index][col_index] = value
    return output


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "primary": facts["primary"],
        "span_mode": facts["span_mode"],
    }


def _always_horizontal(grid):
    return rule_mirror(grid, force_primary="horizontal")


def _always_vertical(grid):
    return rule_mirror(grid, force_primary="vertical")


def _horizontal_priority_witness(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["facts"]["primary"] == "horizontal"


def _vertical_priority_witness(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["facts"]["primary"] == "vertical"


SEMANTIC_RIVALS = {
    "always_horizontal_priority": _always_horizontal,
    "always_vertical_priority": _always_vertical,
}
SEMANTIC_WITNESSES = {
    "horizontal_priority_changes_the_weave": _horizontal_priority_witness,
    "vertical_priority_changes_the_weave": _vertical_priority_witness,
}
WITNESS_RIVALS = {
    "horizontal_priority_changes_the_weave": ["always_vertical_priority"],
    "vertical_priority_changes_the_weave": ["always_horizontal_priority"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject a lesson while either priority-blind rival fits every demo."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"priority-blind competitor survived all demos: {name}")
    return reasons
