"""Generator for puzzle a61f2674.

Rule: gray(5) vertical bars (anchored at bottom). Output keeps only
tallest (→blue 1) and shortest (→red 2); removes the rest.

Combinatorial axes (8): grid_h/w, n_bars, height_min, height_max,
column_layout, anchor_corner, asymmetry_force, palette_size.
Degenerates: tied_heights, single_bar, no_bars.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec7d4f02ef89"
VERSION = "2.1.0"  # keep bars visually separated and add executable self_check
TASK_ID = "ec7d4f02ef89"
SUMMARY = "Gray(5) bottom-anchored vertical bars of pairwise-distinct heights (1..h, incl full-height); rule keeps the TALLEST bar (->blue 1) and SHORTEST bar (->red 2), erases the rest. Distinct heights make tallest/shortest unambiguous (rule tie-breaks leftmost)."

INVARIANTS = [
    "background is 0",
    "all non-bg cells are gray(5)",
    ">=3 distinct gray vertical bars (bottom-anchored), distinct columns",
    "heights are pairwise distinct and in 1..h",
]

COLUMN_LAYOUTS = ("scattered", "left_to_right", "right_to_left",
                  "evenly_spaced", "clustered")
DEGENERATE_TEXTURES = ("tied_heights", "single_bar", "no_bars")
HELPFUL_TEXTURES = COLUMN_LAYOUTS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 8..14', 'valid': '6..18'},
 'grid_w': {'type': 'int', 'default': 'rng 8..14', 'valid': '6..18'},
 'n_bars': {'type': 'int', 'default': 'rng 3..8 by diff', 'valid': '3..8'},
 'height_min': {'type': 'int', 'default': '1', 'valid': '1..h'},
 'height_max': {'type': 'int', 'default': 'h', 'valid': '2..h'},
 'column_layout': {'type': 'str',
                   'default': 'rng helpful',
                   'valid': 'scattered|left_to_right|right_to_left|evenly_spaced|clustered'},
 'anchor_corner': {'type': 'bool', 'default': 'false', 'valid': 'true|false'},
 'asymmetry_force': {'type': 'bool', 'default': 'false', 'valid': 'true|false'},
 'texture': {'type': 'str',
             'default': 'alias for column_layout',
             'valid': 'scattered|left_to_right|right_to_left|evenly_spaced|clustered|tied_heights|single_bar|no_bars'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, nb_lo, nb_hi = 6, 9, 3, 4
    elif difficulty == "hard":
        h_lo, h_hi, nb_lo, nb_hi = 14, 18, 5, 8
    else:
        h_lo, h_hi, nb_lo, nb_hi = 8, 14, 4, 6
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi + 2)   # own range -> non-square too
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_bars = int(overrides.get("n_bars", ctx.draw_int("n_bars", nb_lo, nb_hi)))
    # need n_bars distinct heights in [h_min, h_max] AND n_bars distinct columns;
    # clamp so bars always FIT (ht<=h -> no negative-index wrap).
    h_min = max(1, min(h, int(overrides.get("height_min", 1))))
    h_max = max(h_min, min(h, int(overrides.get("height_max", h))))
    # The task's visual objects are separated vertical bars.  Adjacent columns
    # merge into one connected gray component, which poisoned object-count stats
    # even though the Racket rule still reads columns.  Leave at least one blank
    # column between bars whenever the default path is used.
    n_bars = max(3, min(n_bars, (w + 1) // 2, h_max - h_min + 1))
    layout = (overrides.get("texture") or
              overrides.get("column_layout")
              or ctx.draw_choice("column_layout", list(COLUMN_LAYOUTS)))
    heights = rng.sample(range(h_min, h_max + 1), n_bars)
    cols = _pick_columns(layout, w, n_bars, rng)
    g = full_grid(h, w, 0)
    for col, ht in zip(cols, heights):
        for r in range(h - ht, h):          # ht in [1,h] -> h-ht in [0,h-1]
            g[r][col] = 5
    return g


def _separated_sample(w, n, rng):
    """Sample n columns with at least one blank column between bars."""
    for parity in rng.sample([0, 1], 2):
        cand = list(range(parity, w, 2))
        if len(cand) >= n:
            return sorted(rng.sample(cand, n))
    # Fallback for tiny override widths; generate still clamps n so this should
    # be rare.  Greedy keeps the strongest possible separation.
    cols = []
    for c in range(w):
        if all(abs(c - x) > 1 for x in cols):
            cols.append(c)
            if len(cols) == n:
                return cols
    return cols[:n]


def _pick_columns(layout, w, n, rng):
    if layout == "left_to_right":
        return list(range(0, min(w, 2 * n), 2))[:n]
    if layout == "right_to_left":
        return sorted(list(range(w - 1, -1, -2))[:n])
    if layout == "evenly_spaced":
        if n == 1:
            return [w // 2]
        cols = sorted({round(i * (w - 1) / (n - 1)) for i in range(n)})
        if len(cols) == n and all(b - a > 1 for a, b in zip(cols, cols[1:])):
            return cols
        return _separated_sample(w, n, rng)
    if layout == "clustered":
        span = 2 * (n - 1)
        start = rng.randint(0, max(0, w - 1 - span))
        return list(range(start, start + span + 1, 2))[:n]
    return _separated_sample(w, n, rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariant check for separated bottom-anchored gray bars."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    palette = {v for row in grid for v in row}
    if not palette <= {0, 5}:
        errs.append(f"expected only background 0 and gray bars 5, got {sorted(palette)}")
    bar_cols = []
    heights = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 5]
        if not rows:
            continue
        bar_cols.append(c)
        top = min(rows)
        expected = list(range(top, h))
        if rows != expected:
            errs.append(f"column {c} is not a solid bottom-anchored bar")
        heights.append(h - top)
    if len(bar_cols) < 3:
        errs.append(f"expected at least three bars, found {len(bar_cols)}")
    if len(heights) != len(set(heights)):
        errs.append(f"bar heights should be pairwise distinct, got {heights}")
    adjacent = [(a, b) for a, b in zip(bar_cols, bar_cols[1:]) if b - a <= 1]
    if adjacent:
        errs.append(f"bars should be separated by blank columns, adjacent pairs={adjacent}")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "tied_heights":
        # Multiple bars all same height
        for c in [1, 4, 7]:
            if c < w:
                for r in range(h - 3, h):
                    g[r][c] = 5
        return g
    if name == "single_bar":
        c = w // 2
        for r in range(h - 4, h):
            g[r][c] = 5
        return g
    if name == "no_bars":
        return g
    return g
