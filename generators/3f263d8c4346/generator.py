"""Generator for arc_puzzle_bank_fourth21:M28 — keep top-bottom symmetric blobs.

Rule: keep only blobs whose normalized cells are top-bottom symmetric
within their bbox; drop the rest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_symmetric, all_asymmetric.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import (
    PLUS_5, SQUARE_2X2, T_TETROMINO, L_TROMINO_NE, L_TROMINO_SE,
)

GENERATOR_ID = "3f263d8c4346"
VERSION = "1.2.0"
TASK_ID = "3f263d8c4346"
SUMMARY = "≥1 top-bottom-symmetric blob (kept) + ≥1 top-bottom-asymmetric blob (dropped)."

INVARIANTS = [
    "background is 0",
    "≥1 top-bottom-symmetric shape (kept by rule)",
    "≥1 top-bottom-asymmetric shape (dropped by rule)",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_symmetric", "all_asymmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "mixed_symmetry_blobs",
                       "valid": "mixed_symmetry_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blobs|all_symmetric|all_asymmetric"},
}


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _top_bottom_symmetric(cells):
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    norm = {(r - min_r, c - min(c for _, c in cells)) for r, c in cells}
    height = max_r - min_r
    return {(height - r, c) for r, c in norm} == norm


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify both top-bottom kept and dropped blob branches are present."""
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
    comps = _components(grid)
    if len(comps) < 2:
        errs.append(f"expected at least two isolated blobs, found {len(comps)}")
    has_sym = any(_top_bottom_symmetric(comp) for comp in comps)
    has_asym = any(not _top_bottom_symmetric(comp) for comp in comps)
    if not has_sym:
        errs.append("no top-bottom-symmetric blob present")
    if not has_asym:
        errs.append("no top-bottom-asymmetric blob present")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-zero colors, found {len(colors)}")
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


SYMMETRIC = [PLUS_5, SQUARE_2X2]
ASYMMETRIC = [T_TETROMINO, L_TROMINO_NE, L_TROMINO_SE]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    shapes = [rng.choice(SYMMETRIC), rng.choice(ASYMMETRIC), rng.choice(SYMMETRIC)]
    placed = 0
    for shape, color in zip(shapes, palette):
        sh, sw = _bbox_dims(shape)
        for _ in range(120):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free_at(g, r0, c0, shape):
                paint_at(g, r0, c0, shape, color)
                placed += 1
                break
    if placed != len(shapes):
        raise ValueError("could not place required symmetry-branch blobs")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no candidates to filter.
        return g
    if name == "all_symmetric":
        # All blobs top-bottom-symmetric — rule's "drop asymmetric" branch
        # never fires; output equals input.
        paint_at(g, 1, 1, PLUS_5, 4)
        paint_at(g, 5, 7, SQUARE_2X2, 6)
        return g
    if name == "all_asymmetric":
        # All blobs top-bottom-asymmetric — rule's "keep symmetric" branch
        # never fires; output is empty.
        paint_at(g, 1, 1, L_TROMINO_NE, 4)
        paint_at(g, 5, 7, L_TROMINO_SE, 6)
        return g
    return g
