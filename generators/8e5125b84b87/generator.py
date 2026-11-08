"""Generator for puzzle a79310a0.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (and (> r 0) (= 8 (at g (- r 1) c))) 2 0))))`.
Each output cell at (r, c) is 2 iff the cell directly above it
(r-1, c) is cyan(8); otherwise 0. Effectively: every cyan dot in the
input drops a red mark one row below in the output (and clears
everything else to 0).

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * cyan_count             — how many cyan(8) cells to plant
  * cyan_layout            — random / cluster / row / column / diagonal
                             / scattered
  * cyan_row_bias          — top / bottom / mid / spread (bias for
                             which rows cyan cells fall in; cells in
                             bottom row would have no effect)
  * decoy_palette_size     — extra non-cyan colors planted (ignored
                             by rule)
  * caller-opt-in degenerates: no_cyans, only_bottom_row_cyans
                               (rule no-op), single_cyan
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e5125b84b87"
VERSION = "1.1.0"  # bumped: deeper combinatorial axes added
TASK_ID = "8e5125b84b87"
SUMMARY = "Cyan dots on bg=0; rule paints red one cell below each cyan."

INVARIANTS = [
    "bg = 0",
    "≥1 cyan(8) cell with at least one not in the bottom row",
    "grid dims in [3, 25] × [3, 25]",
]

CYAN_LAYOUTS = ("random", "cluster", "row", "column", "diagonal", "scattered")
ROW_BIASES = ("top", "bottom", "mid", "spread")
DEGENERATE_TEXTURES = ("no_cyans", "only_bottom_row_cyans", "single_cyan")
HELPFUL_TEXTURES = CYAN_LAYOUTS

AXES = {
    "grid_h":             {"type": "int",   "default": "rng 3..18", "valid": "3..25"},
    "grid_w":             {"type": "int",   "default": "rng 3..18", "valid": "3..25"},
    "cyan_count":         {"type": "int",   "default": "rng 2..h*w/4", "valid": "1..h*w/2"},
    "cyan_layout":        {"type": "str",   "default": "rng helpful",
                           "valid": "|".join(CYAN_LAYOUTS)},
    "cyan_row_bias":      {"type": "str",   "default": "rng top|bottom|mid|spread",
                           "valid": "|".join(ROW_BIASES)},
    "decoy_palette_size": {"type": "int",   "default": "rng 0..3", "valid": "0..6"},
    "texture":            {"type": "str",   "default": "alias for cyan_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi = 3, 7
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 3, 18

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    n_cyans = int(overrides.get(
        "cyan_count",
        ctx.draw_int("cyan_count", 2, max(2, (h * w) // 4))))
    layout = (overrides.get("texture")
              or overrides.get("cyan_layout")
              or ctx.draw_choice("cyan_layout", list(CYAN_LAYOUTS)))
    row_bias = overrides.get(
        "cyan_row_bias",
        ctx.draw_choice("cyan_row_bias", list(ROW_BIASES)))
    n_decor = int(overrides.get("decoy_palette_size",
                                ctx.draw_int("decoy_palette_size", 0, 3)))

    g = full_grid(h, w, 0)
    cells = _cyan_layout_cells(layout, h, w, n_cyans, row_bias, rng)
    for r, c in cells:
        if 0 <= r < h - 1 and 0 <= c < w:  # skip bottom row so rule has effect
            g[r][c] = 8

    decor_palette = [c for c in range(1, 10) if c != 8 and c != 2]
    rng.shuffle(decor_palette)
    decor_palette = decor_palette[:max(0, n_decor)]
    if decor_palette:
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and rng.random() < 0.10:
                    g[r][c] = rng.choice(decor_palette)

    if not any(g[r][c] == 8 for r in range(h - 1) for c in range(w)):
        g[0][0] = 8
    return g


def _cyan_layout_cells(layout, h, w, n, row_bias, rng):
    if row_bias == "top":
        candidates = [(r, c) for r in range(0, max(1, h // 2)) for c in range(w)]
    elif row_bias == "bottom":
        candidates = [(r, c) for r in range(max(0, h // 2), h - 1) for c in range(w)]
    elif row_bias == "mid":
        m = h // 2
        candidates = [(r, c) for r in range(max(0, m - 1), min(h - 1, m + 2)) for c in range(w)]
    else:  # spread
        candidates = [(r, c) for r in range(h - 1) for c in range(w)]

    if layout == "cluster":
        if not candidates:
            return []
        cr, cc = rng.choice(candidates)
        candidates.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return candidates[:n]
    if layout == "row":
        if not candidates:
            return []
        rs = sorted({r for r, _ in candidates})
        r = rng.choice(rs)
        cells = [(r, c) for c in range(w)]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column":
        c = rng.randint(0, w - 1)
        cells = [(r, c) for (r, cc) in candidates if cc == c]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        diag = [(k, k) for k in range(min(h - 1, w))]
        return diag[:n]
    if layout == "scattered":
        cells = [(r, c) for (r, c) in candidates if (r + c) % 2 == 0]
        rng.shuffle(cells)
        return cells[:n]
    rng.shuffle(candidates)
    return candidates[:n]


def self_check(grid, *, difficulty=None, meta=None):
    """Verify cyan(8) gravity-fall invariants for 8e5125b84b87."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    cyan_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not cyan_cells:
        errs.append("no cyan (8) cells")
    elif all(r == h - 1 for r, c in cyan_cells):
        errs.append("all cyan (8) cells are already in the bottom row (gravity is no-op)")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the cyan→below-red signal collapses.

    no_cyans              — no 8s; rule no-op (output all 0).
    only_bottom_row_cyans — every cyan is in the bottom row; the rule's
                             "(r-1, c)" reference never lands; output
                             is all 0.
    single_cyan           — one cyan; output has exactly one 2 below it.
    """
    g = full_grid(h, w, 0)
    if name == "no_cyans":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.2:
                    g[r][c] = rng.choice([1, 3, 4, 5, 6, 7, 9])
        return g
    if name == "only_bottom_row_cyans":
        for c in range(w):
            if rng.random() < 0.5:
                g[h - 1][c] = 8
        # ensure ≥1 cyan
        g[h - 1][0] = 8
        return g
    if name == "single_cyan":
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 1)
        g[r][c] = 8
        return g
    return g
