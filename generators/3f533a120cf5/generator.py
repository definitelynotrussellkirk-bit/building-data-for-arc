"""Generator for ARC task 3f533a120cf5.

A connected gray (5) bitmap is paired with a horizontal legend.  The legend
contains one contiguous key sequence and one same-width separator-color bar.
The key may sit immediately above or below the separator; the whole legend may
sit above or below the bitmap.  The oracle crops the gray bitmap's bounding
box, paints each gray cell with the key color for that bitmap column, and
paints each zero inside the box with the separator color.

About 32% of default draws choose one complete canonical linked profile
(canvas dimensions, exact gray bitmap, key equality pattern, legend side,
key-row multiplicity, and gap) before varying colors and lawful translation.
The remaining draws generalize sizes, bitmap morphology, repeated-key layout,
legend side, and the oracle's above/below key-row branch.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f533a120cf5"
TASK_ID = "3f533a120cf5"
VERSION = "3.0.0"
RULE_HASH = "df7e059f3faa"
SUMMARY = (
    "Gray bitmap plus repeated-color column key and separator bar; crop the "
    "bitmap bbox, use the key color on gray cells, and separator color in "
    "bbox holes."
)

INVARIANTS = [
    "the gray cells form one 4-connected, non-rectangular bitmap whose bbox is 3..10 by 3..10",
    "every bitmap row and column contains gray, so its bbox is the output shape",
    "outside the bitmap is exactly one contiguous separator-color bar with the same width as the bitmap",
    "one to three identical contiguous key rows sit immediately above or below that separator bar",
    "the key has 2..5 distinct non-{0,5,separator} colors and at least one repeated column color",
    "the legend and bitmap are separated by 1..4 all-zero rows; all other cells are background 0",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "mask_height": {
        "type": "int",
        "default": "band-shaped 3..10; 32% complete canonical prior",
        "valid": "3..10",
    },
    "mask_width": {
        "type": "int",
        "default": "band-shaped 3..10; 32% complete canonical prior",
        "valid": "3..10",
    },
    "legend_side": {
        "type": "str",
        "default": "rng above|below",
        "valid": "above|below",
    },
    "key_side": {
        "type": "str",
        "default": "rng above|below relative to separator",
        "valid": "above|below",
    },
    "key_distinct_colors": {
        "type": "int",
        "default": "band-shaped 2..5, always < mask_width",
        "valid": "2..5",
    },
    "key_rows": {
        "type": "int",
        "default": "band-shaped 1..3",
        "valid": "1..3",
    },
    "gap_rows": {
        "type": "int",
        "default": "band-shaped 1..4",
        "valid": "1..4",
    },
    "separator_color": {
        "type": "color",
        "default": "rng excluding {0,5}",
        "valid": "1..4|6..9",
    },
}

_CANONICAL_PRIOR_P = 0.32

# Complete canonical morphology after quotienting only color renaming and
# independent lawful translation of the bitmap and legend.  Each entry is:
#   (canvas_h, canvas_w, bitmap_rows, abstract_key_pattern,
#    legend_side, key_side, key_rows, gap_rows)
# The exact bitmap and key equality pattern are answer-bearing and remain
# linked; they are never sampled independently on the canonical-prior path.
_CANONICAL_PROFILES = (
    (
        15,
        10,
        ("11100", "10100", "00111", "11101", "01001", "01111"),
        (0, 1, 2, 0, 0),
        "below",
        "above",
        2,
        2,
    ),
    (
        15,
        15,
        (
            "1001101",
            "1111111",
            "0011000",
            "1111111",
            "1101010",
            "0101111",
            "0101111",
            "1111111",
            "0001110",
            "1111011",
        ),
        (0, 0, 1, 2, 2, 3, 4),
        "above",
        "above",
        2,
        1,
    ),
    (
        15,
        16,
        ("10111111", "11010001", "01111011", "01000011", "01111111"),
        (0, 0, 1, 2, 2, 2, 3, 3),
        "below",
        "above",
        2,
        3,
    ),
    (
        18,
        18,
        (
            "0110010111",
            "1111111111",
            "0010110011",
            "1111100010",
            "0100100110",
            "0111111111",
            "0011000011",
        ),
        (0, 1, 1, 1, 2, 2, 3, 3, 4, 4),
        "above",
        "above",
        2,
        2,
    ),
)

_CANONICAL_SIGNATURES = frozenset(
    (
        h,
        w,
        bitmap,
        key_pattern,
        legend_side,
        key_side,
        key_rows,
        gap_rows,
    )
    for (
        h,
        w,
        bitmap,
        key_pattern,
        legend_side,
        key_side,
        key_rows,
        gap_rows,
    ) in _CANONICAL_PROFILES
)

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in (
        "mask_height",
        "mask_width",
        "key_distinct_colors",
        "key_rows",
        "gap_rows",
        "separator_color",
    ):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    for label in ("legend_side", "key_side"):
        value = overrides.get(label)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{label} must be a string")


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped default with band-independent exact override bounds."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _is_connected(bitmap: list[list[int]]) -> bool:
    cells = {
        (r, c)
        for r, row in enumerate(bitmap)
        for c, value in enumerate(row)
        if value
    }
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _draw_bitmap(mh: int, mw: int, rng, band: str) -> tuple[str, ...]:
    """Carve a connected non-rectangular bitmap with full row/column support."""
    bitmap = [[1] * mw for _ in range(mh)]
    area = mh * mw
    if band == "easy":
        z_lo, z_hi = 1, max(1, area // 4)
    elif band == "hard":
        z_lo, z_hi = max(2, area // 3), max(2, area // 2)
    else:
        z_lo, z_hi = max(1, area // 5), max(2, (2 * area) // 5)
    max_removable = area - max(mh, mw) - 1
    target = min(max_removable, rng.randint(z_lo, z_hi))
    target = max(1, target)

    removed = 0
    candidates = [(r, c) for r in range(mh) for c in range(mw)]
    for _ in range(5):
        rng.shuffle(candidates)
        for r, c in candidates:
            if removed >= target:
                break
            if not bitmap[r][c]:
                continue
            if sum(bitmap[r]) <= 1:
                continue
            if sum(bitmap[rr][c] for rr in range(mh)) <= 1:
                continue
            bitmap[r][c] = 0
            if not _is_connected(bitmap):
                bitmap[r][c] = 1
                continue
            removed += 1
        if removed >= target:
            break
    if removed == 0:
        # A 3x3-or-larger full rectangle always permits removing a corner
        # while preserving all row/column support and 4-connectivity.
        bitmap[0][0] = 0
    return tuple("".join(str(value) for value in row) for row in bitmap)


def _partition_positive(total: int, parts: int, rng) -> list[int]:
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    bounds = [0, *cuts, total]
    return [bounds[i + 1] - bounds[i] for i in range(parts)]


def _draw_key_pattern(width: int, n_colors: int, rng, band: str) -> tuple[int, ...]:
    """Return an abstract key pattern using every label and at least one repeat."""
    if not 2 <= n_colors < width:
        raise ValueError("key_distinct_colors must be at least 2 and less than mask_width")
    use_runs = band == "easy" or rng.random() < (0.70 if band == "medium" else 0.45)
    labels = list(range(n_colors))
    rng.shuffle(labels)
    if use_runs:
        lengths = _partition_positive(width, n_colors, rng)
        pattern = [label for label, length in zip(labels, lengths) for _ in range(length)]
    else:
        pattern = labels + [rng.randrange(n_colors) for _ in range(width - n_colors)]
        rng.shuffle(pattern)
        # Avoid an accidental all-singleton-looking prefix and make the
        # repeated-color lesson visually explicit.
        if all(pattern[i] != pattern[i + 1] for i in range(width - 1)):
            repeated = next(
                label for label in range(n_colors) if pattern.count(label) > 1
            )
            first = pattern.index(repeated)
            second = pattern.index(repeated, first + 1)
            neighbor = first + 1 if first + 1 < width else first - 1
            pattern[neighbor], pattern[second] = pattern[second], pattern[neighbor]
    return tuple(pattern)


def _normalize_key_pattern(values: Iterable[int]) -> tuple[int, ...]:
    labels: dict[int, int] = {}
    normalized = []
    for value in values:
        if value not in labels:
            labels[value] = len(labels)
        normalized.append(labels[value])
    return tuple(normalized)


def _structure(grid) -> dict:
    """Parse one lawful input and return exact semantic observations.

    Raises ``ValueError`` with a concrete invariant failure.  The parser is
    intentionally stricter than the Racket rule's crash boundary so generated
    data cannot drift into visually unrelated inputs that merely execute.
    """
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("ragged grid")
    if not (7 <= h <= 30 and 5 <= w <= 24):
        raise ValueError(f"grid dimensions {h}x{w} outside 7..30 by 5..24")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be integer colors in 0..9")

    gray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not gray:
        raise ValueError("no gray bitmap cells")
    r1 = min(r for r, _ in gray)
    r2 = max(r for r, _ in gray)
    c1 = min(c for _, c in gray)
    c2 = max(c for _, c in gray)
    mh, mw = r2 - r1 + 1, c2 - c1 + 1
    if not (3 <= mh <= 10 and 3 <= mw <= 10):
        raise ValueError(f"gray bbox {mh}x{mw} outside 3..10")
    bitmap = [
        [1 if grid[r][c] == 5 else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    if any(sum(row) == 0 for row in bitmap):
        raise ValueError("gray bbox contains an empty row")
    if any(sum(bitmap[r][c] for r in range(mh)) == 0 for c in range(mw)):
        raise ValueError("gray bbox contains an empty column")
    if sum(map(sum, bitmap)) == mh * mw:
        raise ValueError("gray bitmap is a solid rectangle; at least one bbox hole is required")
    if not _is_connected(bitmap):
        raise ValueError("gray bitmap is not 4-connected")

    separator_candidates = []
    for r in range(h):
        if r1 <= r <= r2:
            continue
        nonzero = [(c, value) for c, value in enumerate(grid[r]) if value != 0]
        if not nonzero:
            continue
        cols = [c for c, _ in nonzero]
        values = [value for _, value in nonzero]
        if (
            len(cols) == mw
            and cols == list(range(cols[0], cols[0] + mw))
            and len(set(values)) == 1
            and values[0] not in (0, 5)
        ):
            separator_candidates.append((r, cols[0], values[0]))
    if len(separator_candidates) != 1:
        raise ValueError(
            f"expected exactly one same-width contiguous separator bar, got {len(separator_candidates)}"
        )
    sep_row, legend_c, sep_color = separator_candidates[0]

    def has_key_signal(row_index: int) -> bool:
        return 0 <= row_index < h and any(
            value != 0 and value != sep_color for value in grid[row_index]
        )

    if has_key_signal(sep_row - 1):
        key_row = sep_row - 1
        key_side = "above"
        step = -1
    elif has_key_signal(sep_row + 1):
        key_row = sep_row + 1
        key_side = "below"
        step = 1
    else:
        raise ValueError("separator has no adjacent key row")

    key_nonzero = [(c, value) for c, value in enumerate(grid[key_row]) if value != 0]
    key_cols = [c for c, _ in key_nonzero]
    key_values = [value for _, value in key_nonzero]
    if key_cols != list(range(legend_c, legend_c + mw)):
        raise ValueError("key row must be a contiguous same-width segment aligned with separator")
    if any(value in (0, 5, sep_color) for value in key_values):
        raise ValueError("key colors must exclude background, gray, and separator colors")
    n_key_colors = len(set(key_values))
    if not 2 <= n_key_colors <= 5:
        raise ValueError(f"key must contain 2..5 distinct colors, got {n_key_colors}")
    if n_key_colors >= mw:
        raise ValueError("key must repeat at least one column color")

    key_rows = 1
    rr = key_row + step
    while 0 <= rr < h and grid[rr] == grid[key_row]:
        key_rows += 1
        rr += step
    if not 1 <= key_rows <= 3:
        raise ValueError(f"expected 1..3 identical key rows, got {key_rows}")
    key_row_indices = [key_row + step * i for i in range(key_rows)]
    block_rows = [sep_row, *key_row_indices]
    if max(block_rows) < r1:
        legend_side = "above"
        gap_rows = r1 - max(block_rows) - 1
    elif min(block_rows) > r2:
        legend_side = "below"
        gap_rows = min(block_rows) - r2 - 1
    else:
        raise ValueError("legend overlaps the gray bitmap rows")
    if not 1 <= gap_rows <= 4:
        raise ValueError(f"legend/bitmap gap must be 1..4 rows, got {gap_rows}")

    allowed = set(gray)
    for c in range(legend_c, legend_c + mw):
        allowed.add((sep_row, c))
        for row_index in key_row_indices:
            allowed.add((row_index, c))
    stray = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in allowed
    ]
    if stray:
        raise ValueError(f"nonzero cells outside bitmap/legend grammar: {stray[:3]}")

    bitmap_rows = tuple("".join(str(value) for value in row) for row in bitmap)
    return {
        "grid_h": h,
        "grid_w": w,
        "mask_height": mh,
        "mask_width": mw,
        "mask_top": r1,
        "mask_left": c1,
        "bitmap": bitmap_rows,
        "legend_side": legend_side,
        "key_side": key_side,
        "key_distinct_colors": n_key_colors,
        "key_rows": key_rows,
        "gap_rows": gap_rows,
        "separator_color": sep_color,
        "separator_row": sep_row,
        "legend_left": legend_c,
        "key_values": tuple(key_values),
        "key_pattern": _normalize_key_pattern(key_values),
        "gray_cells": len(gray),
        "bbox_holes": mh * mw - len(gray),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete visual grammar, including canonical inputs."""
    try:
        _structure(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid) -> dict:
    """Exact semantic-axis observations derived from the returned grid."""
    info = _structure(grid)
    return {label: info[label] for label in AXES}


def canonical_profile_signature(grid):
    """Complete linked profile after quotienting only color and translation."""
    try:
        info = _structure(grid)
    except (TypeError, ValueError):
        return None
    return (
        info["grid_h"],
        info["grid_w"],
        info["bitmap"],
        info["key_pattern"],
        info["legend_side"],
        info["key_side"],
        info["key_rows"],
        info["gap_rows"],
    )


def _layout_grid(
    *,
    canvas_h: int,
    canvas_w: int,
    bitmap: tuple[str, ...],
    key_pattern: tuple[int, ...],
    key_colors: tuple[int, ...],
    separator_color: int,
    legend_side: str,
    key_side: str,
    key_rows: int,
    gap_rows: int,
    rng,
):
    mh, mw = len(bitmap), len(bitmap[0])
    legend_h = key_rows + 1
    core_h = mh + gap_rows + legend_h
    if canvas_h < core_h or canvas_w < mw:
        raise ValueError("canvas cannot fit bitmap and legend")

    extra_h = canvas_h - core_h
    top_margin = rng.randint(0, extra_h)
    if legend_side == "above":
        legend_top = top_margin
        mask_top = legend_top + legend_h + gap_rows
    else:
        mask_top = top_margin
        legend_top = mask_top + mh + gap_rows

    mask_left = rng.randint(0, canvas_w - mw)
    legend_left = rng.randint(0, canvas_w - mw)
    if canvas_w > mw and legend_left == mask_left and rng.random() < 0.75:
        choices = [c for c in range(canvas_w - mw + 1) if c != mask_left]
        legend_left = rng.choice(choices)

    if key_side == "above":
        key_row_indices = list(range(legend_top, legend_top + key_rows))
        sep_row = legend_top + key_rows
    else:
        sep_row = legend_top
        key_row_indices = list(range(legend_top + 1, legend_top + 1 + key_rows))

    grid = full_grid(canvas_h, canvas_w, 0)
    for r, row in enumerate(bitmap):
        for c, value in enumerate(row):
            if value == "1":
                grid[mask_top + r][mask_left + c] = 5
    actual_key = [key_colors[label] for label in key_pattern]
    for row_index in key_row_indices:
        for c, color in enumerate(actual_key):
            grid[row_index][legend_left + c] = color
    for c in range(mw):
        grid[sep_row][legend_left + c] = separator_color
    return grid


def _generate_canonical(ctx, profile, band: str):
    (
        canvas_h,
        canvas_w,
        bitmap,
        key_pattern,
        legend_side,
        key_side,
        key_rows,
        gap_rows,
    ) = profile
    mh, mw = len(bitmap), len(bitmap[0])
    n_key_colors = len(set(key_pattern))
    palette = ctx.draw_distinct_colors(
        f"canonical_palette|{band}",
        n=n_key_colors + 1,
        exclude={0, 5},
    )
    separator_color = palette[0]
    key_colors = palette[1:]

    # KRF-0004: every exact declared axis is recorded under its own keyed
    # label on the early-return path, and every value equals the returned grid.
    ctx.draw_int("mask_height", mh, mh)
    ctx.draw_int("mask_width", mw, mw)
    ctx.draw_choice("legend_side", [legend_side])
    ctx.draw_choice("key_side", [key_side])
    ctx.draw_int("key_distinct_colors", n_key_colors, n_key_colors)
    ctx.draw_int("key_rows", key_rows, key_rows)
    ctx.draw_int("gap_rows", gap_rows, gap_rows)
    ctx.draw_int("separator_color", separator_color, separator_color)

    return _layout_grid(
        canvas_h=canvas_h,
        canvas_w=canvas_w,
        bitmap=bitmap,
        key_pattern=key_pattern,
        key_colors=key_colors,
        separator_color=separator_color,
        legend_side=legend_side,
        key_side=key_side,
        key_rows=key_rows,
        gap_rows=gap_rows,
        rng=ctx.draw_rng(f"canonical_layout|{band}"),
    )


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
    band = difficulty or "medium"

    # Complete-profile prior is default-only. Any explicit semantic control
    # bypasses it so no override is accepted and then silently ignored.
    if not overrides and ctx.draw_rng(f"canonical_prior|{band}").random() < _CANONICAL_PRIOR_P:
        profile = ctx.draw_choice(
            f"canonical_profile|{band}",
            list(_CANONICAL_PROFILES),
        )
        return _generate_canonical(ctx, profile, band)

    if band == "easy":
        mh_lo, mh_hi = 3, 5
        mw_lo, mw_hi = 3, 5
        kr_lo, kr_hi = 2, 2
        gap_lo, gap_hi = 1, 2
        key_side_options = ["above", "above", "above", "below"]
    elif band == "hard":
        mh_lo, mh_hi = 6, 10
        mw_lo, mw_hi = 7, 10
        kr_lo, kr_hi = 1, 3
        gap_lo, gap_hi = 2, 4
        key_side_options = ["above", "below"]
    else:
        mh_lo, mh_hi = 4, 7
        mw_lo, mw_hi = 4, 8
        kr_lo, kr_hi = 1, 3
        gap_lo, gap_hi = 1, 3
        key_side_options = ["above", "above", "below"]

    requested_key_colors = overrides.get("key_distinct_colors")
    if requested_key_colors is not None and not 2 <= int(requested_key_colors) <= 5:
        raise ValueError("key_distinct_colors override outside 2..5")

    mh = _banded_int(ctx, overrides, "mask_height", mh_lo, mh_hi, 3, 10)
    if overrides.get("mask_width") is not None:
        mw = ctx.draw_int("mask_width", 3, 10)
    elif requested_key_colors is not None:
        # A repeated key requires width > distinct-color count.  Honor a
        # single explicit color-count override by drawing a feasible width.
        lower = max(3, int(requested_key_colors) + 1)
        mw = ctx.draw_int("mask_width", lower, 10)
    else:
        mw = ctx.draw_int("mask_width", mw_lo, mw_hi)

    if requested_key_colors is not None:
        n_key_colors = ctx.draw_int("key_distinct_colors", 2, 5)
        if n_key_colors >= mw:
            raise ValueError(
                "key_distinct_colors must be less than mask_width so a repeated key color is visible"
            )
    else:
        max_colors = min(5, mw - 1)
        if band == "easy":
            color_lo, color_hi = 2, min(3, max_colors)
        elif band == "hard":
            color_lo, color_hi = min(3, max_colors), max_colors
        else:
            color_lo, color_hi = 2, min(4, max_colors)
        n_key_colors = ctx.draw_int("key_distinct_colors", color_lo, color_hi)

    legend_side = ctx.draw_choice("legend_side", ["above", "below"])
    key_side = ctx.draw_choice("key_side", key_side_options)
    key_rows = _banded_int(ctx, overrides, "key_rows", kr_lo, kr_hi, 1, 3)
    gap_rows = _banded_int(ctx, overrides, "gap_rows", gap_lo, gap_hi, 1, 4)
    separator_color = ctx.draw_color("separator_color", exclude={0, 5})
    key_colors = ctx.draw_distinct_colors(
        "key_colors",
        n=n_key_colors,
        exclude={0, 5, separator_color},
    )

    shape_rng = ctx.draw_rng("bitmap_shape")
    bitmap = _draw_bitmap(mh, mw, shape_rng, band)
    key_pattern = _draw_key_pattern(
        mw,
        n_key_colors,
        ctx.draw_rng("key_pattern"),
        band,
    )

    legend_h = key_rows + 1
    core_h = mh + gap_rows + legend_h
    margin_rng = ctx.draw_rng("canvas_margins")
    if band == "easy":
        extra_h = margin_rng.randint(1, 4)
        extra_w = margin_rng.randint(2, 5)
    elif band == "hard":
        extra_h = margin_rng.randint(4, 10)
        extra_w = margin_rng.randint(4, 8)
    else:
        extra_h = margin_rng.randint(2, 7)
        extra_w = margin_rng.randint(3, 7)
    canvas_h = core_h + extra_h
    canvas_w = mw + extra_w

    return _layout_grid(
        canvas_h=canvas_h,
        canvas_w=canvas_w,
        bitmap=bitmap,
        key_pattern=key_pattern,
        key_colors=key_colors,
        separator_color=separator_color,
        legend_side=legend_side,
        key_side=key_side,
        key_rows=key_rows,
        gap_rows=gap_rows,
        rng=ctx.draw_rng("layout"),
    )
