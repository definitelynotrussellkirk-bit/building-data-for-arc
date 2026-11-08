"""Generator for ARC task f5e7cf8dc78d.

Each non-zero singleton is a colored row marker.  The canonical rule sorts the
markers by row and turns each marker into a framed horizontal band: the marker
row is filled, the band receives colored left/right sides, and the first/last
bands close against the top/bottom grid edge.  Marker columns are deliberately
varied because they are irrelevant to the transformation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5e7cf8dc78d"
VERSION = "3.0.0"  # exact override contract, canonical-linked prior, no degenerate branches
TASK_ID = "f5e7cf8dc78d"
RULE_HASH = "4480c3031a45"
SUMMARY = (
    "A 0-background grid contains 2-8 uniquely colored singleton markers on "
    "distinct interior rows.  Sorting markers by row defines horizontal bands; "
    "the oracle draws each marker color across its row and along that band's "
    "left/right borders, closing the first and last bands at the grid edges."
)

INVARIANTS = [
    "2-8 non-zero cells; every non-zero color occurs exactly once",
    "marker rows are distinct, interior, and have an exact minimum gap of 1-4",
    "marker columns are interior and vary independently of row/color order",
    "normal draws always make every framed-band branch observable",
]

COLUMN_PATTERNS = (
    "same_column",
    "ascending",
    "descending",
    "alternating_edges",
    "scrambled",
)
COLOR_ORDERS = ("ascending", "descending", "scrambled")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-linked; 35% canonical-like 15",
        "valid": "6..24",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-linked; 35% canonical-like 15",
        "valid": "6..24",
        "doc": "Grid width.",
    },
    "n_dots": {
        "type": "int",
        "default": "2-4 easy / 3-6 medium / 4-8 hard",
        "valid": "2..8",
        "doc": "Exact number of singleton row markers.",
    },
    "min_separation": {
        "type": "int",
        "default": "difficulty-linked",
        "valid": "1..4",
        "doc": "Exact minimum gap between consecutive marker rows.",
    },
    "column_pattern": {
        "type": "enum",
        "default": "rng; canonical-like draws use scrambled",
        "valid": "|".join(COLUMN_PATTERNS),
        "doc": "Recoverable marker-column pattern; columns never affect the rule.",
    },
    "color_order": {
        "type": "enum",
        "default": "rng; mostly scrambled in canonical-like draws",
        "valid": "|".join(COLOR_ORDERS),
        "doc": "Recoverable numeric color order after sorting markers by row.",
    },
}

_INT_RANGES = {
    "grid_h": (6, 24),
    "grid_w": (6, 24),
    "n_dots": (2, 8),
    "min_separation": (1, 4),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one lawful input grid; the Racket rule remains output authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    # Read numeric constraints only to choose a feasible joint domain.  The
    # selected values are still consumed and recorded through GenCtx below.
    requested = {
        name: _read_int_override(overrides, name, lo, hi)
        for name, (lo, hi) in _INT_RANGES.items()
    }
    _read_enum_override(overrides, "column_pattern", COLUMN_PATTERNS)
    _read_enum_override(overrides, "color_order", COLOR_ORDERS)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_like = not overrides and ctx.draw_rng("canonical_prior").random() < 0.35
    n_requested = requested["n_dots"]

    if canonical_like:
        column_pattern = ctx.draw_choice("column_pattern", ["scrambled"])
        preferred_color_orders = ["scrambled", "scrambled", "scrambled", "ascending"]
        chosen_color_order = ctx.draw_rng("canonical_color_order").choice(
            preferred_color_orders
        )
        color_order = ctx.draw_choice("color_order", [chosen_color_order])
    else:
        column_options = list(COLUMN_PATTERNS)
        color_options = list(COLOR_ORDERS)
        # A two-marker sequence cannot be non-monotone.  When n_dots=2 is the
        # only explicit request, choose a compatible mode; an explicitly
        # incompatible pair is rejected later as a multi-override conflict.
        if n_requested == 2 and "column_pattern" not in overrides:
            column_options.remove("scrambled")
        if n_requested == 2 and "color_order" not in overrides:
            color_options.remove("scrambled")
        column_pattern = ctx.draw_choice("column_pattern", column_options)
        color_order = ctx.draw_choice("color_order", color_options)

    min_n = 3 if "scrambled" in (column_pattern, color_order) else 2
    h, n_dots, min_separation = _choose_layout(
        ctx,
        difficulty=difficulty,
        requested=requested,
        min_n=min_n,
        canonical_like=canonical_like,
    )

    if canonical_like:
        w = ctx.draw_int("grid_w", 15, 15)
    elif requested["grid_w"] is not None:
        w = ctx.draw_int("grid_w", 6, 24)
    else:
        w = ctx.draw_int_diff("grid_w", 6, 24)

    rows = _pick_rows_exact(
        ctx.draw_rng("rows"), h, n_dots, min_separation
    )
    colors = _pick_colors(ctx.draw_rng("colors"), n_dots, color_order)
    columns = _pick_columns(
        ctx.draw_rng(f"columns:{column_pattern}"),
        w,
        n_dots,
        column_pattern,
    )

    grid = full_grid(h, w, 0)
    for row, col, color in zip(rows, columns, colors):
        grid[row][col] = color
    return grid


def _read_int_override(overrides, name, lo, hi):
    if name not in overrides or overrides[name] is None:
        return None
    raw = overrides[name]
    if isinstance(raw, bool):
        raise ValueError(f"{name} override must be an integer, not bool")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    return value


def _read_enum_override(overrides, name, options):
    if name not in overrides or overrides[name] is None:
        return None
    value = overrides[name]
    if value not in options:
        raise ValueError(
            f"{name} override {value!r} not in {', '.join(options)}"
        )
    return value


def _difficulty_ranges(difficulty):
    if difficulty == "easy" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) < 0.34
    ):
        return range(6, 13), range(2, 5), range(2, 5)
    if difficulty == "hard" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) > 0.66
    ):
        return range(15, 25), range(4, 9), range(1, 4)
    if difficulty == "medium":
        return range(10, 19), range(3, 7), range(1, 4)
    return range(8, 21), range(2, 8), range(1, 5)


def _choose_layout(ctx, *, difficulty, requested, min_n, canonical_like):
    """Choose a feasible (height, count, exact minimum gap) before drawing.

    No requested value is clamped or replaced.  Single-axis overrides always
    have a feasible witness; incompatible multi-axis combinations raise a
    descriptive ValueError, which is the explicit override contract.
    """
    all_candidates = [
        (h, n, sep)
        for h in range(6, 25)
        for n in range(max(2, min_n), 9)
        for sep in range(1, 5)
        if h >= 3 + (n - 1) * sep
        and (requested["grid_h"] is None or h == requested["grid_h"])
        and (requested["n_dots"] is None or n == requested["n_dots"])
        and (
            requested["min_separation"] is None
            or sep == requested["min_separation"]
        )
    ]
    if not all_candidates:
        explicit = ", ".join(
            f"{key}={value!r}"
            for key, value in requested.items()
            if key != "grid_w" and value is not None
        )
        mode_note = "scrambled modes require n_dots>=3" if min_n == 3 else ""
        detail = "; ".join(part for part in (explicit, mode_note) if part)
        raise ValueError(
            "incompatible overrides: no 6..24 grid can realize 2..8 markers "
            f"with exact row gap 1..4 ({detail})"
        )

    if canonical_like:
        candidates = [
            item
            for item in all_candidates
            if item[0] == 15 and item[1] in (3, 4) and item[2] in (2, 3, 4)
        ]
    else:
        h_pref, n_pref, sep_pref = _difficulty_ranges(difficulty)
        candidates = [
            item
            for item in all_candidates
            if item[0] in h_pref and item[1] in n_pref and item[2] in sep_pref
        ]
    if not candidates:
        candidates = all_candidates

    h_value, n_value, sep_value = ctx.draw_rng("layout_tuple").choice(candidates)
    h = ctx.draw_int("grid_h", h_value, h_value)
    n_dots = ctx.draw_int("n_dots", n_value, n_value)
    min_separation = ctx.draw_int(
        "min_separation", sep_value, sep_value
    )
    return h, n_dots, min_separation


def _pick_rows_exact(rng, h, n, separation):
    """Interior rows whose realized minimum consecutive gap is exactly sep."""
    slack = h - 3 - (n - 1) * separation
    if slack < 0:
        raise ValueError(
            f"cannot place {n} interior rows at gap {separation} in height {h}"
        )

    # Gaps: top slack, n-1 internal extras, bottom slack.  Keep one internal
    # extra at zero so the declared minimum is realized exactly, while
    # distributing all remaining slack without retries or fallbacks.
    extras = [0] * (n + 1)
    tight_gap = rng.randrange(n - 1)
    buckets = [0, n] + [
        index + 1 for index in range(n - 1) if index != tight_gap
    ]
    for _ in range(slack):
        extras[rng.choice(buckets)] += 1

    row = 1 + extras[0]
    rows = [row]
    for index in range(n - 1):
        row += separation + extras[index + 1]
        rows.append(row)
    return rows


def _pick_colors(rng, n, order):
    colors = sorted(rng.sample(range(1, 10), n))
    if order == "ascending":
        return colors
    if order == "descending":
        return list(reversed(colors))
    rng.shuffle(colors)
    if _strictly_increasing(colors) or _strictly_decreasing(colors):
        colors[0], colors[1] = colors[1], colors[0]
    return colors


def _pick_columns(rng, w, n, pattern):
    if pattern == "same_column":
        col = rng.randint(1, w - 2)
        return [col] * n
    if pattern == "alternating_edges":
        return [1 if index % 2 == 0 else w - 2 for index in range(n)]
    if pattern == "ascending":
        # Start at 2 rather than 1 so n=2 remains distinguishable from the
        # alternating_edges witness [1, w-2].
        return [2 + (index * (w - 4)) // (n - 1) for index in range(n)]
    if pattern == "descending":
        return list(reversed(
            [2 + (index * (w - 4)) // (n - 1) for index in range(n)]
        ))

    columns = [rng.randint(1, w - 2) for _ in range(n)]
    center = max(2, min(w - 3, w // 2))
    columns[:3] = [center, w - 2, 1]
    return columns


def _strictly_increasing(values):
    return all(left < right for left, right in zip(values, values[1:]))


def _strictly_decreasing(values):
    return all(left > right for left, right in zip(values, values[1:]))


def _classify_column_pattern(columns, width):
    if len(set(columns)) == 1:
        return "same_column"
    alternating = [
        1 if index % 2 == 0 else width - 2
        for index in range(len(columns))
    ]
    if columns == alternating:
        return "alternating_edges"
    if all(a <= b for a, b in zip(columns, columns[1:])):
        return "ascending"
    if all(a >= b for a, b in zip(columns, columns[1:])):
        return "descending"
    return "scrambled"


def _classify_color_order(colors):
    if _strictly_increasing(colors):
        return "ascending"
    if _strictly_decreasing(colors):
        return "descending"
    return "scrambled"


def observe_overrides(grid) -> dict:
    """Recover the exact semantic axes represented by a returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    width = len(grid[0])
    cells = sorted(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )
    rows = [row for row, _, _ in cells]
    columns = [col for _, col, _ in cells]
    colors = [value for _, _, value in cells]
    gaps = [right - left for left, right in zip(rows, rows[1:])]
    return {
        "n_dots": len(cells),
        "min_separation": min(gaps) if gaps else 0,
        "column_pattern": _classify_column_pattern(columns, width)
        if len(columns) >= 2
        else "invalid",
        "color_order": _classify_color_order(colors)
        if len(colors) >= 2
        else "invalid",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, not merely invalid palettes."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]

    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    if not 6 <= h <= 24 or not 6 <= w <= 24:
        errors.append(f"grid dimensions {h}x{w} outside 6..24")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer colors 0..9")
        return errors

    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not 2 <= len(cells) <= 8:
        errors.append(f"expected 2..8 singleton markers, found {len(cells)}")

    counts: dict[int, int] = {}
    for _, _, color in cells:
        counts[color] = counts.get(color, 0) + 1
    repeated = sorted(color for color, count in counts.items() if count != 1)
    if repeated:
        errors.append(f"every marker color must occur once; repeated {repeated}")

    rows = sorted(row for row, _, _ in cells)
    if len(rows) != len(set(rows)):
        errors.append("markers must occupy distinct rows")
    gaps = [right - left for left, right in zip(rows, rows[1:])]
    if gaps and not 1 <= min(gaps) <= 4:
        errors.append(
            f"realized minimum row gap {min(gaps)} outside declared 1..4"
        )
    if any(row in (0, h - 1) for row, _, _ in cells):
        errors.append("marker rows must be interior so both closure branches teach")
    if any(col in (0, w - 1) for _, col, _ in cells):
        errors.append("marker columns must be interior")

    observed = observe_overrides(grid)
    if observed.get("column_pattern") not in COLUMN_PATTERNS:
        errors.append("marker columns do not realize a declared column pattern")
    if observed.get("color_order") not in COLOR_ORDERS:
        errors.append("marker colors do not realize a declared color order")

    if isinstance(meta, dict):
        explicit = meta.get("overrides")
        if not isinstance(explicit, dict):
            explicit = meta
        for axis in (
            "n_dots",
            "min_separation",
            "column_pattern",
            "color_order",
        ):
            if axis in explicit and explicit[axis] is not None:
                requested_value = explicit[axis]
                if axis in ("n_dots", "min_separation"):
                    requested_value = int(requested_value)
                if observed.get(axis) != requested_value:
                    errors.append(
                        f"{axis} requested {requested_value!r}, "
                        f"observed {observed.get(axis)!r}"
                    )
    return errors
