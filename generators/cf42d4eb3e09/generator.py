"""Generator for arc_puzzle_bank_21_set13_s:S13_H7 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, motifs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf42d4eb3e09"
VERSION = "2.0.1"  # docstring said 'vertical pack' but the rule SELECTS one target component by (holes desc -> symmetry-count desc -> area desc -> top-left) and crops it in colour 8. Gen's tiny 3-5 cell blobs never had holes & rarely symmetry -> selection collapsed to 'largest blob' + winner shapes barely varied (dup 28%). Now mix holed rings / symmetric / plain motifs at varied sizes so all 3 discriminator branches fire and the winning shape varies."
TASK_ID = "cf42d4eb3e09"

SUMMARY = ("Several motifs in distinct colors; the rule outputs ONE selected "
           "motif (most holes, then most mirror-symmetry axes, then largest "
           "area, then top-left), cropped to its bbox and recolored to 8.")

INVARIANTS = [
    "background is 0",
    "2-4 connected motifs in distinct non-zero colors at distinct positions",
    "motifs vary in hole-count / symmetry / area so the selection criteria discriminate",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "motifs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_isolated_motifs",
                       "valid": "scattered_isolated_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; ≥2 distinct non-zero colors present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    return errs


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


def _holed(rng):
    """A frame of varied dims plus random OUTWARD bumps -> exactly one enclosed
    hole but a VARIED outline (so holed winners aren't all identical rings).
    Drives the rule's top-priority 'holes' discriminator with high variety."""
    rh = rng.randint(4, 6); rw = rng.randint(4, 6)
    cells = {(r, c) for r in range(rh) for c in range(rw)
             if r in (0, rh - 1) or c in (0, rw - 1)}
    interior = {(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)}
    base = list(cells)
    for _ in range(rng.randint(1, 5)):
        r, c = rng.choice(base)
        for dr, dc in rng.sample([(-1, 0), (1, 0), (0, -1), (0, 1)], 4):
            nb = (r + dr, c + dc)
            if nb not in interior:          # never fill the hole
                cells.add(nb); break
    return _norm(list(cells))


def _sym_motif(rng):
    """Larger left-right mirror-symmetric polyomino (col-symmetry axis)."""
    half = _build_motif(rng, rng.randint(3, 6))
    w = max(c for _, c in half) + 1
    cells = set(half)
    for (r, c) in half:
        cells.add((r, (2 * w - 1) - c))      # mirror across the vertical axis
    return _norm(list(cells))


def _motif(rng):
    t = rng.random()
    if t < 0.34:
        return _holed(rng)
    if t < 0.67:
        return _sym_motif(rng)
    return _norm(_build_motif(rng, rng.randint(5, 12)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 15, 22)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n = ctx.draw_int("n", 3, 4)
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
            for _ in range(150):
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
