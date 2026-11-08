"""Generator for arc_additional_puzzle_bank_volume19:H131.

Rule: open maze cells partition by distance to two seeds (red + green)
under wall-aware BFS, with ties marked separately.

Combinatorial axes (9): grid_h/w, palette_kind, anchor_row,
seed_distance, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: seeds_collide, no_walls, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d39f2d5ed593"
VERSION = "2.1.1"  # dup 28%: the 2 BFS-Voronoi markers (color 2/3) were at FIXED relative positions (same row, +-2 from center) so the partition barely varied. Now random distinct interior positions + 0-3 interior walls -> varied partitions.
TASK_ID = "d39f2d5ed593"
SUMMARY = (
    "0-bg grid (h~8-13, w~9-15) framed by a "
    "COLOR-5 (gray) OUTER WALL BORDER (entire "
    "row 0, row h-1, col 0, col w-1 painted 5). "
    "Inside: (a) ONE COLOR-2 (red) SEED at "
    "(r, mid-2); (b) ONE COLOR-3 (green) SEED "
    "at (r, mid+2) where r is a random "
    "interior row and mid = w // 2 (seeds "
    "separated by 4 cols). Otherwise the "
    "interior is empty. Rule: APPLY WALL-AWARE "
    "BFS from EACH SEED through bg cells "
    "(4-conn, walls 5 block). Compute distance "
    "to RED and distance to GREEN for every "
    "open cell. PARTITION cells: closer to "
    "RED → paint red color; closer to GREEN → "
    "green color; TIE → tie marker color. "
    "Seeds and walls stay. Net: maze interior "
    "gets partitioned by BFS distance to "
    "seeds, with ties marked separately."
)

INVARIANTS = [
    "background is 0",
    "border walls are 5",
    "there is one red seed and one green seed",
    "seed placement creates closer-to-red, closer-to-green, and tie cells",
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; color-5 border walls present; exactly one color-2 and one color-3 seed."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    has_wall = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_wall:
        errs.append("no color-5 wall cells found")
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            counts[v] = counts.get(v, 0) + 1
    if counts.get(2, 0) != 1:
        errs.append(f"expected exactly 1 color-2 (red) seed; found {counts.get(2,0)}")
    if counts.get(3, 0) != 1:
        errs.append(f"expected exactly 1 color-3 (green) seed; found {counts.get(3,0)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 9, 15)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5
        g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5
        g[h - 1][c] = 5
    # the 2 markers were at FIXED relative positions (same row, +-2 from centre) ->
    # the BFS Voronoi partition barely varied -> dup 28%. Place them at random
    # distinct interior cells (separated) + a few interior walls for partition variety.
    interior = [(rr, cc) for rr in range(1, h - 1) for cc in range(1, w - 1)]
    rng.shuffle(interior)
    a = interior[0]
    b = next((p for p in interior[1:]
              if abs(p[0] - a[0]) + abs(p[1] - a[1]) >= 3), interior[1])
    used = {a, b}
    g[a[0]][a[1]] = 2
    g[b[0]][b[1]] = 3
    n_walls = 0 if difficulty == "easy" else rng.randint(0, 3)
    placed = 0
    for p in interior:
        if placed >= n_walls:
            break
        if p in used:
            continue
        g[p[0]][p[1]] = 5
        used.add(p); placed += 1
    return g


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
