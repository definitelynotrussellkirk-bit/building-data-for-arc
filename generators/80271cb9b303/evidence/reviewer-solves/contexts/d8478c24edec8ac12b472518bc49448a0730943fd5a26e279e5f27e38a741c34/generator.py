"""Generator for ARC task d8c310e9 — extend a horizontal periodic tile.

Every non-empty row shows a prefix of a period that is aligned to column zero.
The visible prefix may end partway through a repeat, so the rightmost non-zero
cell is a delimiter, not necessarily the end of the period.  The Racket oracle
finds the smallest row period compatible with columns 0..R and tiles that
period through the right edge.  Empty rows stay empty.

The three-sample schedule deliberately includes a canonical-scale stacked
motif, a partial-cutoff/leading-zero scene, and an aligned-cutoff scene with a
different period.  Consequently each materialized lesson refutes identity,
last-color fill, fixed-period, first-nonzero anchoring, first-row copying, and
"repeat the whole visible prefix" shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80271cb9b303"
TASK_ID = "80271cb9b303"
VERSION = "3.1.0"  # enforce the declared 4,3,5..6 lesson-period curriculum
RULE_HASH = "4cb32d01d908"

SUMMARY = (
    "A 0-background grid contains 2-4 non-empty rows that are prefixes of one "
    "horizontal tile period, aligned to column 0.  For each non-empty row, find "
    "its rightmost non-zero cell R and the smallest period p consistent with "
    "columns 0..R, then continue that period through the right edge.  Prefixes "
    "may end either on a period boundary or partway through a repeat, may begin "
    "with zero cells, and different rows carry different color patterns.  Empty "
    "rows remain zero."
)

INVARIANTS = [
    "background is 0 and at least one all-zero row remains",
    "there are 2-4 active rows in one of four observable row layouts",
    "all active rows have the same smallest period p in 3..6",
    "each visible prefix contains at least one repeated residue but stops before the right edge",
    "the oracle changes at least one tail cell in every active row",
    "the scene uses exactly 2-4 non-zero colors from one declared palette family",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

ROW_LAYOUTS = ("top_block", "bottom_block", "edge_split", "alternating")
CUTOFF_STYLES = ("aligned", "partial", "mixed")
LEADING_ZERO_STYLES = ("all_zero", "all_nonzero", "mixed")
PALETTE_FAMILIES = ("canonical", "broad")
_CANONICAL_COLORS = (1, 2, 3, 4, 6)
_BROAD_COLORS = (5, 7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "slot 0 anchors 5; otherwise difficulty-aware 5..14",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "slot 0 anchors 15; otherwise difficulty-aware 14..22",
        "valid": "14..22",
    },
    "n_active_rows": {
        "type": "int",
        "default": "slot 0 anchors 3; otherwise rng 2..4",
        "valid": "2..4",
    },
    "period": {
        "type": "int",
        "default": "three-sample schedule: 4, 3, then 5..6",
        "valid": "3..6",
    },
    "cutoff_style": {
        "type": "str",
        "default": "three-sample schedule: mixed, partial, aligned",
        "valid": "aligned|partial|mixed",
    },
    "leading_zero_style": {
        "type": "str",
        "default": "three-sample schedule: mixed, all_zero, all_nonzero",
        "valid": "all_zero|all_nonzero|mixed",
    },
    "row_layout": {
        "type": "str",
        "default": "slot 0 bottom_block; otherwise rng",
        "valid": "top_block|bottom_block|edge_split|alternating",
    },
    "palette_size": {
        "type": "int",
        "default": "slot 0 anchors 3; otherwise rng 2..4 non-zero colors",
        "valid": "2..4",
    },
    "palette_family": {
        "type": "str",
        "default": "slot 0 canonical; otherwise rng canonical|broad",
        "valid": "canonical|broad",
    },
}


def _minimal_row_period(row: list[int], upto: int) -> int | None:
    """Smallest period compatible with row[0:upto+1], matching the oracle."""
    for period in range(1, upto + 2):
        if all(row[col] == row[col % period] for col in range(upto + 1)):
            return period
    return None


def _active_rows(grid: list[list[int]]) -> list[int]:
    return [index for index, row in enumerate(grid) if any(value != 0 for value in row)]


def _row_layout_rows(layout: str, height: int, count: int) -> tuple[int, ...]:
    if layout == "top_block":
        rows = list(range(count))
    elif layout == "bottom_block":
        rows = list(range(height - count, height))
    elif layout == "edge_split":
        order: list[int] = []
        for offset in range(height):
            candidate = offset // 2 if offset % 2 == 0 else height - 1 - offset // 2
            if candidate not in order:
                order.append(candidate)
        rows = order[:count]
    elif layout == "alternating":
        order = list(range(0, height, 2)) + list(range(1, height, 2))
        rows = order[:count]
    else:
        raise ValueError(f"unknown row_layout {layout!r}")
    return tuple(sorted(rows))


def _observe_row_layout(height: int, rows: list[int]) -> str:
    matches = [
        layout
        for layout in ROW_LAYOUTS
        if _row_layout_rows(layout, height, len(rows)) == tuple(rows)
    ]
    return matches[0] if len(matches) == 1 else "ambiguous_or_invalid"


def _style_flags(style: str, count: int, *, rng) -> list[bool]:
    """Return booleans for a two-valued all/none/mixed style."""
    if style in {"all_zero", "aligned"}:
        return [True] * count
    if style in {"all_nonzero", "partial"}:
        return [False] * count
    if style != "mixed":
        raise ValueError(f"unknown style {style!r}")
    flags = [True, False] + [rng.choice((True, False)) for _ in range(count - 2)]
    rng.shuffle(flags)
    return flags


def _draw_int_axis(ctx, overrides, name: str, lo: int, hi: int, *, fixed=None, diff=False):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    if fixed is not None:
        return ctx.draw_int(name, int(fixed), int(fixed))
    return ctx.draw_int_diff(name, lo, hi) if diff else ctx.draw_int(name, lo, hi)


def _draw_choice_axis(ctx, overrides, name: str, options, *, fixed=None):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    if fixed is not None:
        return ctx.draw_choice(name, (fixed,))
    return ctx.draw_choice(name, options)


def _tail_changes(pattern: list[int], right: int, width: int) -> bool:
    period = len(pattern)
    return any(pattern[col % period] != 0 for col in range(right + 1, width))


def _build_patterns(
    *,
    period: int,
    width: int,
    palette: list[int],
    starts_zero: list[bool],
    aligned_cutoffs: list[bool],
    rng,
) -> tuple[list[list[int]], list[int]]:
    """Construct minimal-period row patterns and rightmost visible positions."""
    for _attempt in range(5000):
        patterns: list[list[int]] = []
        rights: list[int] = []
        for row_index, (starts_with_zero, is_aligned) in enumerate(
            zip(starts_zero, aligned_cutoffs)
        ):
            if is_aligned:
                phase = period - 1
            else:
                phase_options = list(range(0 if not starts_with_zero else 1, period - 1))
                phase = rng.choice(phase_options)

            pattern = [rng.choice([0, *palette]) for _ in range(period)]
            pattern[0] = 0 if starts_with_zero else rng.choice(palette)
            pattern[phase] = rng.choice(palette)

            # Force row-to-row variation without assigning semantic meaning to color.
            if row_index and pattern == patterns[0]:
                tweak = 1 if period > 1 else 0
                pattern[tweak] = rng.choice(palette)

            right = (2 * period - 1) if is_aligned else (period + phase)
            if right >= width - 1:
                break
            probe = [pattern[col % period] for col in range(right + 1)]
            if _minimal_row_period(probe, right) != period:
                break
            if not _tail_changes(pattern, right, width):
                break
            patterns.append(pattern)
            rights.append(right)
        else:
            if set(palette) <= {value for pattern in patterns for value in pattern}:
                return patterns, rights
    raise RuntimeError("could not construct an exact observable periodic-prefix scene")


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover every exact semantic axis from a returned grid."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    rows = _active_rows(grid) if grid and width else []
    periods: list[int] = []
    aligned: list[bool] = []
    leading_zero: list[bool] = []
    for row_index in rows:
        row = grid[row_index]
        right = max(col for col, value in enumerate(row) if value != 0)
        period = _minimal_row_period(row, right)
        periods.append(period if period is not None else -1)
        aligned.append(period is not None and (right + 1) % period == 0)
        leading_zero.append(row[0] == 0)

    period_value = periods[0] if periods and len(set(periods)) == 1 else -1
    if aligned and all(aligned):
        cutoff_style = "aligned"
    elif aligned and not any(aligned):
        cutoff_style = "partial"
    elif aligned:
        cutoff_style = "mixed"
    else:
        cutoff_style = "invalid"

    if leading_zero and all(leading_zero):
        leading_style = "all_zero"
    elif leading_zero and not any(leading_zero):
        leading_style = "all_nonzero"
    elif leading_zero:
        leading_style = "mixed"
    else:
        leading_style = "invalid"

    colors = {value for row in grid for value in row if value != 0}
    if colors and colors <= set(_CANONICAL_COLORS):
        palette_family = "canonical"
    elif colors and colors <= set(_BROAD_COLORS):
        palette_family = "broad"
    else:
        palette_family = "mixed_or_invalid"

    return {
        "grid_h": height,
        "grid_w": width,
        "n_active_rows": len(rows),
        "period": period_value,
        "cutoff_style": cutoff_style,
        "leading_zero_style": leading_style,
        "row_layout": _observe_row_layout(height, rows) if rows else "invalid",
        "palette_size": len(colors),
        "palette_family": palette_family,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lesson grammar and reject rule-hiding impostors."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors

    rows = _active_rows(grid)
    if not 2 <= len(rows) <= 4:
        errors.append(f"expected 2-4 active rows, found {len(rows)}")
    if len(rows) >= height:
        errors.append("expected at least one all-zero row")

    periods: list[int] = []
    for row_index in rows:
        row = grid[row_index]
        right = max(col for col, value in enumerate(row) if value != 0)
        if right >= width - 1:
            errors.append(f"row {row_index} reaches the right edge; extension branch hidden")
            continue
        period = _minimal_row_period(row, right)
        if period is None:
            errors.append(f"row {row_index} has no inferable period")
            continue
        periods.append(period)
        if not 3 <= period <= 6:
            errors.append(f"row {row_index} has period {period}; expected 3..6")
        if right < period:
            errors.append(
                f"row {row_index} exposes no repeated residue for period {period}"
            )
        if not any(row[col % period] != 0 for col in range(right + 1, width)):
            errors.append(f"row {row_index} has an all-zero extension tail")
        if any(row[col] != row[col % period] for col in range(right + 1)):
            errors.append(f"row {row_index} contradicts its inferred period {period}")

    if periods and len(set(periods)) != 1:
        errors.append(f"active rows do not share one period: {sorted(set(periods))}")

    observed = observe_overrides(grid)
    if observed["row_layout"] not in ROW_LAYOUTS:
        errors.append("active rows do not realize one declared row_layout")
    if observed["cutoff_style"] not in CUTOFF_STYLES:
        errors.append("cutoffs do not realize one declared cutoff_style")
    if observed["leading_zero_style"] not in LEADING_ZERO_STYLES:
        errors.append("row starts do not realize one declared leading_zero_style")
    if not 2 <= observed["palette_size"] <= 4:
        errors.append(
            f"expected 2-4 non-zero colors, found {observed['palette_size']}"
        )
    if observed["palette_family"] not in PALETTE_FAMILIES:
        errors.append("non-zero colors mix palette families")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the official 5x15, bottom-stacked, canonical-palette manifold."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    observed = observe_overrides(grid)
    reasons: list[str] = []
    if (observed["grid_h"], observed["grid_w"]) != (5, 15):
        reasons.append("canonical dimensions are exactly 5x15")
    if observed["row_layout"] != "bottom_block":
        reasons.append("canonical active rows form a bottom block")
    if observed["n_active_rows"] not in (2, 3):
        reasons.append("canonical scenes contain 2 or 3 active rows")
    if observed["palette_size"] not in (2, 3):
        reasons.append("canonical scenes use 2 or 3 non-zero colors")
    if observed["palette_family"] != "canonical":
        reasons.append("canonical scenes use only colors 1,2,3,4,6")
    return reasons


def _solve_true(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for row_index in _active_rows(grid):
        row = grid[row_index]
        right = max(col for col, value in enumerate(row) if value != 0)
        period = _minimal_row_period(row, right)
        if period is None:
            continue
        output[row_index] = [row[col % period] for col in range(len(row))]
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _last_nonzero_fill(grid):
    output = [list(row) for row in grid]
    for row_index in _active_rows(grid):
        row = grid[row_index]
        right = max(col for col, value in enumerate(row) if value != 0)
        output[row_index] = row[: right + 1] + [row[right]] * (len(row) - right - 1)
    return output


def _fixed_period(grid, period: int):
    output = [list(row) for row in grid]
    for row_index in _active_rows(grid):
        row = grid[row_index]
        output[row_index] = [row[col % period] for col in range(len(row))]
    return output


def _repeat_visible_prefix(grid):
    output = [list(row) for row in grid]
    for row_index in _active_rows(grid):
        row = grid[row_index]
        right = max(col for col, value in enumerate(row) if value != 0)
        block = row[: right + 1]
        output[row_index] = [block[col % len(block)] for col in range(len(row))]
    return output


def _first_nonzero_anchor(grid):
    """Wrong rival: treat leading zeros as margin and shift the motif to col 0."""
    output = [list(row) for row in grid]
    for row_index in _active_rows(grid):
        row = grid[row_index]
        left = next(col for col, value in enumerate(row) if value != 0)
        right = max(col for col, value in enumerate(row) if value != 0)
        segment = row[left : right + 1]
        period = _minimal_row_period(segment, len(segment) - 1) or len(segment)
        output[row_index] = [segment[col % period] for col in range(len(row))]
    return output


def _copy_first_active_pattern(grid):
    output = [list(row) for row in grid]
    rows = _active_rows(grid)
    if not rows:
        return output
    solved = _solve_true(grid)
    template = solved[rows[0]]
    for row_index in rows:
        output[row_index] = list(template)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "last_nonzero_fill": _last_nonzero_fill,
    "fixed_period_3": lambda grid: _fixed_period(grid, 3),
    "fixed_period_4": lambda grid: _fixed_period(grid, 4),
    "repeat_visible_prefix": _repeat_visible_prefix,
    "first_nonzero_anchor": _first_nonzero_anchor,
    "copy_first_active_pattern": _copy_first_active_pattern,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _lawful_and_differs(grid, rival_name: str, predicate=lambda _observed: True) -> bool:
    if self_check(grid):
        return False
    observed = observe_overrides(grid)
    return bool(predicate(observed)) and _solve_true(grid) != SEMANTIC_RIVALS[rival_name](grid)


SEMANTIC_WITNESSES = {
    "non_identity_tail": lambda grid: _lawful_and_differs(grid, "identity"),
    "partial_cutoff_refutes_visible_block": lambda grid: _lawful_and_differs(
        grid,
        "repeat_visible_prefix",
        lambda observed: observed["cutoff_style"] in {"partial", "mixed"},
    ),
    "leading_zero_refutes_first_nonzero_anchor": lambda grid: _lawful_and_differs(
        grid,
        "first_nonzero_anchor",
        lambda observed: observed["leading_zero_style"] in {"all_zero", "mixed"},
    ),
    "row_specific_patterns": lambda grid: _lawful_and_differs(
        grid, "copy_first_active_pattern"
    ),
    "period_not_three": lambda grid: _lawful_and_differs(
        grid, "fixed_period_3", lambda observed: observed["period"] != 3
    ),
    "period_not_four": lambda grid: _lawful_and_differs(
        grid, "fixed_period_4", lambda observed: observed["period"] != 4
    ),
    "not_last_color_fill": lambda grid: _lawful_and_differs(
        grid, "last_nonzero_fill"
    ),
}

WITNESS_RIVALS = {
    "non_identity_tail": ["identity"],
    "partial_cutoff_refutes_visible_block": ["repeat_visible_prefix"],
    "leading_zero_refutes_first_nonzero_anchor": ["first_nonzero_anchor"],
    "row_specific_patterns": ["copy_first_active_pattern"],
    "period_not_three": ["fixed_period_3"],
    "period_not_four": ["fixed_period_4"],
    "not_last_color_fill": ["last_nonzero_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named rival to be refuted or answer-equivalent on query."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors}")
            continue
        if pair.get("output") != _solve_true(pair["input"]):
            reasons.append(f"demo {index} output does not match periodic extension")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors}")
    if query.get("output") != _solve_true(query["input"]):
        reasons.append("query output does not match periodic extension")

    surviving = {
        name
        for name, competitor in LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair.get("output") for pair in demos)
    }
    true_answer = _solve_true(query["input"])
    for name in sorted(surviving):
        if LESSON_COMPETITORS[name](query["input"]) != true_answer:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % EXAMPLES_NEEDED

    height = _draw_int_axis(
        ctx, overrides, "grid_h", 5, 14, fixed=5 if slot == 0 else None, diff=True
    )
    width = _draw_int_axis(
        ctx, overrides, "grid_w", 14, 22, fixed=15 if slot == 0 else None, diff=True
    )
    n_rows = _draw_int_axis(
        ctx, overrides, "n_active_rows", 2, 4, fixed=3 if slot == 0 else None
    )
    if overrides.get("period") is not None:
        # Explicit overrides retain the full advertised 3..6 support.
        period = _draw_int_axis(ctx, overrides, "period", 3, 6)
    elif slot == 0:
        period = _draw_int_axis(ctx, overrides, "period", 3, 6, fixed=4)
    elif slot == 1:
        period = _draw_int_axis(ctx, overrides, "period", 3, 6, fixed=3)
    else:
        # Reserve the third teaching slot for a genuinely longer period.
        period = _draw_int_axis(ctx, overrides, "period", 5, 6)
    cutoff_style = _draw_choice_axis(
        ctx,
        overrides,
        "cutoff_style",
        CUTOFF_STYLES,
        fixed=("mixed", "partial", "aligned")[slot],
    )
    leading_style = _draw_choice_axis(
        ctx,
        overrides,
        "leading_zero_style",
        LEADING_ZERO_STYLES,
        fixed=("mixed", "all_zero", "all_nonzero")[slot],
    )
    row_layout = _draw_choice_axis(
        ctx,
        overrides,
        "row_layout",
        ROW_LAYOUTS,
        fixed="bottom_block" if slot == 0 else None,
    )
    palette_size = _draw_int_axis(
        ctx, overrides, "palette_size", 2, 4, fixed=3 if slot == 0 else None
    )
    palette_family = _draw_choice_axis(
        ctx,
        overrides,
        "palette_family",
        PALETTE_FAMILIES,
        fixed="canonical" if slot == 0 else None,
    )

    rows = _row_layout_rows(row_layout, height, n_rows)
    layout_rng = ctx.draw_rng("layout")
    starts_zero = _style_flags(leading_style, n_rows, rng=layout_rng)
    aligned_cutoffs = _style_flags(cutoff_style, n_rows, rng=layout_rng)

    color_pool = _CANONICAL_COLORS if palette_family == "canonical" else _BROAD_COLORS
    palette = ctx.draw_rng("palette").sample(list(color_pool), palette_size)
    patterns, rights = _build_patterns(
        period=period,
        width=width,
        palette=palette,
        starts_zero=starts_zero,
        aligned_cutoffs=aligned_cutoffs,
        rng=ctx.draw_rng("patterns"),
    )

    grid = full_grid(height, width, 0)
    for row_index, pattern, right in zip(rows, patterns, rights):
        for col in range(right + 1):
            grid[row_index][col] = pattern[col % period]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_active_rows": n_rows,
        "period": period,
        "cutoff_style": cutoff_style,
        "leading_zero_style": leading_style,
        "row_layout": row_layout,
        "palette_size": palette_size,
        "palette_family": palette_family,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid
