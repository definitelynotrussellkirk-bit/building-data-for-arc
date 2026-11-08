"""Generator for 9720b24f.

Rule: intruder pixels inside a shape component's convex hull are removed.

Combinatorial axes (8): grid_h/w, size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_shell, no_intruder, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "2a673eec7c28"
RULE_HASH = "844928233fa8"  # canonical rule this generator was written against
VERSION = "2.0.1"
TASK_ID = "2a673eec7c28"
SUMMARY = "Intruder pixels inside a shape component's convex hull are removed."

INVARIANTS = [
    "a same-color component forms a convex enclosing outline",
    "nonzero cells of other colors appear inside that component's convex hull",
    "intruder pixels are erased to background while the enclosing component is preserved",
]

SIZE_KINDS = ("S6", "S7", "S8")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shell", "no_intruder", "full_grid")
HELPFUL_TEXTURES = SIZE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..18", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 11..18", "valid": "8..24"},
    "size":           {"type": "choice", "default": "rng helpful",
                       "valid": "6|7|8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for size",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct non-zero colors (shell + intruder)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_shell", "no_intruder", "full_grid"):
        return []
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-zero colors (shell + intruder), found {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # rule: for each colour, take components >=3 cells, compute their convex hull, and
    # erase OTHER-colour cells inside the hull. So place several independent
    # shell(rectangle frame) + interior-intruder groups; rule reads h,w so vary size.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 8, 12); n_groups = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 24); n_groups = rng.randint(2, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 18); w = ctx.draw_int("grid_w", 11, 18); n_groups = rng.randint(1, 2)
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]
    color_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(color_pool)
    cidx = 0
    placed = 0
    for _attempt in range(200):
        if placed >= n_groups or cidx + 1 >= len(color_pool):
            break
        fh = rng.randint(4, 7); fw = rng.randint(4, 7)
        if fh > h or fw > w:
            continue
        r1 = rng.randint(0, h - fh); c1 = rng.randint(0, w - fw)
        r2, c2 = r1 + fh - 1, c1 + fw - 1
        # require a 1-cell gap around the box
        if any(occ[r][c] for r in range(max(0, r1 - 1), min(h, r2 + 2))
               for c in range(max(0, c1 - 1), min(w, c2 + 2))):
            continue
        shell = color_pool[cidx]; intruder = color_pool[cidx + 1]; cidx += 2
        draw_frame(g, r1, c1, r2, c2, shell)
        # 1-4 intruder cells in the interior (compact, away from the frame)
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        if interior:
            k = min(len(interior), rng.randint(1, 4))
            for (r, c) in rng.sample(interior, k):
                g[r][c] = intruder
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                occ[r][c] = True
        placed += 1
    if placed == 0:                     # fallback: guarantee at least one group
        draw_frame(g, 1, 1, min(h - 1, 6), min(w - 1, 6), color_pool[0])
        g[3][3] = color_pool[1]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_shell":
        g[6][6] = 4
        return g
    if name == "no_intruder":
        draw_frame(g, 2, 2, 8, 8, 3)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 3
        return g
    return g
