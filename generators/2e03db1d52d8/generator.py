"""Generator for arc_additional_puzzles_21_set21_bundle:M145 — Recolor by hole count.

Rule: each obj recolored to 3/4/5/6 by hole count (0/1/2/else).
Same shape as M55/M161 family.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_obj,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid, all_holed, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import has_neighbor

GENERATOR_ID = "2e03db1d52d8"
VERSION = "1.1.1"
TASK_ID = "2e03db1d52d8"
SUMMARY = "Mix of solid/frame/double-frame objects; recolor by hole count."

INVARIANTS = [
    "between 2 and 3 non-touching objects",
    "objects span hole counts: at least solid (0) and frame (1)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "all_holed", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10",  "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_obj":          {"type": "int", "default": "rng 2..3",   "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "left_to_right_pack",
                       "valid": "left_to_right_pack"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _solid(rh, rw):
    return {(r, c) for r in range(rh) for c in range(rw)}


def _frame(rh, rw):
    cells = set()
    for c in range(rw): cells.add((0, c)); cells.add((rh-1, c))
    for r in range(rh): cells.add((r, 0)); cells.add((r, rw-1))
    return cells


def _double_frame(rh, rw):
    cells = _frame(rh, rw)
    for c in range(rw): cells.add((rh//2, c))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 4-connected non-bg components (solid/frame/dbl-frame objects)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    nonzero = set((r, c) for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not nonzero:
        return ["no non-bg cells found"]
    visited = set(); n_comp = 0
    for start in nonzero:
        if start in visited:
            continue
        n_comp += 1
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in nonzero and nb not in visited:
                    queue.append(nb)
    if n_comp < 2:
        return [f"expected >=2 4-connected objects (solid/frame/dbl), got {n_comp}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 12, 14)
        n_obj = ctx.draw_int("n_obj", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 16, 18)
        n_obj = ctx.draw_int("n_obj", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 12, 18)
        n_obj = ctx.draw_int("n_obj", 2, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    plans = ["solid", "frame"] + (["dbl"] if n_obj >= 3 else [])
    rng.shuffle(plans)
    color_rng = ctx.draw_rng("colors")
    cur_c = 1; used = set()
    for kind in plans:
        if kind == "solid":
            cells = _solid(rng.randint(2, 3), rng.randint(2, 3))
        elif kind == "frame":
            cells = _frame(4, 4)
        else:
            cells = _double_frame(5, 4)
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bh = max(rs)-min(rs)+1; bw = max(cs)-min(cs)+1
        if cur_c + bw + 1 >= w: continue
        rr = rng.randint(0, h - bh); rc = cur_c
        placed = {(rr+r-min(rs), rc+c-min(cs)) for r, c in cells}
        if any(p in used or has_neighbor(p, used, ignore=placed) for p in placed):
            cur_c += bw + 2; continue
        used |= placed
        col = color_rng.randint(2, 9)
        for r, c in placed: g[r][c] = col
        cur_c += bw + 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 14
    g = full_grid(h, w, 0)
    if name == "all_solid":
        # all objects solid → all recolored to 3 (hole count 0); rule outputs uniform color
        for (r, c) in _solid(2, 2): g[1 + r][1 + c] = 4
        for (r, c) in _solid(3, 3): g[1 + r][6 + c] = 6
        return g
    if name == "all_holed":
        # all objects have holes → all recolored to 4 (hole count 1); uniform color
        for (r, c) in _frame(3, 3): g[1 + r][1 + c] = 4
        for (r, c) in _frame(4, 4): g[1 + r][6 + c] = 6
        return g
    if name == "no_objects":
        # blank → no objects, rule has no effect
        return g
    return g
