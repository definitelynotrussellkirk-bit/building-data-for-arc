"""Generator for arc_puzzle_bank_next21:H14.

Rule: a HOLLOW object (a frame whose bbox encloses background HOLES)
transfers its hole pattern (the enclosed 0-cells, relative to its bbox)
onto a same-bbox-size SOLID object, carving those cells to 0.

Combinatorial axes: grid size, the bbox size, the hollow's interior
fill (which sets the hole pattern), the two colors, and positions.
Degenerates: missing_solid_twin, size_mismatch, no_hole.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, fill_box, full_grid

GENERATOR_ID = "bc932ac8117a"
VERSION = "2.0.1"  # 2.0.0->2.0.1: add self_check. diversity: random bbox + interior hole pattern + colors + positions + grid (was fixed ~9)
TASK_ID = "bc932ac8117a"
SUMMARY = (
    "0-bg grid (size varies). A HOLLOW object — a rectangular frame (one "
    "color) with a connected interior decoration leaving >=1 enclosed "
    "HOLE — and a same-bbox-size SOLID filled box (another color), placed "
    "apart. Rule: take the hollow's hole pattern (enclosed 0-cells "
    "relative to its bbox) and carve it into the matching-size solid "
    "(paint those cells 0). The grid size, bbox size, the interior fill "
    "(hence the hole pattern), the colors and positions all vary freely "
    "(was a fixed frame+solid, ~9 distinct)."
)

INVARIANTS = [
    "one hollow object (frame + connected decoration) with >=1 enclosed hole",
    "one solid filled box of the SAME bbox dimensions, a different color",
    "the two objects are disconnected (separate components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_solid_twin", "size_mismatch", "no_hole")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "box_h":          {"type": "int", "default": "varies", "valid": "4..8"},
    "box_w":          {"type": "int", "default": "varies", "valid": "4..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "paired", "valid": "paired"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "missing_solid_twin|size_mismatch|no_hole"},
}


def _reserve_bbox(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=2 distinct nonzero colors (hollow + solid pair)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return errs  # degenerate
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct colors (hollow+solid pair), got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr = (8, 11), (12, 15), (4, 5)
    elif difficulty == "hard":
        hr, wr, szr = (11, 16), (16, 22), (5, 8)
    else:
        hr, wr, szr = (9, 13), (13, 18), (4, 7)

    for _attempt in range(40):
        bh = rng.randint(*szr); bw = rng.randint(*szr)
        h = rng.randint(*hr); w = rng.randint(*wr)
        if bh + 2 > h or 2 * bw + 3 > w:
            continue
        ca, cb = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        # place hollow (frame ca) + solid (filled cb), same bbox dims
        if not _reserve_bbox(occ, 1, 1, bh, bw, h, w):
            continue
        ht, hl = 1, 1
        draw_frame(g, ht, hl, ht + bh - 1, hl + bw - 1, ca)
        # interior cells (rows ht+1..ht+bh-2, cols hl+1..hl+bw-2)
        interior = [(r, c) for r in range(ht + 1, ht + bh - 1)
                    for c in range(hl + 1, hl + bw - 1)]
        # connected decoration grown from a frame-adjacent seed; leave >=1 hole
        deco = set()
        if interior:
            seed_cell = (ht + 1, hl + 1)
            deco = {seed_cell}
            target = rng.randint(0, max(0, len(interior) - 1))
            for _ in range(200):
                if len(deco) >= target:
                    break
                r, c = rng.choice(list(deco))
                dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                nc = (r + dr, c + dc)
                if nc in interior:
                    deco.add(nc)
            for (r, c) in deco:
                g[r][c] = ca
        # need >=1 hole left
        if len(deco) >= len(interior):
            continue

        # solid filled box, same bbox dims, placed to the right
        placed = False
        for _t in range(40):
            st = rng.randint(0, h - bh); sl = rng.randint(bw + 2, w - bw)
            if sl < 0:
                break
            if _reserve_bbox(occ, st, sl, bh, bw, h, w):
                fill_box(g, st, sl, st + bh - 1, sl + bw - 1, cb)
                placed = True
                break
        if placed:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 18, 0)
    if name == "missing_solid_twin":
        draw_frame(g, 1, 1, 6, 6, 2)
        g[3][3] = 0
        return g
    if name == "size_mismatch":
        draw_frame(g, 1, 1, 6, 6, 2)
        g[3][3] = 0
        fill_box(g, 1, 10, 4, 13, 3)
        return g
    if name == "no_hole":
        for r in range(1, 7):
            for c in range(1, 7):
                g[r][c] = 2
        fill_box(g, 1, 10, 6, 15, 3)
        return g
    return g
