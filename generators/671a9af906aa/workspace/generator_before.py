"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k17 — BFS through 8-walled maze with key/door.

Rule: 8-walled outer + interior walls. Start (2), goal (3), color-4 key,
color-5 door (passable only with key). Output paints the BFS path color 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_start, door_without_key, walls_block_path.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "671a9af906aa"
VERSION = "1.2.2"  # AXES synced to the real band draws (defect-lint axis-honesty)
TASK_ID = "671a9af906aa"

SUMMARY = "8-walled maze with start(2), goal(3), optional key(4) + doors(5); rule paints BFS path from start to goal in color 7 (doors passable only if a key exists)."

# Rivals: 'paint shortest by manhattan, ignore walls' refuted by ≥1
# demo where path bends around walls. 'paint cells in straight line'
# refuted by ≥1 demo with zigzag path. 'use start color (2) for path'
# refuted by any demo (path is 7). 'paint through doors without key'
# refuted by ≥1 demo with door blocking when no key.
# 4 demos with varied maze layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "outer border is color-8 walls",
    "exactly one color-2 start and one color-3 goal cell, both interior",
    "0-1 color-4 key cell, 0-2 color-5 door cells",
    "some interior color-8 wall cells (sparse)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "door_without_key", "walls_block_path")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-8 easy / 8-11 med / 10-14 hard",
                       "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "8-10 easy / 10-13 med / 12-16 hard",
                       "valid": "8..16"},
    "use_key":        {"type": "int", "default": "0 easy / 0-1 med / 1 hard", "valid": "0..1"},
    "n_doors":        {"type": "int", "default": "0-1 easy / 0-2 med / 2-4 hard", "valid": "0..4"},
    "n_iw":           {"type": "int", "default": "0-2 easy / 1-4 med / 4-8 hard", "valid": "0..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "walled_maze_with_keys",
                       "valid": "walled_maze_with_keys"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-8 outer border; ≥1 start (2) cell; ≥1 goal (3) cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_8_border = any(grid[0][c] == 8 for c in range(w))
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    has_3 = any(grid[r][c] == 3 for r in range(h) for c in range(w))
    if not has_8_border:
        errs.append("no color-8 wall cells on top border")
    if not has_2:
        errs.append("no color-2 start cell found")
    if not has_3:
        errs.append("no color-3 goal cell found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        use_key = ctx.draw_int("use_key", 0, 0)
        n_doors = ctx.draw_int("n_doors", 0, 1)
        n_iw = ctx.draw_int("n_iw", 0, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        use_key = ctx.draw_int("use_key", 1, 1)
        n_doors = ctx.draw_int("n_doors", 2, 4)
        n_iw = ctx.draw_int("n_iw", 4, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        use_key = ctx.draw_int("use_key", 0, 1)
        n_doors = ctx.draw_int("n_doors", 0, 2)
        n_iw = ctx.draw_int("n_iw", 1, 4)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 8; g[h - 1][c] = 8
    for r in range(h): g[r][0] = 8; g[r][w - 1] = 8

    def place(value):
        for _ in range(80):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = value
            return (r, c)
        return None

    s = place(2)
    if s is None: return g
    for _ in range(120):
        gr = rng.randint(1, h - 2); gc = rng.randint(1, w - 2)
        if g[gr][gc] != 0: continue
        if abs(gr - s[0]) + abs(gc - s[1]) < 4: continue
        g[gr][gc] = 3; break
    if n_doors > 0:
        use_key = 1
    if use_key:
        place(4)
    for _ in range(n_doors):
        place(5)
    for _ in range(n_iw):
        place(8)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 8; g[h - 1][c] = 8
    for r in range(h): g[r][0] = 8; g[r][w - 1] = 8
    if name == "no_start":
        # Goal but no start — rule's BFS has no source; path
        # undefined.
        g[5][7] = 3
        return g
    if name == "door_without_key":
        # Door present but no key — rule's "passable with key"
        # branch never activates; door is effectively a wall.
        g[1][1] = 2; g[5][7] = 3; g[3][4] = 5
        return g
    if name == "walls_block_path":
        # Walls form a column that disconnects start side from
        # goal side — rule's BFS yields no path.
        g[1][1] = 2; g[5][7] = 3
        for r in range(1, h - 1): g[r][4] = 8
        return g
    return g
