"""Generator for arc_puzzle_bank_21_set20_bundle:medium_p01 — orientation recolor.

Rule: each blob's bbox: w > h → 2 (horizontal), h > w → 3 (vertical),
else (square) → 4. Output keeps blob shapes, only colors change.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_squares, all_same_orientation, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import SQUARE_2X2, H_LINE_3, V_LINE_3

GENERATOR_ID = "799ac8e38d8d"
VERSION = "2.0.1"
TASK_ID = "799ac8e38d8d"
SUMMARY = (
    "0-bg grid (h~8-11, w~11-13) with "
    "3 BASE BLOBS — H_LINE_3 (1×3 "
    "horizontal), V_LINE_3 (3×1 vertical), "
    "SQUARE_2X2 — plus 0-2 random EXTRA "
    "shapes (4-cell lines, 2×3/3×2 rects, "
    "3×3 squares) placed at non-touching "
    "positions in random non-2-3-4 colors "
    "(from {5,6,7,8,9} for bases, "
    "{1,2,3,4} for extras). Each blob is "
    "isolated (no 4-touching). Rule "
    "(ORIENTATION-BASED RECOLOR): for "
    "EACH 4-CONNECTED BLOB, COMPUTE its "
    "BBOX (bb_h × bb_w). RECOLOR every "
    "cell of the blob based on bbox "
    "shape: bb_w > bb_h → COLOR 2 (red, "
    "horizontal); bb_h > bb_w → COLOR 3 "
    "(green, vertical); bb_h == bb_w → "
    "COLOR 4 (yellow, square). Blob cell "
    "POSITIONS preserved; only colors "
    "change. Net: every blob recolored "
    "by orientation classifier (h-line→2, "
    "v-line→3, square→4)."
)

# Rivals: 'output is input' refuted by demos (colors recolor to 2/3/4).
# 'recolor by area' refuted by demos with same-size diff-orientation
# producing different colors. 'recolor by cell count' refuted same way.
# 'use input colors' refuted by demos (always 2/3/4). 3 demos with
# ≥1 of each orientation cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 horizontal blob (w > h), >=1 vertical blob (h > w), >=1 square (h = w)",
    "input colors aren't already the orientation colors (rule isn't identity)",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_squares", "all_same_orientation", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, blobs with at least two distinct bbox orientations (H, V, or square)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find connected components via 4-conn flood fill
    visited = [[False] * w for _ in range(h)]
    def bfs(sr, sc):
        col = grid[sr][sc]; q = [(sr, sc)]; visited[sr][sc] = True; cells = []
        while q:
            r, c = q.pop(); cells.append((r, c))
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = r+dr, c+dc
                if 0<=nr<h and 0<=nc<w and not visited[nr][nc] and grid[nr][nc]==col:
                    visited[nr][nc]=True; q.append((nr, nc))
        return cells
    orientations = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                cells = bfs(r, c)
                rs = [rr for rr, _ in cells]; cs = [cc for _, cc in cells]
                bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
                if bw > bh:
                    orientations.add("H")
                elif bh > bw:
                    orientations.add("V")
                else:
                    orientations.add("S")
    if not orientations:
        errs.append("no nonzero blobs found")
    elif len(orientations) < 2:
        errs.append(f"only orientation(s) {orientations}; expected ≥2 of H/V/S for rule to be non-trivial")
    return errs


def _bbox_dims(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) + 1, max(cs) + 1


def _free_at(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(10, 12)
        n_extras = 0
    elif difficulty == "hard":
        h = rng.randint(13, 18); w = rng.randint(15, 20)
        n_extras = rng.randint(2, 4)
    else:
        h = rng.randint(9, 12); w = rng.randint(11, 14)
        n_extras = rng.randint(0, 2)
    g = full_grid(h, w, 0)
    palette = rng.sample([5, 6, 7, 8, 9], 3)
    base_shapes = [H_LINE_3, V_LINE_3, SQUARE_2X2]
    extra_shapes = [
        [(0, 0), (0, 1), (0, 2), (0, 3)],  # horizontal line 4
        [(0, 0), (1, 0), (2, 0), (3, 0)],  # vertical line 4
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],  # 2x3 horizontal
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],  # 3x2 vertical
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],  # 3x3 square
    ]
    extras = [rng.choice(extra_shapes) for _ in range(n_extras)]
    extras_palette = rng.sample([1, 2, 3, 4], n_extras) if n_extras > 0 else []
    shapes = base_shapes + extras
    palette = palette + extras_palette
    rng.shuffle(palette)
    for shape, color in zip(shapes, palette):
        sh, sw = _bbox_dims(shape)
        for _ in range(40):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free_at(g, r0, c0, shape):
                paint_at(g, r0, c0, shape, color)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "all_squares":
        # all blobs are squares → every output cell becomes 4, no orientation contrast
        paint_at(g, 1, 1, SQUARE_2X2, 5)
        paint_at(g, 4, 5, SQUARE_2X2, 6)
        paint_at(g, 6, 9, SQUARE_2X2, 7)
        return g
    if name == "all_same_orientation":
        # only horizontal blobs → only color 2 fires, no 3 or 4 contrast
        paint_at(g, 1, 1, H_LINE_3, 5)
        paint_at(g, 4, 5, H_LINE_3, 6)
        paint_at(g, 7, 8, H_LINE_3, 7)
        return g
    if name == "no_blobs":
        # empty grid → no objects to recolor, rule no-op
        return g
    return g
