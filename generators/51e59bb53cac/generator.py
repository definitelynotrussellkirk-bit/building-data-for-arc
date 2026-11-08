"""Generator for ARC task 7ee1c6ea / content hash 51e59bb53cac.

A single gray (5) rectangular frame encloses zeros and exactly two colors.
The output swaps those two colors only in the strict frame interior.  The same
colors also form dense, unchanged clutter outside the frame so a whole-grid
color swap is observably wrong.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "51e59bb53cac"
TASK_ID = "51e59bb53cac"
VERSION = "2.0.0"  # canonical two-color texture, scoped-swap witnesses, honest observable axes
RULE_HASH = "6efb83adf2b2"
SUMMARY = (
    "Swap the two nonzero colors inside the sole gray frame; preserve the "
    "same colors outside it."
)

INVARIANTS = [
    "background is 0 and the only gray cells are one complete rectangular 5-frame",
    "the strict frame interior contains exactly two colors, both repeated, plus zero",
    "the two interior color counts differ so the swap changes their histogram",
    "both swappable colors also occur outside the frame and remain unchanged",
    "the full palette is exactly {0, 5, interior-color-1, interior-color-2}",
]

FRAME_ANCHORS = ("corner", "edge", "interior")
PALETTE_KINDS = ("canonical", "broad")
CANONICAL_COLOR_PAIRS = ((1, 7), (2, 3), (4, 9), (6, 8))
LEGAL_COLORS = tuple(color for color in range(1, 10) if color != 5)
BROAD_COLOR_PAIRS = tuple(
    (left, right)
    for index, left in enumerate(LEGAL_COLORS)
    for right in LEGAL_COLORS[index + 1 :]
    if (left, right) not in CANONICAL_COLOR_PAIRS
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped keyed draw",
        "valid": "8..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped keyed draw",
        "valid": "8..22",
    },
    "frame_h": {
        "type": "int",
        "default": "difficulty-shaped keyed draw, constrained to fit",
        "valid": "5..10",
    },
    "frame_w": {
        "type": "int",
        "default": "difficulty-shaped keyed draw, constrained to fit",
        "valid": "5..10",
    },
    "frame_anchor": {
        "type": "str",
        "default": "keyed choice among feasible anchor classes",
        "valid": "|".join(FRAME_ANCHORS),
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed canonical-or-broad pair family",
        "valid": "|".join(PALETTE_KINDS),
    },
    "fill_ratio": {
        "type": "float",
        "default": "difficulty-shaped interior occupancy",
        "valid": "0.35..0.90",
    },
    "outside_fill_ratio": {
        "type": "float",
        "default": "difficulty-shaped exterior occupancy",
        "valid": "0.30..0.85",
    },
}


def _draw_banded_int(ctx, label: str, lo: int, hi: int) -> int:
    """Difficulty-shape a full-range integer without narrowing overrides."""
    return ctx.draw_int_diff(label, lo, hi)


def _draw_ratio(
    ctx,
    label: str,
    *,
    valid_lo: float,
    valid_hi: float,
    default_lo: float,
    default_hi: float,
) -> float:
    raw = ctx.overrides.get(label)
    if raw is not None:
        value = float(raw)
        if not valid_lo <= value <= valid_hi:
            raise ValueError(
                f"{label} override {value} outside [{valid_lo}, {valid_hi}]"
            )
        ctx._record(label, value, from_override=True)
        return value
    value = ctx.draw_rng(label).uniform(default_lo, default_hi)
    ctx._record(label, value, from_override=False)
    return value


def _anchor_positions(
    height: int, width: int, frame_h: int, frame_w: int, anchor: str
) -> list[tuple[int, int]]:
    max_row = height - frame_h - 1
    max_col = width - frame_w - 1
    if max_row < 1 or max_col < 1:
        return []
    positions: list[tuple[int, int]] = []
    for row in range(1, max_row + 1):
        row_edge = row in {1, max_row}
        for col in range(1, max_col + 1):
            col_edge = col in {1, max_col}
            category = (
                "corner"
                if row_edge and col_edge
                else "edge"
                if row_edge != col_edge
                else "interior"
            )
            if category == anchor:
                positions.append((row, col))
    return positions


def _feasible_anchors(
    height: int, width: int, frame_h: int, frame_w: int
) -> tuple[str, ...]:
    return tuple(
        anchor
        for anchor in FRAME_ANCHORS
        if _anchor_positions(height, width, frame_h, frame_w, anchor)
    )


def _choose_color_pair(ctx, palette_kind: str) -> tuple[int, int]:
    pool = (
        CANONICAL_COLOR_PAIRS
        if palette_kind == "canonical"
        else BROAD_COLOR_PAIRS
    )
    return ctx.draw_rng("color_pair").choice(pool)


def _neighbors(cell: tuple[int, int]) -> Iterable[tuple[int, int]]:
    row, col = cell
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _connected_cells(
    allowed: list[tuple[int, int]],
    starts: list[tuple[int, int]],
    count: int,
    rng,
) -> list[tuple[int, int]]:
    """Grow a randomized connected set from one or more guaranteed starts."""
    allowed_set = set(allowed)
    selected = list(dict.fromkeys(starts))
    selected_set = set(selected)
    if not selected_set <= allowed_set:
        raise ValueError("connected-cell seed lies outside the legal region")
    target = min(max(count, len(selected)), len(allowed_set))
    frontier = {
        neighbor
        for cell in selected
        for neighbor in _neighbors(cell)
        if neighbor in allowed_set and neighbor not in selected_set
    }
    while len(selected) < target:
        if not frontier:
            raise ValueError("legal paint region disconnected before target occupancy")
        choices = sorted(frontier)
        cell = choices[rng.randrange(len(choices))]
        frontier.remove(cell)
        selected.append(cell)
        selected_set.add(cell)
        for neighbor in _neighbors(cell):
            if neighbor in allowed_set and neighbor not in selected_set:
                frontier.add(neighbor)
    return selected


def _unequal_color_sequence(
    count: int, colors: tuple[int, int], rng
) -> list[int]:
    if count < 5:
        raise ValueError("need at least five painted interior cells")
    first_count = count // 2
    if count % 2 == 0:
        first_count -= 1
    first_count = max(2, first_count)
    second_count = count - first_count
    if second_count < 2 or first_count == second_count:
        raise ValueError("could not allocate two repeated unequal color counts")
    values = [colors[0]] * first_count + [colors[1]] * second_count
    rng.shuffle(values)
    return values


def _balanced_color_sequence(
    count: int, colors: tuple[int, int], rng
) -> list[int]:
    if count < 4:
        raise ValueError("need four exterior witnesses for two colors")
    first_count = count // 2
    values = [colors[0]] * first_count + [colors[1]] * (count - first_count)
    rng.shuffle(values)
    return values


def _outside_zones(
    height: int,
    width: int,
    row: int,
    col: int,
    frame_h: int,
    frame_w: int,
) -> dict[str, list[tuple[int, int]]]:
    bottom = row + frame_h - 1
    right = col + frame_w - 1
    return {
        "top": [(r, c) for r in range(0, row) for c in range(width)],
        "bottom": [
            (r, c) for r in range(bottom + 1, height) for c in range(width)
        ],
        "left": [
            (r, c)
            for r in range(row, bottom + 1)
            for c in range(0, col)
        ],
        "right": [
            (r, c)
            for r in range(row, bottom + 1)
            for c in range(right + 1, width)
        ],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown overrides: {', '.join(unknown)}")

    requested_anchor = overrides.get("frame_anchor")
    if requested_anchor is not None and requested_anchor not in FRAME_ANCHORS:
        raise ValueError(f"unknown frame_anchor: {requested_anchor!r}")
    requested_frame_h = overrides.get("frame_h")
    requested_frame_w = overrides.get("frame_w")
    if requested_frame_h is not None and not 5 <= int(requested_frame_h) <= 10:
        raise ValueError("frame_h override outside 5..10")
    if requested_frame_w is not None and not 5 <= int(requested_frame_w) <= 10:
        raise ValueError("frame_w override outside 5..10")

    # A requested edge/interior class needs slack beyond the one-cell margin.
    anchor_slack = 4 if requested_anchor in {"edge", "interior"} else 2
    min_height = max(
        8,
        int(requested_frame_h) + anchor_slack
        if requested_frame_h is not None
        else 9 if requested_anchor in {"edge", "interior"} else 8,
    )
    min_width = max(
        8,
        int(requested_frame_w) + anchor_slack
        if requested_frame_w is not None
        else 9 if requested_anchor in {"edge", "interior"} else 8,
    )
    if min_height > 22 or min_width > 22:
        raise ValueError("requested frame/anchor combination cannot fit in 22x22")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_banded_int(ctx, "grid_h", min_height, 22)
    width = _draw_banded_int(ctx, "grid_w", min_width, 22)

    frame_slack = 4 if requested_anchor in {"edge", "interior"} else 2
    max_frame_h = min(10, height - frame_slack)
    max_frame_w = min(10, width - frame_slack)
    frame_h = _draw_banded_int(ctx, "frame_h", 5, max_frame_h)
    frame_w = _draw_banded_int(ctx, "frame_w", 5, max_frame_w)

    feasible = _feasible_anchors(height, width, frame_h, frame_w)
    if not feasible:
        raise ValueError("no legal frame placement with a one-cell exterior margin")
    frame_anchor = ctx.draw_choice("frame_anchor", feasible)
    positions = _anchor_positions(height, width, frame_h, frame_w, frame_anchor)
    frame_row, frame_col = ctx.draw_rng("frame_position").choice(positions)

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    colors = _choose_color_pair(ctx, palette_kind)

    band = difficulty or "medium"
    ratio_bands = {
        "easy": ((0.42, 0.58), (0.48, 0.62)),
        "medium": ((0.55, 0.72), (0.58, 0.72)),
        "hard": ((0.68, 0.86), (0.66, 0.80)),
    }
    (fill_lo, fill_hi), (outside_lo, outside_hi) = ratio_bands[band]
    fill_ratio = _draw_ratio(
        ctx,
        "fill_ratio",
        valid_lo=0.35,
        valid_hi=0.90,
        default_lo=fill_lo,
        default_hi=fill_hi,
    )
    outside_fill_ratio = _draw_ratio(
        ctx,
        "outside_fill_ratio",
        valid_lo=0.30,
        valid_hi=0.85,
        default_lo=outside_lo,
        default_hi=outside_hi,
    )

    grid = full_grid(height, width, 0)
    draw_rect_outline(grid, frame_row, frame_col, frame_h, frame_w, 5)

    interior = [
        (row, col)
        for row in range(frame_row + 1, frame_row + frame_h - 1)
        for col in range(frame_col + 1, frame_col + frame_w - 1)
    ]
    interior_target = min(
        len(interior) - 1,
        max(5, round(len(interior) * fill_ratio)),
    )
    rng_interior = ctx.draw_rng("interior_texture")
    interior_boundary = [
        cell
        for cell in interior
        if cell[0] in {frame_row + 1, frame_row + frame_h - 2}
        or cell[1] in {frame_col + 1, frame_col + frame_w - 2}
    ]
    start = interior_boundary[rng_interior.randrange(len(interior_boundary))]
    painted_interior = _connected_cells(
        interior, [start], interior_target, rng_interior
    )
    interior_values = _unequal_color_sequence(
        len(painted_interior), colors, rng_interior
    )
    for (row, col), value in zip(painted_interior, interior_values):
        grid[row][col] = value

    zones = _outside_zones(
        height, width, frame_row, frame_col, frame_h, frame_w
    )
    if any(not cells for cells in zones.values()):
        raise ValueError("frame placement failed to leave all four exterior zones")
    bottom = frame_row + frame_h - 1
    right = frame_col + frame_w - 1
    rng_outside = ctx.draw_rng("outside_texture")
    starts = [
        (frame_row - 1, rng_outside.randint(frame_col, right)),
        (bottom + 1, rng_outside.randint(frame_col, right)),
        (rng_outside.randint(frame_row, bottom), frame_col - 1),
        (rng_outside.randint(frame_row, bottom), right + 1),
    ]
    outside = [cell for cells in zones.values() for cell in cells]
    outside_target = min(
        len(outside) - 1,
        max(8, round(len(outside) * outside_fill_ratio)),
    )
    painted_outside = _connected_cells(outside, starts, outside_target, rng_outside)
    outside_values = _balanced_color_sequence(
        len(painted_outside), colors, rng_outside
    )
    # Force both colors into multiple frame-adjacent witnesses before consuming
    # the randomized tail; the exact color order is irrelevant to the oracle.
    forced = [colors[0], colors[1], colors[0], colors[1]]
    for index, value in enumerate(forced):
        outside_values[index] = value
    rng_outside.shuffle(outside_values[4:])
    for (row, col), value in zip(painted_outside, outside_values):
        grid[row][col] = value

    return grid


def _grid_shape_errors(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], 0, 0
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], len(grid), width
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integer values in 0..9")
    return errors, len(grid), width


def _analysis(grid: Any) -> dict[str, Any]:
    errors, height, width = _grid_shape_errors(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "height": height,
        "width": width,
    }
    if errors:
        return result
    if not (8 <= height <= 22 and 8 <= width <= 22):
        errors.append(f"grid dimensions {height}x{width} outside 8..22")

    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        errors.append("expected one gray rectangular frame")
        return result
    top = min(row for row, _ in gray)
    bottom = max(row for row, _ in gray)
    left = min(col for _, col in gray)
    right = max(col for _, col in gray)
    frame_h = bottom - top + 1
    frame_w = right - left + 1
    result.update(
        {
            "bbox": (top, left, bottom, right),
            "frame_h": frame_h,
            "frame_w": frame_w,
        }
    )
    if frame_h < 5 or frame_w < 5:
        errors.append("gray frame must be at least 5x5")
    if top < 1 or left < 1 or bottom >= height - 1 or right >= width - 1:
        errors.append("gray frame must leave a nonempty exterior on all four sides")

    outline = (
        {(top, col) for col in range(left, right + 1)}
        | {(bottom, col) for col in range(left, right + 1)}
        | {(row, left) for row in range(top, bottom + 1)}
        | {(row, right) for row in range(top, bottom + 1)}
    )
    gray_set = set(gray)
    missing = outline - gray_set
    extra = gray_set - outline
    if missing:
        errors.append(f"gray frame outline is incomplete at {min(missing)}")
    if extra:
        errors.append(f"gray appears off the frame outline at {min(extra)}")

    interior_cells = [
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    ]
    interior_counter = Counter(grid[row][col] for row, col in interior_cells)
    interior_colors = sorted(
        color for color in interior_counter if color not in {0, 5}
    )
    result["interior_counter"] = dict(interior_counter)
    result["interior_colors"] = interior_colors
    if len(interior_colors) != 2:
        errors.append(
            "strict frame interior must contain exactly two nonzero non-gray colors"
        )
        return result
    color_a, color_b = interior_colors
    result["colors"] = (color_a, color_b)
    if interior_counter[0] < 1:
        errors.append("strict frame interior must include an unchanged zero witness")
    if min(interior_counter[color_a], interior_counter[color_b]) < 2:
        errors.append("each interior swap color must occur at least twice")
    if interior_counter[color_a] == interior_counter[color_b]:
        errors.append("interior swap-color counts must be unequal")

    palette = {value for row in grid for value in row}
    expected_palette = {0, 5, color_a, color_b}
    result["palette"] = sorted(palette)
    if palette != expected_palette:
        errors.append(
            f"full palette must be exactly {sorted(expected_palette)}, got {sorted(palette)}"
        )

    outside_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if not (top <= row <= bottom and left <= col <= right)
    ]
    outside_counter = Counter(grid[row][col] for row, col in outside_cells)
    result["outside_counter"] = dict(outside_counter)
    if min(outside_counter[color_a], outside_counter[color_b]) < 2:
        errors.append("both interior colors must have repeated unchanged witnesses outside")
    if outside_counter[0] < 1:
        errors.append("exterior must retain at least one background cell")
    outside_density = (
        (outside_counter[color_a] + outside_counter[color_b]) / len(outside_cells)
        if outside_cells
        else 0.0
    )
    result["outside_density"] = outside_density
    if not 0.25 <= outside_density <= 0.90:
        errors.append(
            f"exterior two-color texture density {outside_density:.3f} outside 0.25..0.90"
        )

    zones = _outside_zones(height, width, top, left, frame_h, frame_w)
    zone_witnesses = {
        name: sum(grid[row][col] in {color_a, color_b} for row, col in cells)
        for name, cells in zones.items()
    }
    result["zone_witnesses"] = zone_witnesses
    for name, count in zone_witnesses.items():
        if count < 1:
            errors.append(f"{name} exterior zone lacks a colored scoping witness")

    max_row = height - frame_h - 1
    max_col = width - frame_w - 1
    row_edge = top in {1, max_row}
    col_edge = left in {1, max_col}
    frame_anchor = (
        "corner"
        if row_edge and col_edge
        else "edge"
        if row_edge != col_edge
        else "interior"
    )
    palette_kind = (
        "canonical"
        if (color_a, color_b) in CANONICAL_COLOR_PAIRS
        else "broad"
    )
    result["frame_anchor"] = frame_anchor
    result["palette_kind"] = palette_kind
    return result


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or shortcut-friendly teaching scenes."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact non-float semantic axis from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "frame_h": analysis["frame_h"],
        "frame_w": analysis["frame_w"],
        "frame_anchor": analysis["frame_anchor"],
        "palette_kind": analysis["palette_kind"],
    }


def rule_mirror(grid):
    """Small test-only Python mirror; the Racket program remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    top, left, bottom, right = analysis["bbox"]
    color_a, color_b = analysis["colors"]
    output = [row[:] for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            value = grid[row][col]
            if value == color_a:
                output[row][col] = color_b
            elif value == color_b:
                output[row][col] = color_a
    return output
