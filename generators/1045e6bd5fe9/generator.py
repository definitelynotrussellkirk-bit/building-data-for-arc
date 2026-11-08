"""Generator for ecdecbb3.

Rule: each red center projects to nearest full 8 walls, adding legs
and 3x3 wall nodes.

Combinatorial axes (8): grid_h/w, orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_centers.
Degenerates: no_walls, no_centers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1045e6bd5fe9"
VERSION = "2.1.1"  # +self_check
TASK_ID = "1045e6bd5fe9"
SUMMARY = (
    "0-bg grid (h, w~10-13) with: "
    "(a) TWO FULL COLOR-8 (cyan) "
    "WALLS — either horizontal "
    "(rows 1 and h-2 entirely "
    "color 8) or vertical (cols "
    "1 and w-2 entirely color "
    "8); (b) 1-2 COLOR-2 (red) "
    "CENTER cells between the "
    "walls (≥3 cells from each "
    "wall). Rule (PROJECT RED "
    "CENTERS TO WALLS WITH LEGS "
    "+ 3×3 NODES): for EACH "
    "COLOR-2 CENTER, PROJECT "
    "perpendicular to the walls "
    "(if walls horizontal, "
    "project vertically; if "
    "vertical, project "
    "horizontally). DRAW LEGS "
    "of color 2 from the center "
    "to the nearest walls, AND "
    "stamp a 3×3 COLOR-8 "
    "(cyan) NODE at the wall "
    "intersection points. Net: "
    "red centers project to "
    "walls, leaving legs + "
    "wall-side nodes."
)

INVARIANTS = [
    "the scene has full horizontal or full vertical color-8 walls",
    "one or more color-2 cells sit between those walls",
    "each color-2 projects perpendicular to the wall family",
    "centers sit clear of walls so projections have room",
]

ORIENTATIONS = ("horizontal_walls", "vertical_walls")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_walls", "no_centers", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_centers":      {"type": "int", "default": "2", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11)
        n_centers = ctx.draw_int("n_centers", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16); w = ctx.draw_int("grid_w", 14, 16)
        n_centers = ctx.draw_int("n_centers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
        n_centers = ctx.draw_int("n_centers", 2, 3)
    g = full_grid(h, w, 0)

    if orientation == "horizontal_walls":
        # 2..3 full-width walls at distinct rows (>=4 apart so centers fit).
        wall_rows = _pick_walls(rng, h, n_max=3)
        for wr in wall_rows:
            for c in range(w):
                g[wr][c] = 8
        for _ in range(n_centers):
            for _t in range(40):
                wr = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                if g[wr][c] == 0 and any(abs(wr - x) >= 3 for x in wall_rows) \
                        and all(abs(wr - x) != 0 for x in wall_rows):
                    g[wr][c] = 2
                    break
    else:
        wall_cols = _pick_walls(rng, w, n_max=3)
        for wc in wall_cols:
            for r in range(h):
                g[r][wc] = 8
        for _ in range(n_centers):
            for _t in range(40):
                r = rng.randint(0, h - 1)
                wc = rng.randint(0, w - 1)
                if g[r][wc] == 0 and any(abs(wc - x) >= 3 for x in wall_cols) \
                        and all(abs(wc - x) != 0 for x in wall_cols):
                    g[r][wc] = 2
                    break
    return g


def _pick_walls(rng, n, n_max=3):
    """Pick 2..n_max wall lines in [1, n-2], pairwise >=4 apart."""
    n_walls = rng.randint(2, n_max)
    walls = []
    for _ in range(80):
        cand = rng.randint(1, n - 2)
        if all(abs(cand - x) >= 4 for x in walls):
            walls.append(cand)
            if len(walls) >= n_walls:
                break
    if len(walls) < 2:
        walls = [1, n - 2]
    return sorted(walls)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Color-8 full-span wall(s) AND color-2 center cell(s) both present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    # Full-span row or column of 8s (the walls)
    has_wall = (any(all(grid[r][c] == 8 for c in range(w)) for r in range(h)) or
                any(all(grid[r][c] == 8 for r in range(h)) for c in range(w)))
    if not has_wall:
        errors.append("no full-span color-8 wall row or column found")
    has_center = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_center:
        errors.append("no color-2 center cell found")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_walls":
        g[5][5] = 2
        return g
    if name == "no_centers":
        for c in range(11):
            g[1][c] = 8
            g[9][c] = 8
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 8
        return g
    return g
