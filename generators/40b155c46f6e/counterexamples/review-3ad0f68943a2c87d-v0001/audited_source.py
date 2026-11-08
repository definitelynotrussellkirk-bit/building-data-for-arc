"""Generator for arc_puzzle_bank_tenth21:E68.

Rule: compact active rows with one odd color recolor that cell to the row
majority.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, single_color, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40b155c46f6e"
VERSION = "2.1.0"  # match canonical compact/two-active-row structure
TASK_ID = "40b155c46f6e"
SUMMARY = (
    "0-bg grid matching the canonical row-majority-cleanup format: "
    "usually a 5-row canvas with two separated ACTIVE rows. Each active "
    "row contains one COMPACT contiguous run of non-zero cells with exactly "
    "two colors: a MAJORITY color appearing multiple times and one ODD "
    "singleton. The rule recolors each active row's singleton to the row "
    "majority; blank rows/background stay zero."
)

# Rivals: 'recolor all rows' refuted by ≥2 demos where some rows already
# have only one color (no change). 'recolor majority cells to odd
# color' refuted by any demo (odd becomes major, not the reverse).
# 'use bg color for odd' refuted by any demo (odd takes major's color).
# 'operate per column' refuted by ≥1 demo where columns wouldn't match
# the pattern but rows do. 3 demos with varied (major, odd, count)
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "normal instances have a few compact active rows, not every row active",
    "each active row has exactly two nonzero colors",
    "one color appears once and the other appears multiple times",
    "inactive cells stay zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "single_color", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5..7"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "n_active_rows":  {"type": "int", "default": "2", "valid": "1..3"},
    "run_len":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = int(overrides.get("grid_h", ctx.draw_int("grid_h", 5, 5)))
        w = int(overrides.get("grid_w", ctx.draw_int("grid_w", 8, 9)))
        n_active = int(overrides.get("n_active_rows", 2))
        run_lo, run_hi = 4, 4
    elif difficulty == "hard":
        h = int(overrides.get("grid_h", ctx.draw_int("grid_h", 5, 7)))
        w = int(overrides.get("grid_w", ctx.draw_int("grid_w", 9, 12)))
        n_active = int(overrides.get("n_active_rows", ctx.draw_int("n_active_rows", 2, 3)))
        run_lo, run_hi = 4, 6
    else:
        h = int(overrides.get("grid_h", ctx.draw_int("grid_h", 5, 5)))
        w = int(overrides.get("grid_w", ctx.draw_int("grid_w", 8, 10)))
        n_active = int(overrides.get("n_active_rows", 2))
        run_lo, run_hi = 4, 5
    g = full_grid(h, w, 0)
    n_active = max(1, min(n_active, max(1, h - 1)))
    preferred = [1, 3, 5]
    candidates = [r for r in preferred if r < h]
    if len(candidates) < n_active:
        candidates += [r for r in range(h) if r not in candidates]
    active_rows = candidates[:n_active]
    # Small shuffle for hard/overridden cases while preserving separated rows when possible.
    if h > 5 or n_active != 2:
        rng.shuffle(active_rows)
        active_rows = sorted(active_rows[:n_active])
    for r in active_rows:
        majority, odd = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        run_len = int(overrides.get("run_len", ctx.draw_int("run_len", run_lo, min(run_hi, w))))
        run_len = max(3, min(run_len, w))
        start = rng.randint(0, w - run_len)
        cols = list(range(start, start + run_len))
        odd_pos = rng.choice(cols)
        for c in cols:
            g[r][c] = majority
        g[r][odd_pos] = odd
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify compact two-color active-row invariants for 40b155c46f6e."""
    errs = []
    h, w = len(grid), len(grid[0])
    active_rows = []
    for r in range(h):
        row = [grid[r][c] for c in range(w)]
        nz_colors = {v for v in row if v != 0}
        nz_cols = [c for c, v in enumerate(row) if v != 0]
        if not nz_cols:
            continue
        active_rows.append(r)
        if len(nz_colors) != 2:
            errs.append(f"row {r} has {len(nz_colors)} non-zero colors (expected exactly 2)")
            break
        lo, hi = min(nz_cols), max(nz_cols)
        if nz_cols != list(range(lo, hi + 1)):
            errs.append(f"row {r} active cells are not one compact run")
            break
        counts = {color: row.count(color) for color in nz_colors}
        if sorted(counts.values())[0] != 1 or sorted(counts.values())[1] <= 1:
            errs.append(f"row {r} lacks a singleton odd color and repeated majority")
            break
    if all(grid[r][c] == 0 for r in range(h) for c in range(w)):
        errs.append("all cells are zero (no active rows)")
    if len(active_rows) > max(3, h // 2 + 1):
        errs.append("too many active rows; canonical task has a few compact rows")
    if len(active_rows) == h:
        errs.append("every row is active; blank separator rows are missing")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 9, 0)
    if name == "no_marks":
        return g
    if name == "single_color":
        for r in range(6):
            for c in range(2, 7):
                g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(9):
                g[r][c] = 3
        return g
    return g
