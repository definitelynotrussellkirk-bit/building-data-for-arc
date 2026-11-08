"""Generator for 5b:hard_34 — overlay count map from components.

Rule: take normalized binary masks of all components and overlay them;
output is the per-cell count (0→0, 1→2, 2→3, 3→4, 4+→6).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, single_component, all_same_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea3fc2d64936"
VERSION = "2.1.0"  # add executable overlay-count invariants; sample distinct normalized shapes and fail closed if component placement under-fills. Previous default could rarely leak all-same-shape degenerates. Bigger shapes (3-6 cells, all share (0,0) so the count-buckets incl 4+/6 stay covered) -> bigger/varied crops; n 3-5 (4+ bucket more often); bigger grids
TASK_ID = "ea3fc2d64936"
SUMMARY = "3-5 separated components in distinct colors (each 3-6 cells, all containing the top-left cell). Rule: crop+normalize each component to a binary mask, overlay all masks top-left-aligned, output the per-cell count mapped 1->2, 2->3, 3->4, 4+->6 (output dims = max crop size)."

INVARIANTS = [
    "background is 0",
    "3-4 isolated components in distinct colors",
    "each component has 3-5 cells (so overlay is non-trivial)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_component", "all_same_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "rng 3..5 by diff", "valid": "3..8"},
    "palette_size":   {"type": "int", "default": "= n_components", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "scattered_components",
                       "valid": "scattered_components"},
    "n_distinct_colors": {"type": "int", "default": "= n_components", "valid": "3..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


# every shape contains (0,0) so the overlaid masks share a top-left cell ->
# the count there equals the component count, keeping the high buckets (3->4,
# 4+->6) reachable.
_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)],          # P-pentomino
    [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)],          # 5
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],          # L
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],          # Z-ish
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],  # 3x2 block (6)
    [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)],  # C (6)
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],          # 4-tall L (bbox 4x2)
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)],          # 4-wide L (bbox 2x4)
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    n = min(n, 8)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        shapes = rng.sample(_SHAPES, n)
        if all(_place(g, rng, shape, color) for color, shape in zip(palette, shapes)):
            return g
    raise ValueError("could not place all overlay components")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, tuple(cells)))
    return comps


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    msgs = []
    comps = _components(grid)
    if not (3 <= len(comps) <= 5):
        msgs.append(f"expected 3-5 isolated components, found {len(comps)}")
    colors = [c for c, _ in comps]
    if len(colors) != len(set(colors)):
        msgs.append("components should have distinct colors")
    shapes = [_norm(cells) for _, cells in comps]
    if len(set(shapes)) <= 1:
        msgs.append("all normalized component masks are identical; overlay gradient is hidden")
    for color, cells in comps:
        if len(cells) < 3:
            msgs.append(f"component color {color} has fewer than 3 cells")
        if (0, 0) not in _norm(cells):
            msgs.append(f"component color {color} does not normalize to a top-left occupied cell")
    return sorted(set(msgs))


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no masks to overlay.
        return g
    if name == "single_component":
        # Only 1 component — rule's overlay count never exceeds 1
        # (encoded as 2); count map collapses to a single mask.
        for r, c in [(3, 4), (4, 4), (4, 5), (5, 5)]: g[r][c] = 4
        return g
    if name == "all_same_shape":
        # All components have identical shape, placed apart —
        # overlay count map is a constant N (encoded as the
        # corresponding bucket); rule's gradient is invisible.
        for r, c in [(0, 0), (0, 1), (1, 0)]: g[r][c] = 4
        for r, c in [(0, 4), (0, 5), (1, 4)]: g[r][c] = 6
        for r, c in [(5, 0), (5, 1), (6, 0)]: g[r][c] = 7
        return g
    return g
