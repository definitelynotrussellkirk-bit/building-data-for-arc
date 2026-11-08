"""Generator for arc_puzzle_bank_next21:H10 — rotate each object 180 in bbox.

Rule: each connected component is rotated 180° within its own bounding box.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, point_symmetric_blob, single_cell_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3d0bcc09b993"
VERSION = "1.1.1"
TASK_ID = "3d0bcc09b993"

SUMMARY = "2-3 connected motifs in distinct colors at separate positions."

INVARIANTS = [
    "background is 0",
    "2-3 motifs in distinct non-zero colors",
    "each motif is non-symmetric (180-rotation differs from itself)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "point_symmetric_blob", "single_cell_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "n":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "asymmetric_blobs",
                       "valid": "asymmetric_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blobs|point_symmetric_blob|single_cell_blob"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-zero colors (motifs in distinct colors)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-zero colors, found {len(colors)}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


L_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 2)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            shape = list(rng.choice(L_SHAPES))
            rs = [r for r, _ in shape]; cs = [c for _, c in shape]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in shape:
                    g[r0 + r][c0 + c] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize H10 layout")


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no shapes to rotate.
        return g
    if name == "point_symmetric_blob":
        # 2x2 blocks (180-symmetric) — rule's rotation is identity;
        # effect invisible.
        for r in range(1, 3):
            for c in range(1, 3): g[r][c] = 4
        for r in range(3, 5):
            for c in range(6, 8): g[r][c] = 6
        return g
    if name == "single_cell_blob":
        # 1-cell objects — bbox is 1x1; rotation is trivially
        # identity.
        g[2][2] = 4; g[3][6] = 6
        return g
    return g
