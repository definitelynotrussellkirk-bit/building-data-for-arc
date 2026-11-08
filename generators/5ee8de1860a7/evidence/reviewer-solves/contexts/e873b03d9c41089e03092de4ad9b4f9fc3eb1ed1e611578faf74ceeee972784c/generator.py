"""Generator for ARC task fc754716 / 5ee8de1860a7.

The input contains exactly one nonzero interior cell.  The Racket oracle reads
that cell's color and returns a same-sized grid whose outer border is that
color and whose interior is zero.  A pinned 30% schedule stays on the exact
canonical profile; the remaining default draws follow a rotation-safe cycle
whose dimensions and colors do not repeat within a four-pair lesson and whose
marker is always off-center.  Thus every choice of query among four adjacent
samples leaves demonstrations that rebut fixed-size, fixed-color, and
center-only shortcuts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5ee8de1860a7"
TASK_ID = "5ee8de1860a7"
VERSION = "3.1.0"
RULE_HASH = "474fc5439247"

SUMMARY = (
    "Create a 3..15 by 3..15 zero-background grid containing exactly one "
    "nonzero marker in the interior.  The marker color is 1..9.  The output "
    "oracle discards the marker position, preserves the input dimensions, "
    "paints the complete outer border in the marker color, and leaves every "
    "interior output cell zero.  Thirty percent of default sample indices "
    "reproduce the strict demonstrated profile: one centered marker on one "
    "of the five canonical dimension/color profiles."
)

INVARIANTS = [
    "the grid is rectangular with height and width in 3..15",
    "background is color 0",
    "exactly one nonzero cell exists",
    "the sole marker is strictly inside the outer border",
    "the marker color is an integer in 1..9",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "30% canonical profile; otherwise rotation-safe cycle",
        "valid": "3..15",
    },
    "grid_w": {
        "type": "int",
        "default": "30% canonical profile; otherwise rotation-safe cycle",
        "valid": "3..15",
    },
    "fg_color": {
        "type": "color",
        "default": "canonical color prior or rotation-safe 4-color cycle",
        "valid": "1..9",
    },
    "marker_row": {
        "type": "int",
        "default": "centered canonical anchor or off-center scheduled position",
        "valid": "1..h-2",
    },
    "marker_col": {
        "type": "int",
        "default": "centered canonical anchor or off-center scheduled position",
        "valid": "1..w-2",
    },
}

# Exact linked profiles derived from all four train inputs and the held-out test
# input.  The color set is part of the strict empirical profile, not merely a
# broad one-marker superfamily.
_CANONICAL_PROFILES = (
    (5, 7, 1),
    (5, 3, 3),
    (5, 5, 6),
    (3, 3, 2),
    (9, 7, 8),
)
_CANONICAL_FG_COLORS = tuple(profile[2] for profile in _CANONICAL_PROFILES)
_CANONICAL_BY_BAND = {
    "easy": _CANONICAL_PROFILES[:4],
    "medium": _CANONICAL_PROFILES,
    "hard": (_CANONICAL_PROFILES[-1],),
}
_GENERAL_DIMENSIONS = {
    "easy": (4, 7),
    "medium": (5, 11),
    "hard": (8, 15),
}

# Finite declaration for every linked dimension/marker override that cannot be
# realized while keeping the marker strictly inside the grid.  Publishing the
# exact tuples lets the override checker distinguish intentional rejections
# from accidental multi-axis failures.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = tuple(
    {"grid_h": height, "marker_row": row}
    for height in range(3, 16)
    for row in range(1, 14)
    if row > height - 2
) + tuple(
    {"grid_w": width, "marker_col": col}
    for width in range(3, 16)
    for col in range(1, 14)
    if col > width - 2
)

_CANONICAL_DIMENSIONS = {(h, w) for h, w, _ in _CANONICAL_PROFILES}
_GENERAL_PROFILES = {
    band: tuple(
        (height, width)
        for height in range(lo, hi + 1)
        for width in range(lo, hi + 1)
        if (height, width) not in _CANONICAL_DIMENSIONS
    )
    for band, (lo, hi) in _GENERAL_DIMENSIONS.items()
}
# Deliberately disjoint from all five canonical colors.  With sample_index as
# the cycle coordinate, general draws within any four adjacent indices have
# distinct colors, while at most two canonical anchors can share a color.
_GENERAL_FG_COLORS = (4, 5, 7, 9)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "fg_color", "marker_row", "marker_col"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and not 3 <= value <= 15:
            raise ValueError(f"{name} must be in 3..15")
    color = overrides.get("fg_color")
    if color is not None and not 1 <= color <= 9:
        raise ValueError("fg_color must be in 1..9")
    for name in ("marker_row", "marker_col"):
        value = overrides.get(name)
        if value is not None and not 1 <= value <= 13:
            raise ValueError(f"{name} must be in 1..13")


def _record_exact(ctx, h, w, color, row, col):
    """Record every exact semantic axis on the canonical return path."""
    ctx.draw_int("grid_h", h, h)
    ctx.draw_int("grid_w", w, w)
    ctx.draw_choice("fg_color", [color])
    ctx.draw_int("marker_row", row, row)
    ctx.draw_int("marker_col", col, col)


def _canonical_profile(seed, sample_index, band):
    profiles = _CANONICAL_BY_BAND[band]
    return profiles[(seed + sample_index) % len(profiles)]


def _rotation_safe_general_profile(seed, sample_index, band):
    """Return one deterministic non-canonical profile for a default draw.

    The dimension and color cycles have periods of at least four and use the
    absolute sample index, so distinct general samples inside any four-index
    window cannot collide on either attribute.  Canonical dimensions/colors
    are excluded from these pools, preventing an intervening canonical anchor
    from creating a third equal demonstration.  The position pool omits the
    geometric center, while the 3/10 canonical schedule contains at most two
    anchors in any four-index window.
    """
    dimensions = _GENERAL_PROFILES[band]
    h, w = dimensions[(seed + sample_index) % len(dimensions)]
    color = _GENERAL_FG_COLORS[(seed + sample_index) % len(_GENERAL_FG_COLORS)]
    center = (h // 2, w // 2)
    positions = tuple(
        (row, col)
        for row in range(1, h - 1)
        for col in range(1, w - 1)
        if (row, col) != center
    )
    row, col = positions[(seed * 17 + sample_index) % len(positions)]
    return h, w, color, row, col


def _draw_default_color(ctx, seed, sample_index, band):
    """Choose a keyed exact color while guaranteeing demo color contrast.

    Materialized lessons start at sample index zero.  Indices one and two
    therefore exclude the canonical index-zero color, so the three demos can
    never support a fixed-color border shortcut.
    """
    if ctx.overrides.get("fg_color") is not None:
        return ctx.draw_color("fg_color", exclude={0})
    colors = list(range(1, 10))
    if sample_index % 10 in (1, 2):
        block_start = sample_index - (sample_index % 10)
        anchor = _canonical_profile(seed, block_start, band)[2]
        colors.remove(anchor)
    color = colors[(seed + sample_index) % len(colors)]
    return ctx.draw_choice("fg_color", [color])


def _draw_dimension(ctx, label, band_lo, band_hi, required_min):
    requested = ctx.overrides.get(label)
    if requested is not None:
        value = ctx.draw_int(label, 3, 15)
        if value < required_min:
            raise ValueError(
                f"{label}={value} cannot contain the requested interior marker; "
                f"need at least {required_min}"
            )
        return value
    lo = max(band_lo, required_min)
    hi = max(band_hi, lo)
    if hi > 15:
        raise ValueError(f"requested marker requires {label}>{15}")
    return ctx.draw_int(label, lo, hi)


def _scheduled_position(ctx, h, w, sample_index):
    """Cycle through separated positions before using one fully random slot.

    The seven non-canonical residues in each ten-sample block cover all four
    interior corners, two center-line displacements, and one random location.
    This makes a contiguous lesson rebut marker-position and center-only
    shortcuts without sacrificing a stable canonical-profile prior.
    """
    row_override = ctx.overrides.get("marker_row")
    col_override = ctx.overrides.get("marker_col")
    if row_override is not None:
        row = ctx.draw_int("marker_row", 1, h - 2)
    else:
        row = None
    if col_override is not None:
        col = ctx.draw_int("marker_col", 1, w - 2)
    else:
        col = None

    slot = sample_index % 7
    scheduled = (
        (1, 1),
        (h - 2, w - 2),
        (1, w - 2),
        (h - 2, 1),
        (h // 2, 1),
        (1, w // 2),
    )
    if row is None and col is None and slot == 6:
        row = ctx.draw_int("marker_row", 1, h - 2)
        col = ctx.draw_int("marker_col", 1, w - 2)
        return row, col

    fallback_row, fallback_col = scheduled[slot % len(scheduled)]
    if row is None:
        row = ctx.draw_int("marker_row", fallback_row, fallback_row)
    if col is None:
        col = ctx.draw_int("marker_col", fallback_col, fallback_col)
    return row, col


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"

    # A spaced deterministic 3/10 sample-index schedule makes the strict empirical
    # manifold stable in every band and in disjoint seed ranges.  Any exact
    # override exits this prior so the requested value is never silently inert.
    if not overrides and sample_index % 10 in (0, 4, 8):
        h, w, color = _canonical_profile(seed, sample_index, band)
        row, col = h // 2, w // 2
        _record_exact(ctx, h, w, color, row, col)
        grid = full_grid(h, w, 0)
        grid[row][col] = color
        return grid

    # Default non-canonical draws use a schedule with a simple local proof:
    # every four adjacent samples remain lesson-identifiable no matter which
    # one is selected as the query.  Exact overrides intentionally leave this
    # schedule and continue through the independent per-axis path below.
    if not overrides:
        h, w, color, row, col = _rotation_safe_general_profile(
            seed, sample_index, band
        )
        _record_exact(ctx, h, w, color, row, col)
        grid = full_grid(h, w, 0)
        grid[row][col] = color
        return grid

    row_request = overrides.get("marker_row")
    col_request = overrides.get("marker_col")
    required_h = (row_request + 2) if row_request is not None else 3
    required_w = (col_request + 2) if col_request is not None else 3
    band_lo, band_hi = _GENERAL_DIMENSIONS[band]
    h = _draw_dimension(ctx, "grid_h", band_lo, band_hi, required_h)
    w = _draw_dimension(ctx, "grid_w", band_lo, band_hi, required_w)
    color = _draw_default_color(ctx, seed, sample_index, band)
    row, col = _scheduled_position(ctx, h, w, sample_index)

    grid = full_grid(h, w, 0)
    grid[row][col] = color
    return grid


def observe_overrides(grid):
    """Derive every exact semantic axis directly from the returned grid."""
    h = len(grid)
    w = len(grid[0])
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    observed = {"grid_h": h, "grid_w": w}
    if len(markers) == 1:
        row, col, color = markers[0]
        observed.update(
            {"fg_color": color, "marker_row": row, "marker_col": col}
        )
    return observed


def _sole_marker(grid):
    """Return the (row, col, color) of the single nonzero cell, else None."""
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(markers) != 1:
        return None
    return markers[0]


def _rule_mirror(grid):
    """Diagnostic Python mirror of the canonical Racket rule (border paint)."""
    marker = _sole_marker(grid)
    if marker is None:
        raise ValueError("rule mirror requires exactly one nonzero marker")
    height, width = len(grid), len(grid[0])
    color = marker[2]
    return [
        [
            color
            if row in (0, height - 1) or col in (0, width - 1)
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


# --- Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md) ---


def strict_canonical_like(grid):
    """[] iff grid sits on the strict linked manifold: one of the five
    canonical (h, w, color) profiles with the marker exactly centered."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    row, col, color = _sole_marker(grid)
    reasons = []
    if (height, width, color) not in _CANONICAL_PROFILES:
        reasons.append(
            f"(h,w,color)=({height},{width},{color}) is not one of the five "
            "canonical profiles"
        )
    if (row, col) != (height // 2, width // 2):
        reasons.append(
            f"canonical inputs center the marker at ({height // 2},{width // 2}); "
            f"found ({row},{col})"
        )
    return reasons


def _lawful_marker(grid):
    """Sole interior marker of a grammar-lawful grid, else None (for witnesses)."""
    if self_check(grid):
        return None
    return _sole_marker(grid)


def _w_canonical_centered_profile(grid):
    return not strict_canonical_like(grid)


def _w_off_center_marker(grid):
    marker = _lawful_marker(grid)
    if marker is None:
        return False
    height, width = len(grid), len(grid[0])
    return (marker[0], marker[1]) != (height // 2, width // 2)


def _w_non_canonical_dims(grid):
    marker = _lawful_marker(grid)
    if marker is None:
        return False
    dims = (len(grid), len(grid[0]))
    return dims not in {(h, w) for h, w, _ in _CANONICAL_PROFILES}


def _w_non_canonical_color(grid):
    marker = _lawful_marker(grid)
    if marker is None:
        return False
    return marker[2] not in _CANONICAL_FG_COLORS


def _w_marker_on_interior_ring(grid):
    """Marker one cell away from the border — rebuts deep-interior priors."""
    marker = _lawful_marker(grid)
    if marker is None:
        return False
    height, width = len(grid), len(grid[0])
    row, col, _ = marker
    return row in (1, height - 2) or col in (1, width - 2)


def _canonical_profile_only_rival(grid):
    """Wrong shortcut: solve only the five demonstrated centered profiles.

    This fits every authoritative canonical pair but returns an all-zero grid
    for any lawful input outside that strict manifold.  It captures the shared
    failure behind the off-center, non-canonical-dimension, and
    non-canonical-color witnesses without pretending that the canonical-anchor
    and interior-ring predicates are themselves rival counterexamples.
    """
    if strict_canonical_like(grid) == []:
        return _rule_mirror(grid)
    return full_grid(len(grid), len(grid[0]), 0)


SEMANTIC_WITNESSES = {
    "canonical_centered_profile": _w_canonical_centered_profile,
    "off_center_marker": _w_off_center_marker,
    "non_canonical_dims": _w_non_canonical_dims,
    "non_canonical_color": _w_non_canonical_color,
    "marker_on_interior_ring": _w_marker_on_interior_ring,
}

BRANCH_WITNESSES = {
    "canonical_centered_profile",
    "marker_on_interior_ring",
}

SEMANTIC_RIVALS = {
    "canonical_profile_only": _canonical_profile_only_rival,
}

WITNESS_RIVALS = {
    "off_center_marker": ["canonical_profile_only"],
    "non_canonical_dims": ["canonical_profile_only"],
    "non_canonical_color": ["canonical_profile_only"],
}

CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """[] iff the demos rule out every competing rule that would answer the
    query differently: fixed border color, fixed output size, and a
    centered-marker-only gate (the documented rejected shortcuts)."""
    reasons = []
    demo_markers = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        grid = demo["input"]
        errors = self_check(grid)
        if errors:
            return [f"demo {index} input off-grammar: {errors[0]}"]
        if demo["output"] != _rule_mirror(grid):
            return [f"demo {index} output does not match the canonical rule"]
        row, col, color = _sole_marker(grid)
        demo_markers.append((len(grid), len(grid[0]), row, col, color))
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    q_grid = query["input"]
    errors = self_check(q_grid)
    if errors:
        return [f"query input off-grammar: {errors[0]}"]
    q_row, q_col, q_color = _sole_marker(q_grid)
    q_h, q_w = len(q_grid), len(q_grid[0])

    demo_colors = {color for _, _, _, _, color in demo_markers}
    if len(demo_colors) == 1 and q_color not in demo_colors:
        reasons.append(
            "fixed-border-color competitor consistent: every demo marker is "
            f"color {next(iter(demo_colors))} but the query marker is {q_color}"
        )
    demo_dims = {(h, w) for h, w, _, _, _ in demo_markers}
    if len(demo_dims) == 1 and (q_h, q_w) not in demo_dims:
        reasons.append(
            "fixed-output-size competitor consistent: every demo is "
            f"{next(iter(demo_dims))} but the query is ({q_h},{q_w})"
        )
    all_demos_centered = all(
        (row, col) == (h // 2, w // 2) for h, w, row, col, _ in demo_markers
    )
    if all_demos_centered and (q_row, q_col) != (q_h // 2, q_w // 2):
        reasons.append(
            "centered-marker-only competitor consistent: every demo marker is "
            "centered but the query marker is off-center"
        )
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = competitor(q_grid) != _rule_mirror(q_grid)
        except Exception as exc:  # pragma: no cover - defensive contract report
            reasons.append(
                f"{name} could not be evaluated: {type(exc).__name__}: {exc}"
            )
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"{name} fits every demonstration but changes the query answer"
            )
    return reasons


def self_check(grid, *, difficulty=None, meta=None):
    """Reject every scene outside the single-interior-marker task grammar."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    height = len(grid)
    errors = []
    if not 3 <= height <= 15 or not 3 <= width <= 15:
        errors.append("grid dimensions must both be in 3..15")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors in 0..9")
        return errors

    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one nonzero marker, found {len(markers)}")
    elif not (
        0 < markers[0][0] < height - 1
        and 0 < markers[0][1] < width - 1
    ):
        errors.append("the sole marker must be strictly inside the border")
    return errors
