"""Generator for arc_puzzle_bank_seventh21:M44 — in-place rotate-CW each blob.

Rule: rotate each blob's bbox 90° CW in place (the rotated grid is
pasted at the same top-left corner of the original bbox, but only
within the rotated bbox dimensions).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, square_blobs, blobs_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import L_TROMINO_NE, L_TROMINO_SE

GENERATOR_ID = "860252b77847"
VERSION = "1.2.1"
TASK_ID = "860252b77847"
SUMMARY = "Several non-touching blobs (L-shapes or similar asymmetric shapes) in distinct colors. Rule: for each blob, crop to bbox, rotate 90° CW in place, then paste back at the SAME top-left corner of the original bbox (so the rotated shape occupies a flipped-dim region). Other cells become 0."

# Rivals: 'output is input' refuted by demos with asymmetric blobs.
# 'rotate 180' refuted by demos with cw rotation visible. 'rotate
# at center' refuted by demos showing paste at top-left. 'recolor'
# refuted by demos preserving colors. 3 demos with ≥2 distinct
# asymmetric shapes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "blobs are L-shapes (rotation-distinct from original)",
    "blobs don't overlap or 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "square_blobs", "blobs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "isolated_l_blobs",
                       "valid": "isolated_l_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; non-bg connected components each have 3-4 cells (L-like blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_blobs — allowed
    # Find 4-connected components
    visited = set()
    comps = []
    for sr, sc in nonzero:
        if (sr, sc) in visited:
            continue
        comp = []
        stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if grid[r][c] != 0:
                comp.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        stack.append((nr, nc))
        if comp:
            comps.append(comp)
    if not comps:
        return []
    # Square blobs: 2x2 or larger squares → degenerate allowed
    for comp in comps:
        rs = [r for r, c in comp]; cs = [c for r, c in comp]
        bh, bw = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        if bh == bw and len(comp) == bh * bw:
            return []  # degenerate square_blobs — allowed
    errs = []
    # Normal case: each blob should be 3-4 cells
    for comp in comps:
        if not (3 <= len(comp) <= 4):
            errs.append(f"expected 3-4 cell blob; got {len(comp)}")
    return errs


def _free(g, r0, c0, cells):
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 17)
        w = ctx.draw_int("grid_w", 13, 18)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(2, min(5, max(2, h // 3)))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    shapes = [L_TROMINO_NE, L_TROMINO_SE,
              [(0, 0), (1, 0), (2, 0), (2, 1)],
              [(0, 0), (0, 1), (0, 2), (1, 0)]]
    for color in palette:
        shape = rng.choice(shapes)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(40):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, shape):
                paint_at(g, r0, c0, shape, color)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no blobs to rotate.
        return g
    if name == "square_blobs":
        # Rotation-symmetric square blobs — rotate-CW is identity (no visible effect).
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 4
        for r in range(2):
            for c in range(2): g[5 + r][5 + c] = 5
        return g
    if name == "blobs_touching":
        # Two L-blobs adjacent — rotated bboxes overlap, ambiguous in-place rotate.
        g[1][1] = 4; g[2][1] = 4; g[3][1] = 4; g[3][2] = 4
        g[1][3] = 5; g[2][3] = 5; g[3][3] = 5; g[3][4] = 5
        return g
    return g
