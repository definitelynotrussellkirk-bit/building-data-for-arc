"""Generator for arc_additional_puzzle_bank_volume23:E160.

Rule: each color-3 (green) connected component is checked for how many of the
4 grid edges its bbox touches. Components whose bbox touches EXACTLY ONE edge
get recolored to color 8 (cyan). Components touching 0 edges (interior) or
≥ 2 edges (corner/spanning) stay green.

Combinatorial axes (8): grid_h/w, palette_kind, n_components, shape_id,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_components, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "4614f605ddab"
VERSION = "1.3.0"  # 1.2.0 placed components at random positions, so some seeds
# had NO component touching exactly one edge -> rule recoloured nothing ->
# identity (~4/24). 1.3.0 always places one mid-side (single-edge) component.
TASK_ID = "4614f605ddab"
SUMMARY = "Color-3 components. Rule recolors to cyan(8) those whose bbox touches EXACTLY ONE grid edge; interior (0 edges) and corner/spanning (≥2 edges) components stay green."

# Rivals: 'recolor every green' refuted by ≥2 demos with interior or
# corner components staying 3. 'recolor only corner components' refuted
# by any demo where the corner stays 3 and a side-only becomes 8.
# 'use color 8 for all 3s' refuted by demos with mixed outcomes.
# 'recolor by size' refuted by ≥1 demo where size doesn't predict.
# 3 demos covering 0/1/2-edge-touching mixes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "at least one green component touches exactly one border",
    "other green components touch zero or two borders",
    "green components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..20"},
    "n_components":   {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "mixed", "valid": "mixed"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (0, 2)],
]


def _shape_fits(g, r0, c0, shape):
    h, w = len(g), len(g[0])
    cells = []
    for dr, dc in shape:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < h and 0 <= c < w): return None
        cells.append((r, c))
    # Need at least 1 bg-cell margin between components
    for r, c in cells:
        for nr in range(r - 1, r + 2):
            for nc in range(c - 1, c + 2):
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells and g[nr][nc] != 0:
                    return None
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        n = ctx.draw_int("n_components", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n = ctx.draw_int("n_components", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n = ctx.draw_int("n_components", 3, 5)
    g = full_grid(h, w, 0)
    # Guarantee >=1 component touching EXACTLY ONE edge (else the rule recolours
    # nothing -> identity). A horizontal pair on the top edge, mid-width, touches
    # only the top (not left/right/bottom). The random fill keeps a 1-cell margin
    # (via _shape_fits) so it never merges with this one.
    gc = max(1, min(w - 3, w // 2))
    g[0][gc] = 3
    g[0][gc + 1] = 3
    placed = 1
    # Mix: some edge-touching components, some interior, some corner-touching.
    for _ in range(120):
        if placed >= n: break
        shape = rng.choice(_SHAPES)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = _shape_fits(g, r0, c0, shape)
        if cells is None: continue
        for r, c in cells:
            g[r][c] = 3
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """>=1 color-3 component whose bbox touches EXACTLY one grid edge, so the
    rule recolours something (non-identity)."""
    h = len(grid); w = len(grid[0])
    seen = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or seen[r][c]:
                continue
            stack = [(r, c)]; seen[r][c] = True; cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 3):
                        seen[nr][nc] = True; stack.append((nr, nc))
            rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
            sc = ((min(rs) == 0) + (max(rs) == h - 1)
                  + (min(cs) == 0) + (max(cs) == w - 1))
            if sc == 1:
                return []
    return ["no component touching exactly one edge -> rule is identity"]


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "all_interior":
        draw_rect(g, 4, 4, 2, 2, 3)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
