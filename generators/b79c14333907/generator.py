"""Generator for arc_additional_puzzle_bank_volume20:H138.

Rule: open maze cells are partitioned by nearest seed (BFS through
walls), with tie cells colored cyan.

Combinatorial axes (9): grid_h/w, palette_kind, anchor_row,
seed_distance, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: seeds_collide, no_walls, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b79c14333907"
# 1.2.0: seeds were SYMMETRIC same-row +-2 offset with NO interior walls ->
# repetitive vertical splits (uniq=0.28, dup-outputs). Now seeds placed at
# random distinct interior positions + interior 5-walls -> rich BFS Voronoi.
# 1.3.0: FIX identity -- interior walls could split the two seeds into separate
# open regions; the rule paints only cells reachable from BOTH seeds, so a split
# left every 0-cell untouched (output == input). Both seeds now drawn from the
# SAME connected open component.
VERSION = "1.3.0"
TASK_ID = "b79c14333907"
SUMMARY = (
    "0-bg maze bordered by color-5 walls, with extra interior color-5 walls, "
    "and two seeds (color 2 and color 3) at random distinct open interior "
    "positions. Rule: BFS distance from each seed through open (non-5) cells; "
    "each open cell is painted by its NEARER seed's color (2 or 3), or 8 on a "
    "tie. Seed positions and the interior wall layout vary freely."
)

INVARIANTS = [
    "background is 0",
    "border cells are color-5 walls; extra interior 5-walls may exist",
    "there is one seed color 2 and one seed color 3 at distinct open cells",
    "both seeds lie in open (non-wall) interior cells",
]

PALETTE_KINDS = ("default", "tight_corridor", "wide_chamber", "off_center_seeds")
DEGENERATE_TEXTURES = ("seeds_collide", "no_walls", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 9..15", "valid": "7..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_distance":  {"type": "int", "default": "4", "valid": "2..8"},
    "anchor_row":     {"type": "str", "default": "rng",
                       "valid": "top|middle|bottom"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        wall_frac = 0.05
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        wall_frac = 0.18
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 9, 16)
        wall_frac = 0.12
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # border walls
    for r in range(h):
        g[r][0] = 5
        g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5
        g[h - 1][c] = 5

    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    # interior walls: a mix of scattered cells and a few short segments
    n_walls = int(len(interior) * wall_frac)
    rng.shuffle(interior)
    for (r, c) in interior[:n_walls]:
        g[r][c] = 5
    # an occasional partial wall line (like the canonical 5-column)
    if rng.random() < 0.5 and w > 6:
        wc = rng.randint(2, w - 3)
        gap = rng.randint(1, h - 2)
        for r in range(1, h - 1):
            if r != gap:
                g[r][wc] = 5

    open_cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                  if g[r][c] == 0]
    if len(open_cells) < 2:
        # too dense; fall back to clearing interior walls
        for (r, c) in interior:
            if g[r][c] == 5:
                g[r][c] = 0
        open_cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    # Both seeds MUST lie in the SAME connected open region. The rule paints a
    # 0-cell only when it is reachable from BOTH seeds; if interior walls split
    # the seeds into different regions their reachable sets are disjoint, no
    # cell is reachable from both, and the rule does nothing -> identity.
    comps = [comp for comp in _open_components(g) if len(comp) >= 2]
    if not comps:
        for (r, c) in interior:
            if g[r][c] == 5:
                g[r][c] = 0
        comps = [comp for comp in _open_components(g) if len(comp) >= 2]
    comp = max(comps, key=len)
    a, b = rng.sample(comp, 2)
    g[a[0]][a[1]] = 2
    g[b[0]][b[1]] = 3
    return g


def _open_components(g):
    """Connected components (4-conn) of non-wall (non-5) cells."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or g[sr][sc] == 5:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] != 5):
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """The color-2 and color-3 seeds must lie in the SAME connected open region,
    so cells reachable from both exist and the rule paints them. Returns
    violation list."""
    h, w = len(grid), len(grid[0])
    pos2 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    pos3 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(pos2) != 1 or len(pos3) != 1:
        return [f"need exactly one color-2 and one color-3 seed, got "
                f"{len(pos2)}/{len(pos3)}"]
    for comp in _open_components(grid):
        cs = set(comp)
        if pos2[0] in cs and pos3[0] in cs:
            return []
    return ["the two seeds are in different open regions -> rule is identity"]


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "seeds_collide":
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 5
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 5
        mid = w // 2
        g[5][mid] = 2
        g[5][mid + 1] = 3
        return g
    if name == "no_walls":
        mid = w // 2
        g[5][mid - 2] = 2
        g[5][mid + 2] = 3
        return g
    if name == "no_seeds":
        for r in range(h):
            g[r][0] = 5
            g[r][w - 1] = 5
        for c in range(w):
            g[0][c] = 5
            g[h - 1][c] = 5
        return g
    return g
