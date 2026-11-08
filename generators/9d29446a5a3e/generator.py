"""Generator for e760a62e.

Rule: color-8 lines (rows/cols that are >half 8) divide a coarse lattice.
Colored dots map to coarse coordinates; for each color, same-coarse-row or
same-coarse-col dot pairs fill the coarse cells between them (two different
colors over a cell -> 6). Output: 8 lines stay 8; every other cell takes
its coarse cell's fill color.

This generator builds a full-8-line lattice and places aligned same-color
dot pairs (and optional crossings for 6).

Combinatorial axes: grid size, the lattice lines, the dot colors and
aligned positions.
Degenerates: no_lines, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d29446a5a3e"
VERSION = "2.1.0"  # add executable lattice/dot-pair self_check
TASK_ID = "9d29446a5a3e"
SUMMARY = (
    "0-bg grid (size varies) with full color-8 lattice lines and colored "
    "dots. Rule: dots map to coarse lattice cells; same-coarse-row/col "
    "same-color dot pairs fill the coarse cells between them (color "
    "conflicts -> 6); output expands each coarse cell's fill (8 lines stay "
    "8). The grid size, lattice and dot colors/positions vary freely (was a "
    "fixed setup, ~25 distinct)."
)

INVARIANTS = [
    "color-8 lines (>half 8) divide the coarse lattice",
    "each color's aligned dot pairs fill the coarse cells between them",
    "two colors over a coarse cell -> 6; output expands the coarse fill",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines", "no_dots", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..22"},
    "n_hlines":       {"type": "int", "default": "varies", "valid": "1..3"},
    "n_vlines":       {"type": "int", "default": "varies", "valid": "1..3"},
    "n_colors":       {"type": "int", "default": "varies", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "lattice_dots", "valid": "lattice_dots"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_lines|no_dots|full_grid"},
}


def _lines(rng, N, k):
    """k full-line positions in [1,N-2], segments (incl edges) >=2 wide."""
    for _ in range(40):
        ws = sorted(rng.sample(range(1, N - 1), k)) if k > 0 else []
        bounds = [-1] + ws + [N]
        if all(bounds[i + 1] - bounds[i] - 1 >= 2 for i in range(len(bounds) - 1)):
            return ws
    return None


def _segments(ws, N):
    bounds = [-1] + ws + [N]
    return [(bounds[i] + 1, bounds[i + 1] - 1)
            for i in range(len(bounds) - 1) if bounds[i + 1] - 1 >= bounds[i] + 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, lr, kr = (12, 14), (12, 14), (1, 2), (2, 2)
    elif difficulty == "hard":
        hr, wr, lr, kr = (16, 22), (16, 22), (2, 3), (3, 4)
    else:
        hr, wr, lr, kr = (13, 18), (13, 18), (1, 3), (2, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        hl = _lines(rng, h, rng.randint(*lr)); vl = _lines(rng, w, rng.randint(*lr))
        if hl is None or vl is None:
            continue
        row_segs = _segments(hl, h); col_segs = _segments(vl, w)
        Gr = len(row_segs); Gc = len(col_segs)
        if Gr < 2 and Gc < 2:
            continue

        g = full_grid(h, w, 0)
        for r in hl:
            for c in range(w):
                g[r][c] = 8
        for c in vl:
            for r in range(h):
                g[r][c] = 8

        occ = set()

        def place_dot(gr, gc, color):
            r0, r1 = row_segs[gr]; c0, c1 = col_segs[gc]
            for _t in range(30):
                r = rng.randint(r0, r1); c = rng.randint(c0, c1)
                if (r, c) not in occ:
                    g[r][c] = color; occ.add((r, c)); return True
            return False

        colors = rng.sample([1, 2, 3, 4, 5, 7, 9], rng.randint(*kr))
        connections = 0
        for color in colors:
            if Gc >= 2 and (Gr < 2 or rng.random() < 0.5):
                gr = rng.randint(0, Gr - 1)
                gc1, gc2 = rng.sample(range(Gc), 2)
                if place_dot(gr, gc1, color) and place_dot(gr, gc2, color):
                    connections += 1
            elif Gr >= 2:
                gc = rng.randint(0, Gc - 1)
                gr1, gr2 = rng.sample(range(Gr), 2)
                if place_dot(gr1, gc, color) and place_dot(gr2, gc, color):
                    connections += 1
        if connections >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    for c in range(11):
        g[5][c] = 8
    for r in range(11):
        g[r][5] = 8
    g[2][1] = 3; g[2][8] = 3      # same coarse row -> fill
    if name == "no_lines":
        return full_grid(11, 11, 0)
    if name == "no_dots":
        g[2][1] = 0; g[2][8] = 0
        return g
    if name == "full_grid":
        return full_grid(11, 11, 8)
    return g


def _line_segments(lines, n):
    bounds = [-1] + sorted(lines) + [n]
    return [(bounds[i] + 1, bounds[i + 1] - 1) for i in range(len(bounds) - 1)]


def _seg_index(segs, x):
    for i, (a, b) in enumerate(segs):
        if a <= x <= b:
            return i
    return None


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    hlines = [r for r in range(h) if sum(v == 8 for v in grid[r]) > w // 2]
    vlines = [c for c in range(w) if sum(grid[r][c] == 8 for r in range(h)) > h // 2]
    if not hlines or not vlines:
        errs.append("expected at least one full-ish color-8 row and column lattice line")
        return errs
    row_segs = _line_segments(hlines, h)
    col_segs = _line_segments(vlines, w)
    dots_by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v not in (0, 8):
                gr = _seg_index(row_segs, r)
                gc = _seg_index(col_segs, c)
                if gr is None or gc is None:
                    errs.append("colored dot lies on a lattice line instead of inside a coarse cell")
                dots_by_color.setdefault(v, []).append((gr, gc))
    if sum(len(v) for v in dots_by_color.values()) < 2:
        errs.append("expected at least one aligned colored dot pair")
    aligned = False
    for pts in dots_by_color.values():
        for i, (r1, c1) in enumerate(pts):
            for r2, c2 in pts[i + 1:]:
                if r1 == r2 or c1 == c2:
                    aligned = True
    if not aligned:
        errs.append("no same-color dot pair shares a coarse row or coarse column")
    return errs
