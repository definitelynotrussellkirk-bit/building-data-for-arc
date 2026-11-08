"""Generator for puzzle 4258a5f9.

Rule: for each cell with v == 5 → 5. Else if any 8-neighbor of (r, c)
has value 5 → 1, else 0. (5 dots get a halo of 1; others zero out.)

Combinatorial axes (8): grid_h/w, bg_color, n_dots, dot_layout,
dot_clustering, decoy_palette_size, decoy_density, dot_position_bias.
Degenerates: no_dots, dot_in_every_cell, border_dots_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "09c1490f30e0"
VERSION = "2.2.0"  # poison fix: default bg=0 and no decoys (canonical inputs are {0,5}-only; rule zeroes everything but 5s+halo)
TASK_ID = "09c1490f30e0"
SUMMARY = (
    "BG-COLOR (bg ∈ {0, 2..4, 6..9}, "
    "excluding 1 and 5) grid (h, w ~ "
    "4-18) with: (a) 1..n_dots COLOR-5 "
    "(gray) DOT CELLS placed via one "
    "of 8 LAYOUTS (random / cluster / "
    "row / column / diagonal / "
    "scattered / blob / corners) "
    "constrained to a POSITION BIAS "
    "region (random / top / bottom / "
    "center / spread); (b) optional "
    "DECOY CELLS in 0..3 non-{bg, 1, "
    "5} colors scattered at low "
    "density (0..0.15). All other "
    "cells stay bg. Rule (FOR EACH "
    "GRAY-5 DOT, KEEP THE DOT AND "
    "PAINT COLOR 1 AT ALL ITS 8-"
    "NEIGHBORS): for EACH CELL "
    "(r, c) in the input: IF v=5, "
    "KEEP it as 5 in the output. "
    "ELSE: CHECK if ANY of its 8 "
    "surrounding neighbors has value "
    "5. IF YES: PAINT (r, c) with "
    "COLOR 1. IF NO: SET (r, c) to "
    "bg-0. Net: gray dots survive; "
    "each dot grows a halo of 1s in "
    "its 8-neighborhood; all other "
    "cells (including decoys) are "
    "zeroed out."
)

INVARIANTS = [
    "bg ≠ 5 and ≠ 1",
    "≥1 gray(5) cell (except no_dots: genuinely dotless, output all-0)",
    "ones_decoy boards: ≥1 input color-1 cell away from every 5",
]

DOT_LAYOUTS = ("random", "cluster", "row", "column", "diagonal",
               "scattered", "blob", "corners")
POSITION_BIASES = ("random", "top", "bottom", "center", "spread")
DEGENERATE_TEXTURES = ("no_dots", "dot_in_every_cell", "border_dots_only")
HELPFUL_TEXTURES = DOT_LAYOUTS + ("ones_decoy",)

AXES = {
    "grid_h":             {"type": "int", "default": "rng 4..18", "valid": "3..25"},
    "grid_w":             {"type": "int", "default": "rng 4..18", "valid": "3..25"},
    "bg_color":           {"type": "color", "default": "0 (canonical is {0,5}-only)", "valid": "0..9 (≠1,5)"},
    "n_dots":             {"type": "int", "default": "rng 1..h*w/4", "valid": "1..h*w/2"},
    "dot_layout":         {"type": "str", "default": "rng helpful",
                           "valid": "random|cluster|row|column|diagonal|"
                                    "scattered|blob|corners"},
    "dot_position_bias":  {"type": "str", "default": "rng helpful",
                           "valid": "random|top|bottom|center|spread"},
    "decoy_palette_size": {"type": "int", "default": "0 (canonical has no decoys)", "valid": "0..6"},
    "decoy_density":      {"type": "float", "default": "rng 0..0.15", "valid": "0..0.5"},
    "texture":            {"type": "str", "default": "alias for dot_layout",
                           "valid": "random|cluster|row|column|diagonal|"
                                    "scattered|blob|corners|ones_decoy|"
                                    "no_dots|dot_in_every_cell|"
                                    "border_dots_only",
                           "doc": "ones_decoy: input contains color-1 cells "
                                  "NOT near any 5 - they erase to 0 "
                                  "(refutes '1s are preserved')."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 7
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 4, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    # POISON FIX (2.2.0): canonical inputs are {0,5} ONLY. The rule
    # zeroes everything that isn't a 5 or 5-adjacent, so a non-0 bg and
    # scattered decoys are a decoy the rule ignores AND canonical never
    # contains. Default to bg=0 and no decoys; honor overrides only (the
    # decoy/ones_decoy stress axes remain available explicitly).
    bg = int(overrides.get("bg_color", 0))
    n_dots = int(overrides.get("n_dots",
                               ctx.draw_int("n_dots", 1, max(1, h * w // 4))))
    layout = (overrides.get("texture") or overrides.get("dot_layout")
              or ctx.draw_choice("dot_layout", list(DOT_LAYOUTS)))
    bias = overrides.get("dot_position_bias",
                         ctx.draw_choice("dot_position_bias", list(POSITION_BIASES)))
    n_decoy = int(overrides.get("decoy_palette_size", 0))
    decoy_d = float(overrides.get("decoy_density",
                                  ctx.draw_rng("decoy_density").uniform(0.0, 0.15)))
    g = full_grid(h, w, bg)
    decoy_palette = [c for c in range(1, 10) if c not in {bg, 1, 5}]
    rng.shuffle(decoy_palette)
    decoy_palette = decoy_palette[:max(0, n_decoy)]
    if decoy_palette:
        for r in range(h):
            for c in range(w):
                if rng.random() < decoy_d:
                    g[r][c] = rng.choice(decoy_palette)
    candidates = _candidates_for_bias(bias, h, w)
    cells = _layout_cells(layout, candidates, n_dots, rng)
    for r, c in cells:
        g[r][c] = 5
    if not any(g[r][c] == 5 for r in range(h) for c in range(w)):
        g[h // 2][w // 2] = 5
    if layout == "ones_decoy":
        # input 1s away from every 5: the rule erases them to 0
        fives = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 5]
        placed = 0
        for _t in range(200):
            if placed >= rng.randint(2, 4):
                break
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != bg:
                continue
            if any(abs(r - fr) <= 1 and abs(c - fc) <= 1 for fr, fc in fives):
                continue
            g[r][c] = 1
            placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg≠5 and ≠1; ≥1 gray(5) dot cell."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if not any(grid[r][c] == 5 for r in range(h) for c in range(w)):
        errs.append("no gray(5) dot cell found")
    return errs


def _candidates_for_bias(bias, h, w):
    if bias == "top":
        return [(r, c) for r in range(0, max(1, h // 2)) for c in range(w)]
    if bias == "bottom":
        return [(r, c) for r in range(max(0, h // 2), h) for c in range(w)]
    if bias == "center":
        return [(r, c) for r in range(h // 4, max(h // 4 + 1, 3 * h // 4))
                for c in range(w // 4, max(w // 4 + 1, 3 * w // 4))]
    if bias == "spread":
        return [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
    return [(r, c) for r in range(h) for c in range(w)]


def _layout_cells(layout, candidates, n, rng):
    if not candidates: return []
    n = min(n, len(candidates))
    if layout == "cluster":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return candidates[:n]
    if layout == "row":
        rs = sorted({r for r, _ in candidates})
        if not rs: return []
        r = rng.choice(rs)
        cells = [(r, c) for (rr, c) in candidates if rr == r]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column":
        cs = sorted({c for _, c in candidates})
        if not cs: return []
        c = rng.choice(cs)
        cells = [(r, c) for (r, cc) in candidates if cc == c]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        cset = set(candidates)
        return [(k, k) for k in range(25) if (k, k) in cset][:n]
    if layout == "scattered":
        scat = [(r, c) for (r, c) in candidates if (r + c) % 2 == 0]
        rng.shuffle(scat)
        return scat[:n]
    if layout == "blob":
        cr, cc = rng.choice(candidates)
        candidates = sorted(candidates, key=lambda rc: max(abs(rc[0] - cr), abs(rc[1] - cc)))
        return candidates[:n]
    if layout == "corners":
        h = max(r for r, _ in candidates) + 1
        w = max(c for _, c in candidates) + 1
        return [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)][:n]
    rng.shuffle(candidates)
    return candidates[:n]


def _draw_from_degenerate(name, h, w, rng):
    bg = rng.choice([c for c in range(10) if c not in {1, 5}])
    g = full_grid(h, w, bg)
    if name == "no_dots":
        # genuinely NO 5 cells: every cell (bg and decoys) erases to 0,
        # the output is the all-zero grid (NOT identity)
        for _ in range(rng.randint(0, 4)):
            g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = \
                rng.choice([c for c in range(2, 10) if c != 5 and c != bg])
        return g
    if name == "dot_in_every_cell":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    if name == "border_dots_only":
        for c in range(w):
            g[0][c] = 5; g[h - 1][c] = 5
        for r in range(h):
            g[r][0] = 5; g[r][w - 1] = 5
        return g
    return g
