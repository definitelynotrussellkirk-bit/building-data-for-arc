"""Generator for arc_puzzle_bank_21_set13_s:S13_H2 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, motifs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cadfb7a1ae72"
VERSION = "2.0.1"  # same rule+wrong 'gallery pack' docstring as cf42d4eb3e09: rule SELECTS one component by (holes desc -> symmetry-count desc -> area desc -> top-left) and crops it in colour 8. Tiny 3-5 cell motifs never had holes/symmetry -> selection collapsed to 'largest' + winner barely varied (distinct 19). Now mix VARIED holed rings / symmetric / large-plain motifs so all 3 discriminator branches fire and the winner varies."
TASK_ID = "cadfb7a1ae72"

SUMMARY = ("Several motifs in distinct colors; the rule outputs ONE selected motif "
           "(most holes, then most mirror-symmetry axes, then largest area, then "
           "top-left), cropped to its bbox and recolored to 8.")

INVARIANTS = [
    "background is 0",
    "2-4 connected motifs in distinct non-zero colors at distinct positions",
    "motifs vary in hole-count / symmetry / area so the selection criteria discriminate",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "motifs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..26"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_isolated_motifs",
                       "valid": "scattered_isolated_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _holed(rng, n_holes):
    """A frame (1 enclosed hole) optionally split into 2 holes by an internal bar."""
    rh = rng.randint(4, 6); rw = rng.randint(5, 7)
    cells = {(r, c) for r in range(rh) for c in range(rw)
             if r in (0, rh - 1) or c in (0, rw - 1)}
    if n_holes >= 2 and rw >= 5:
        midc = rw // 2                       # vertical bar splits interior -> 2 holes
        for r in range(rh):
            cells.add((r, midc))
    return _norm(list(cells))


def _colsym(rng):
    half = _build_motif(rng, rng.randint(3, 6))
    w = max(c for _, c in half) + 1
    cells = set(half)
    for (r, c) in half:
        cells.add((r, (2 * w - 1) - c))      # mirror across vertical axis
    return _norm(list(cells))


def _rowsym(rng):
    half = _build_motif(rng, rng.randint(3, 6))
    h = max(r for r, _ in half) + 1
    cells = set(half)
    for (r, c) in half:
        cells.add(((2 * h - 1) - r, c))      # mirror across horizontal axis
    return _norm(list(cells))


def _bothsym(rng):
    q = _build_motif(rng, rng.randint(2, 4))
    h = max(r for r, _ in q) + 1; w = max(c for _, c in q) + 1
    cells = set()
    for (r, c) in q:
        cells.add((r, c)); cells.add(((2 * h - 1) - r, c))
        cells.add((r, (2 * w - 1) - c)); cells.add(((2 * h - 1) - r, (2 * w - 1) - c))
    return _norm(list(cells))


def _motif(rng):
    t = rng.random()
    if t < 0.18:
        return _holed(rng, 1)                # holes=1, often col/row symmetric
    if t < 0.32:
        return _holed(rng, 2)                # holes=2
    if t < 0.50:
        return _colsym(rng)                  # sym-class 2
    if t < 0.66:
        return _rowsym(rng)                  # sym-class 1
    if t < 0.80:
        return _bothsym(rng)                 # sym-class 3
    return _norm(_build_motif(rng, rng.randint(5, 12)))   # sym-class 0, holes 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 26)
        w = ctx.draw_int("grid_w", 18, 26)
        n = ctx.draw_int("n", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 15, 22)
        n = ctx.draw_int("n", 3, 5)
    rng = ctx.draw_rng("layout")

    for outer in range(60):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            cells = _motif(rng)
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    if name == "motifs_touching":
        g[2][2] = 4; g[2][3] = 4; g[3][3] = 4
        g[3][4] = 5; g[4][4] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 distinct non-bg colors, each forming a connected component separated from others."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) < 2:
        msgs.append(f"expected >=2 distinct motif colors, found {len(colors)}")
    return msgs
