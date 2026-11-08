"""Generator for ARC task 99fa7670.

Rule: each colored seed extends rightward to col w-1 and then downward
along col w-1.

Combinatorial axes (8): grid_h/w, n_seeds, palette_size, seed_layout,
position_bias, palette_kind, seed_separation, anchor_endpoints.
Degenerates: no_seeds, single_seed, all_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee1c3a11982c"
VERSION = "2.2.0"
TASK_ID = "ee1c3a11982c"
SUMMARY = (
    "0-bg grid (h, w ~5-12) with 2-5 SPARSE non-bg SEEDS "
    "in distinct colors at random positions NOT in the "
    "last row or last column. Rule: for each non-bg seed "
    "at (r, c) with color k: PAINT every cell in row r "
    "from c to col w-1 (extending rightward to the last "
    "column) with color k. Then for the cell (r, w-1) — "
    "also paint every cell in col w-1 from r to row h-1 "
    "(extending downward to the last row) with color k. "
    "Net: each seed traces an L-shaped path right to the "
    "right edge, then down to the bottom-right corner."
)

INVARIANTS = [
    "background is 0",
    ">=1 nonzero seed cell",
    "seeds are NOT in last col (so right-extension is visible)",
    "seeds are NOT in last row (so down-extension is visible)",
]

SEED_LAYOUTS = ("scattered", "diagonal", "anti_diag", "row", "col",
                "corners", "blob")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "all_seeds")
HELPFUL_TEXTURES = SEED_LAYOUTS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "grid_w":           {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "n_seeds":          {"type": "int", "default": "2-3 easy / 3-5 med / 5-8 hard", "valid": "1..8"},
    "palette_size":     {"type": "int", "default": "= n_seeds",
                         "valid": "1..7"},
    "seed_layout":      {"type": "str", "default": "rng helpful",
                         "valid": "scattered|diagonal|anti_diag|row|col|corners|blob"},
    "position_bias":    {"type": "str", "default": "rng spread|center|edge",
                         "valid": "spread|center|edge"},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "warm|cool|broad|small"},
    "seed_separation":  {"type": "int", "default": "1", "valid": "1..3"},
    "texture":          {"type": "str", "default": "alias for seed_layout",
                         "valid": "scattered|diagonal|anti_diag|row|col|corners|blob|no_seeds|single_seed|all_seeds"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # difficulty scales grid size AND seed count (path count) so hard isn't sparse
    if difficulty == "easy":
        h_lo, h_hi, s_lo, s_hi = 4, 6, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, s_lo, s_hi = 11, 16, 5, 8
    else:
        h_lo, h_hi, s_lo, s_hi = 5, 12, 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_seeds = int(overrides.get("n_seeds",
                                ctx.draw_int("n_seeds", s_lo, s_hi)))
    n_seeds = max(1, min(8, n_seeds))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n_seeds:
        extras = [c for c in range(1, 10) if c not in pool]
        rng.shuffle(extras)
        pool += extras
    palette = pool[:n_seeds]
    layout = (overrides.get("texture") or overrides.get("seed_layout")
              or ctx.draw_choice("seed_layout", list(SEED_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    sep = int(overrides.get("seed_separation", 1))
    g = full_grid(h, w, 0)
    cells = _layout_cells(layout, h - 1, w - 1, bias, rng)
    placed = []
    for r, c in cells:
        if all(abs(pr - r) + abs(pc - c) >= sep for pr, pc in placed):
            placed.append((r, c))
        if len(placed) >= n_seeds:
            break
    if not placed:
        placed.append((1, 1))
    for i, (r, c) in enumerate(placed):
        g[r][c] = palette[i % len(palette)]
    return g


def _layout_cells(layout, h_max, w_max, bias, rng):
    cells = [(r, c) for r in range(h_max) for c in range(w_max)]
    if layout == "diagonal":
        diag = [(k, k) for k in range(min(h_max, w_max))]
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        return diag + rest
    if layout == "anti_diag":
        anti = [(k, w_max - 1 - k) for k in range(min(h_max, w_max))]
        rest = [c for c in cells if c not in anti]
        rng.shuffle(rest)
        return anti + rest
    if layout == "row":
        r = rng.randint(0, h_max - 1)
        chosen = [(r, c) for c in range(w_max)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "col":
        c = rng.randint(0, w_max - 1)
        chosen = [(r, c) for r in range(h_max)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "corners":
        corners = [(0, 0), (0, w_max - 1),
                   (h_max - 1, 0), (h_max - 1, w_max - 1)]
        rest = [c for c in cells if c not in corners]
        rng.shuffle(rest)
        return corners + rest
    if layout == "blob":
        cr, cc = rng.randint(0, h_max - 1), rng.randint(0, w_max - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    if bias == "center":
        cr, cc = h_max // 2, w_max // 2
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    if bias == "edge":
        cells.sort(key=lambda rc: -min(rc[0], h_max - 1 - rc[0],
                                       rc[1], w_max - 1 - rc[1]))
        return cells
    rng.shuffle(cells)
    return cells



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the L-path seed invariants for ee1c3a11982c."""
    errs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 2 or w < 2:
        return ["grid too small"]
    seeds = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not seeds:
        errs.append("no nonzero seed cells")
        return errs
    bad_edge = [(r, c) for r, c, _ in seeds if r == h - 1 or c == w - 1]
    if bad_edge:
        errs.append(f"seed(s) on last row/col: {bad_edge[:5]}")
    colors = [v for _, _, v in seeds]
    if len(colors) != len(set(colors)):
        errs.append("seed colors should be distinct so paths are separately identifiable")
    return errs

def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "no_seeds":
        return g
    if name == "single_seed":
        g[1][1] = color
        return g
    if name == "all_seeds":
        for r in range(h - 1):
            for c in range(w - 1):
                if rng.random() < 0.4:
                    g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    return g
