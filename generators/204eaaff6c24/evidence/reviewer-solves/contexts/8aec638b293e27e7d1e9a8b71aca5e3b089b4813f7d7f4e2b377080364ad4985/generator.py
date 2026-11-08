"""Input generator for canonical ARC task d631b094 / 204eaaff6c24.

Canonical rule authority is unchanged: find the sole nonzero color, count its
cells N, and emit a 1 x N bar of that color.  The sampler deliberately varies
canvas, count, color, and topology while retaining a deterministic four-pair
teaching schedule:

* one exact-canonical-profile disconnected witness,
* one broad ordinary draw,
* one broad disconnected witness,
* one broad ordinary draw.

Thus every four-pair lesson and every three-of-four query rotation contains a
demonstration that refutes the strongest canonical-fitting shortcut retained
here: counting only the largest 8-connected foreground component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "204eaaff6c24"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4571597a8055"
SUMMARY = (
    "0-background grid with exactly one nonzero color. Count all of that "
    "color's cells (1..30) and output a 1 x N bar of the same color."
)

INVARIANTS = [
    "background is 0 and at least one 0 cell remains",
    "exactly one nonzero color appears (any of 1..9)",
    "1..30 nonzero cells, so the canonical 1 x N output fits ARC limits",
    "grid dimensions stay within 3..12 x 3..12",
    "ordinary four-pair windows contain two disconnected 8-neighbor witnesses",
]

FG_LAYOUTS = (
    "random", "cluster", "row", "column", "diagonal", "blob", "scattered"
)
HELPFUL_TEXTURES = FG_LAYOUTS
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIM_LO, _DIM_HI = 3, 12
_N_LO, _N_HI = 1, 30

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 3..5 easy, 3..6 medium, 6..12 hard; free dimensions grow for exact count/layout controls",
        "valid": "3..12",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 3..5 easy, 3..6 medium, 6..12 hard; free dimensions grow for exact count/layout controls",
        "valid": "3..12",
    },
    "fg_color": {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "n_cells": {
        "type": "int",
        "default": "band rng 1..8 easy, 1..15 medium, 5..30 hard; scheduled exact profile uses 2..4",
        "valid": "1..30",
    },
    "fg_layout": {
        "type": "str",
        "default": "rng helpful; scheduled witness draws use scattered",
        "valid": "|".join(FG_LAYOUTS),
    },
    "texture": {
        "type": "str",
        "default": "compatibility alias for fg_layout",
        "valid": "|".join(FG_LAYOUTS),
    },
}

# The two public spellings are mutually exclusive.  Other value-dependent
# feasibility failures attach `incompatible_axes` directly to the ValueError.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("fg_layout", "texture")]

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_disconnected_witness",
    "broad_ordinary_a",
    "broad_disconnected_witness",
    "broad_ordinary_b",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic profile chosen by pair index, independent of rule labels."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the declared one-color counting domain, not a topology shortcut.

    Singleton, short-line, solid-2x2, connected, and disconnected foregrounds
    are all lawful for the count rule.  Generic minimal-shape lint warnings for
    those cases are therefore diagnostic false positives, not grounds to narrow
    the semantic domain.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("color outside 0..9")
    if not (_DIM_LO <= h <= _DIM_HI and _DIM_LO <= w <= _DIM_HI):
        errors.append(
            f"dims {h}x{w} outside valid {_DIM_LO}..{_DIM_HI} x {_DIM_LO}..{_DIM_HI}"
        )
    colors = {value for row in grid for value in row if value != 0}
    if not colors:
        errors.append("no nonzero cell (the rule has no color to count)")
    elif len(colors) > 1:
        errors.append(f"{len(colors)} nonzero colors {sorted(colors)}; exactly one allowed")
    count = sum(value != 0 for row in grid for value in row)
    if count > _N_HI:
        errors.append(f"{count} nonzero cells; output bar would exceed {_N_HI} cells")
    if count == h * w:
        errors.append("no background 0 cell left")
    return errors


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover the two exact semantic controls from a returned grid."""
    colors = {value for row in grid or [] for value in row if value != 0}
    color = next(iter(colors)) if len(colors) == 1 else None
    count = sum(value != 0 for row in grid or [] for value in row)
    return {"fg_color": color, "n_cells": count}


def _conflict(message: str, axes) -> None:
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(set(axes)))
    raise error


def _validate_call(seed, sample_index, difficulty, overrides) -> dict:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}; use easy, medium, hard, or None")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    values = {name: value for name, value in overrides.items() if value is not None}

    integer_ranges = {
        "grid_h": (_DIM_LO, _DIM_HI),
        "grid_w": (_DIM_LO, _DIM_HI),
        "fg_color": (1, 9),
        "n_cells": (_N_LO, _N_HI),
    }
    for name, (lo, hi) in integer_ranges.items():
        if name not in values:
            continue
        value = values[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool/float/string)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    for name in ("fg_layout", "texture"):
        if name not in values:
            continue
        value = values[name]
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        if value not in FG_LAYOUTS:
            raise ValueError(f"unknown {name} {value!r}; valid: {FG_LAYOUTS}")

    if "fg_layout" in values and "texture" in values:
        _conflict(
            "fg_layout and texture are conflicting aliases; pass only one",
            ("fg_layout", "texture"),
        )
    return values


def _band_limits(difficulty):
    if difficulty == "easy":
        return 3, 5, 1, 8
    if difficulty == "hard":
        return 6, 12, 5, 30
    return 3, 6, 1, 15


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Strict keyed integer draw; explicit overrides use the full valid range."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, lo, hi)


def _layout_cap(layout, h, w):
    if layout == "row":
        return w
    if layout == "column":
        return h
    if layout == "diagonal":
        return min(h, w)
    return h * w


def _isolated_cap(h, w):
    return ((h + 1) // 2) * ((w + 1) // 2)


def _weighted_options(values, preferred):
    values = tuple(sorted(set(values)))
    options = list(values)
    preferred = set(preferred)
    for value in values:
        if value in preferred:
            options.extend([value] * 6)
    return options


def _draw_feasible_dimensions(ctx, values, *, n, layout, d_lo, d_hi):
    """Jointly construct dimensions for an exact count and optional layout.

    Free axes may grow up to the declared 12x12 envelope.  Exact axes remain
    exact.  Selecting h first is safe because it is drawn only from values that
    retain at least one feasible w, then w is drawn from that conditional set.
    """
    heights = [values["grid_h"]] if "grid_h" in values else list(range(d_lo, _DIM_HI + 1))
    widths = [values["grid_w"]] if "grid_w" in values else list(range(d_lo, _DIM_HI + 1))

    def feasible(h, w):
        if h * w < n + 1:
            return False
        return layout is None or _layout_cap(layout, h, w) >= n

    pairs = [(h, w) for h in heights for w in widths if feasible(h, w)]
    if not pairs:
        axes = {"n_cells"}
        if layout is not None:
            axes.add("texture" if "texture" in values else "fg_layout")
        axes.update(name for name in ("grid_h", "grid_w") if name in values)
        _conflict(
            f"n_cells={n} cannot fit requested layout/dimensions within the declared 3..12 envelope",
            axes,
        )

    feasible_h = sorted({h for h, _ in pairs})
    if "grid_h" in values:
        h_options = feasible_h
    else:
        h_options = _weighted_options(feasible_h, range(d_lo, d_hi + 1))
    h = ctx.draw_choice("grid_h", h_options)

    feasible_w = sorted({w for pair_h, w in pairs if pair_h == h})
    if "grid_w" in values:
        w_options = feasible_w
    else:
        w_options = _weighted_options(feasible_w, range(d_lo, d_hi + 1))
    w = ctx.draw_choice("grid_w", w_options)
    return h, w


def _layout_cells(layout, h, w, n, rng):
    if layout == "cluster":
        center_r, center_c = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda cell: abs(cell[0] - center_r) + abs(cell[1] - center_c))
        return cells[:n]
    if layout == "row":
        row = rng.randint(0, h - 1)
        cells = [(row, c) for c in range(w)]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column":
        column = rng.randint(0, w - 1)
        cells = [(r, column) for r in range(h)]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        return [(index, index) for index in range(min(h, w))][:n]
    if layout == "blob":
        center_r, center_c = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda cell: max(abs(cell[0] - center_r), abs(cell[1] - center_c)))
        return cells[:n]
    if layout == "scattered":
        primary = [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
        primary_set = set(primary)
        rest = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if (r, c) not in primary_set
        ]
        rng.shuffle(primary)
        rng.shuffle(rest)
        return (primary + rest)[:n]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    return cells[:n]


def _foreground_color(grid):
    for row in grid:
        for value in row:
            if value != 0:
                return value
    return 0


def _component_sizes_8(grid):
    color = _foreground_color(grid)
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color and color != 0
    }
    sizes = []
    while remaining:
        todo = [remaining.pop()]
        size = 0
        while todo:
            r, c = todo.pop()
            size += 1
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        todo.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _largest_8_connected_component(grid):
    """Rival only: count the largest 8-connected foreground component."""
    color = _foreground_color(grid)
    sizes = _component_sizes_8(grid)
    return [[color] * (sizes[0] if sizes else 0)]


def _multiple_8_connected_components(grid):
    return len(_component_sizes_8(grid)) >= 2


SEMANTIC_RIVALS = {
    "largest_8_connected_component": _largest_8_connected_component,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "multiple_8_connected_components": _multiple_8_connected_components,
}
WITNESS_RIVALS = {
    "multiple_8_connected_components": ["largest_8_connected_component"],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("placement")
    d_lo, d_hi, n_lo, n_hi = _band_limits(difficulty)

    # Any explicit control bypasses the teaching schedule so it stays exact.
    scheduled = not values
    profile = schedule_profile(seed, sample_index, difficulty) if scheduled else "override"
    if profile == "canonical_disconnected_witness":
        d_lo = d_hi = 3
        n_lo, n_hi = 2, 4

    layout = None
    if "texture" in values:
        layout = ctx.draw_choice("texture", FG_LAYOUTS)
    elif "fg_layout" in values:
        layout = ctx.draw_choice("fg_layout", FG_LAYOUTS)

    n_override = values.get("n_cells")
    if n_override is not None:
        h, w = _draw_feasible_dimensions(
            ctx,
            values,
            n=n_override,
            layout=layout,
            d_lo=d_lo,
            d_hi=d_hi,
        )
    else:
        h = _banded_int(ctx, overrides, "grid_h", d_lo, d_hi, _DIM_LO, _DIM_HI)
        w = _banded_int(ctx, overrides, "grid_w", d_lo, d_hi, _DIM_LO, _DIM_HI)

    color = ctx.draw_color_strict("fg_color", exclude=(0,))

    if layout is None:
        if profile in ("canonical_disconnected_witness", "broad_disconnected_witness"):
            layout = ctx.draw_choice("fg_layout", ("scattered",))
        else:
            pool = [
                candidate
                for candidate in FG_LAYOUTS
                if n_override is None or _layout_cap(candidate, h, w) >= n_override
            ]
            layout = ctx.draw_choice("fg_layout", pool)

    layout_cap = min(_layout_cap(layout, h, w), h * w - 1, _N_HI)
    if n_override is not None:
        if n_override > layout_cap:
            axes = {"n_cells", "texture" if "texture" in values else "fg_layout"}
            axes.update(name for name in ("grid_h", "grid_w") if name in values)
            _conflict(
                f"n_cells={n_override} cannot fit layout {layout!r} on {h}x{w} (cap {layout_cap})",
                axes,
            )
        n = ctx.draw_int_strict("n_cells", _N_LO, layout_cap)
    else:
        cap = min(n_hi, layout_cap)
        if profile in ("canonical_disconnected_witness", "broad_disconnected_witness"):
            cap = min(cap, _isolated_cap(h, w))
            low = max(2, min(n_lo, cap))
        else:
            low = min(n_lo, cap)
        n = ctx.draw_int_strict("n_cells", low, max(low, cap))

    grid = full_grid(h, w, 0)
    for r, c in _layout_cells(layout, h, w, n, rng):
        grid[r][c] = color
    return grid
