"""Generator for converting scattered column cells into bottom histograms.

Rule: every nonempty column contains one color.  Count that column's nonzero
cells, erase their scattered positions, and draw a solid bar of the same color
and height against the bottom edge of the same column.  Empty columns remain
empty.

The official task has exactly three active columns on 7x10, 8x8, 8x9, or 9x9
grids.  The teaching distribution keeps substantial support on that manifold
while varying dimensions, active-column count, palette range, counts, column
positions, and scatter geometry.  Every ordinary draw contains unequal counts,
a singleton and a taller column, cells at both vertical extremes, empty
columns, and visible movement in every active column.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6aaddc95d135"
VERSION = "3.0.0"
TASK_ID = "6aaddc95d135"
RULE_HASH = "7640715456c4"
SUMMARY = (
    "A zero-background grid has three to six active columns. Each active "
    "column uses its own nonzero color and contains a scattered set of cells. "
    "For each column independently, count the nonzero cells and replace them "
    "with a solid bottom-aligned bar of the same height and color in that "
    "same column; empty columns stay empty."
)

# Rival shortcuts deliberately rebutted by every ordinary draw:
# - identity/already packed: every active column changes;
# - top packing: a bottom-edge witness makes alignment visible;
# - keep one/fixed-height bars: counts include 1, 2, and >=3;
# - count-only/modal recoloring: active columns use distinct colors;
# - fixed positions/fixed size: dimensions and active columns vary;
# - horizontal packing: multiple cells share columns and rows are scattered.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is zero and at least one column is empty",
    "there are three to six active columns with distinct colors",
    "each active column uses exactly one nonzero color",
    "column counts include at least two different positive values",
    "every active column is scattered rather than already bottom-packed",
    "the input contains evidence in both the top and bottom rows",
]

PALETTE_MODES = ("low_ids", "high_ids", "mixed_ids")
_CANONICAL_DIMS = {(8, 8), (9, 9), (7, 10), (8, 9)}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-band rng 7..10",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-band rng 8..10",
        "valid": "8..10",
    },
    "n_cols": {
        "type": "int",
        "default": "weighted rng 3..6 (canonical 3 favored)",
        "valid": "3..6",
    },
    "palette_mode": {
        "type": "str",
        "default": "rng low_ids|high_ids|mixed_ids",
        "valid": "|".join(PALETTE_MODES),
    },
}

# The exact official dimension/active-column manifold is deliberately a
# substantial subset, not the entire generalized teaching grammar.
MIN_STRICT_FRAC = 0.15


def _active_columns(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    return [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]


def _column_rows(grid: list[list[int]], c: int) -> list[int]:
    return [r for r in range(len(grid)) if grid[r][c] != 0]


def _column_counts(grid: list[list[int]]) -> list[int]:
    return [len(_column_rows(grid, c)) for c in _active_columns(grid)]


def _is_bottom_packed(rows: list[int], h: int) -> bool:
    return rows == list(range(h - len(rows), h))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful teaching grammar.

    This intentionally rejects no-op and underspecified scenes: empty/full
    fields, one- or two-column toys, repeated colors across columns, mixed
    colors within a column, equal-height-only lessons, already packed columns,
    and scenes without both top- and bottom-edge evidence.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errs: list[str] = []
    if not 7 <= h <= 10 or not 8 <= w <= 10:
        errs.append(f"grid {h}x{w} outside the lawful 7..10 by 8..10 envelope")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errs.append("cell value outside integer ARC colors 0..9")
        return errs

    active = _active_columns(grid)
    if not 3 <= len(active) <= 6:
        errs.append(f"expected 3..6 active columns, found {len(active)}")
    if len(active) >= w:
        errs.append("at least one empty column is required")

    colors: list[int] = []
    counts: list[int] = []
    for c in active:
        values = {grid[r][c] for r in range(h) if grid[r][c] != 0}
        rows = _column_rows(grid, c)
        if len(values) != 1:
            errs.append(f"column {c} has {len(values)} nonzero colors: {sorted(values)}")
            continue
        colors.append(next(iter(values)))
        counts.append(len(rows))
        if not 1 <= len(rows) <= h - 2:
            errs.append(
                f"column {c} count {len(rows)} outside lawful 1..{h - 2}"
            )
        if _is_bottom_packed(rows, h):
            errs.append(f"column {c} is already bottom-packed (no visible rule)")

    if len(colors) != len(set(colors)):
        errs.append("active columns must use distinct colors")
    if counts and len(set(counts)) < 2:
        errs.append("column counts do not vary")
    if not any(value != 0 for value in grid[0]):
        errs.append("no top-row evidence")
    if not any(value != 0 for value in grid[-1]):
        errs.append("no bottom-row evidence")
    return errs


def observe_overrides(grid) -> dict[str, int]:
    """Recover the exact semantic integer axis from the returned grid."""
    return {"n_cols": len(_active_columns(grid))}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the canonical Racket oracle."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        if not values:
            continue
        for r in range(h - len(values), h):
            out[r][c] = values[0]
    return out


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact official shape/palette grammar within our superset."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    active = _active_columns(grid)
    strict: list[str] = []
    if (h, w) not in _CANONICAL_DIMS:
        strict.append(f"dimensions {h}x{w} are outside official profiles")
    if len(active) != 3:
        strict.append(f"official examples have 3 active columns, found {len(active)}")
    return strict


def _has_singleton_and_tall(grid) -> bool:
    counts = _column_counts(grid)
    return 1 in counts and any(count >= 3 for count in counts)


def _has_three_count_levels(grid) -> bool:
    return len(set(_column_counts(grid))) >= 3


def _has_top_and_bottom_evidence(grid) -> bool:
    return any(grid[0]) and any(grid[-1])


def _has_gapped_scatter(grid) -> bool:
    for c in _active_columns(grid):
        rows = _column_rows(grid, c)
        if len(rows) >= 2 and any(b - a > 1 for a, b in zip(rows, rows[1:])):
            return True
    return False


def _all_active_columns_move(grid) -> bool:
    h = len(grid)
    active = _active_columns(grid)
    return bool(active) and all(
        not _is_bottom_packed(_column_rows(grid, c), h) for c in active
    )


def _has_distinct_column_colors(grid) -> bool:
    colors = []
    for c in _active_columns(grid):
        values = {grid[r][c] for r in range(len(grid)) if grid[r][c] != 0}
        if len(values) != 1:
            return False
        colors.append(next(iter(values)))
    return len(colors) >= 3 and len(colors) == len(set(colors))


def _has_empty_column(grid) -> bool:
    return len(_active_columns(grid)) < len(grid[0])


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "singleton_and_tall_bars": _has_singleton_and_tall,
    "three_distinct_count_levels": _has_three_count_levels,
    "top_and_bottom_evidence": _has_top_and_bottom_evidence,
    "gapped_scatter": _has_gapped_scatter,
    "all_active_columns_move": _all_active_columns_move,
    "distinct_column_colors": _has_distinct_column_colors,
    "empty_column_preserved": _has_empty_column,
}


def _pack_top(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def _bottom_singletons(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in _active_columns(grid):
        out[-1][c] = next(grid[r][c] for r in range(h) if grid[r][c] != 0)
    return out


def _bottom_fixed_two(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in _active_columns(grid):
        color = next(grid[r][c] for r in range(h) if grid[r][c] != 0)
        out[-2][c] = color
        out[-1][c] = color
    return out


def _bottom_modal_recolor(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    active = _active_columns(grid)
    if not active:
        return out
    modal = next(grid[r][active[0]] for r in range(h) if grid[r][active[0]] != 0)
    for c in active:
        count = len(_column_rows(grid, c))
        for r in range(h - count, h):
            out[r][c] = modal
    return out


def _pack_rows_left(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r in range(h):
        values = [value for value in grid[r] if value != 0]
        out[r][: len(values)] = values
    return out


def _sort_bars_left(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    bars = []
    for c in _active_columns(grid):
        rows = _column_rows(grid, c)
        color = grid[rows[0]][c]
        bars.append((len(rows), color))
    for c, (count, color) in enumerate(sorted(bars, reverse=True)):
        for r in range(h - count, h):
            out[r][c] = color
    return out


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": lambda grid: [row[:] for row in grid],
    "top_pack": _pack_top,
    "keep_only_bottom_cell": _bottom_singletons,
    "fixed_height_two": _bottom_fixed_two,
    "modal_color_bars": _bottom_modal_recolor,
    "pack_rows_left": _pack_rows_left,
    "sort_bars_left": _sort_bars_left,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut fits demos but changes query."""
    reasons: list[str] = []
    for name, rival in _RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but changes query"
                )
    return reasons


def _banded_int(ctx, label: str, lo: int, hi: int, valid_lo: int, valid_hi: int) -> int:
    """Use band defaults but honor every declared boundary in every band."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _draw_n_cols(ctx, difficulty: str | None) -> int:
    if "n_cols" in ctx.overrides and ctx.overrides["n_cols"] is not None:
        return ctx.draw_int("n_cols", 3, 6)
    if difficulty == "easy":
        values, weights = (3, 4, 5, 6), (15, 4, 1, 0)
    elif difficulty == "hard":
        values, weights = (3, 4, 5, 6), (9, 6, 3, 2)
    else:
        values, weights = (3, 4, 5, 6), (12, 5, 2, 1)
    value = ctx.draw_rng("n_cols_weighted").choices(values, weights=weights, k=1)[0]
    ctx.overrides["n_cols"] = value
    return ctx.draw_int("n_cols", 3, 6)


def _palette(mode: str) -> tuple[int, ...]:
    return {
        "low_ids": (1, 2, 3, 4, 5, 6),
        "high_ids": (4, 5, 6, 7, 8, 9),
        "mixed_ids": (1, 3, 5, 7, 8, 9),
    }[mode]


def _scattered_rows(
    rng,
    h: int,
    count: int,
    *,
    force_top: bool = False,
    force_bottom: bool = False,
) -> list[int]:
    required: set[int] = set()
    if force_top:
        required.add(0)
    if force_bottom:
        required.add(h - 1)
    if len(required) > count:
        raise ValueError("row requirements exceed column count")

    candidates = [r for r in range(h) if r not in required]
    rows = set(required)
    rows.update(rng.sample(candidates, count - len(rows)))
    target = set(range(h - count, h))
    if rows == target:
        outside = [r for r in range(h - count) if r not in rows]
        replaceable = [r for r in rows if r not in required]
        if not outside or not replaceable:
            raise RuntimeError("cannot force visible scatter")
        rows.remove(rng.choice(replaceable))
        rows.add(rng.choice(outside))
    return sorted(rows)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h = _banded_int(ctx, "grid_h", 7, 8, 7, 10)
        w = _banded_int(ctx, "grid_w", 8, 9, 8, 10)
        tall = 3
    elif difficulty == "hard":
        h = _banded_int(ctx, "grid_h", 8, 10, 7, 10)
        w = _banded_int(ctx, "grid_w", 9, 10, 8, 10)
        tall = min(5, h - 2)
    else:
        h = _banded_int(ctx, "grid_h", 8, 9, 7, 10)
        w = _banded_int(ctx, "grid_w", 8, 10, 8, 10)
        tall = min(4, h - 2)

    n_cols = _draw_n_cols(ctx, difficulty)
    palette_mode = ctx.draw_choice("palette_mode", PALETTE_MODES)
    rng = ctx.draw_rng("layout")

    active = rng.sample(range(w), n_cols)
    colors = rng.sample(list(_palette(palette_mode)), n_cols)
    counts = [1, 2, tall]
    while len(counts) < n_cols:
        counts.append(rng.randint(1, h - 2))
    rng.shuffle(counts)

    singleton_index = counts.index(1)
    two_index = counts.index(2)
    tall_index = max(range(n_cols), key=counts.__getitem__)

    grid = full_grid(h, w, 0)
    for index, (c, color, count) in enumerate(zip(active, colors, counts)):
        rows = _scattered_rows(
            rng,
            h,
            count,
            force_top=index == tall_index,
            force_bottom=index == two_index,
        )
        # Avoid accidentally forcing the singleton to the bottom when the
        # count-2 and singleton indices coincide (they cannot, but keep the
        # invariant local and explicit for future edits).
        if index == singleton_index and rows == [h - 1]:
            rows = [0]
        for r in rows:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    return grid
