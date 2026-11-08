"""Generator for arc_additional_puzzle_bank_volume16:H107.

Rule: red and green maze markers create a symmetric equidistant cyan
line.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_seeds, single_seed, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1f7c2a19280"
# 2.2.0: on a 4-connected grid the BFS distance to a marker has fixed
# checkerboard parity, so an equidistant (dist_red==dist_green) cell can exist
# ONLY when the red and green markers share parity ((r+c)%2 equal). 2.1.0
# placed them at independent random cells -> ~half had OPPOSITE parity -> NO
# bisector cell -> the rule painted nothing -> identity (14/24 seeds). 2.2.0
# forces same-parity markers AND verifies (via BFS) that >=1 equidistant
# reachable cell exists, retrying otherwise, so the cyan bisector always fires.
VERSION = "2.2.0"
TASK_ID = "e1f7c2a19280"
SUMMARY = (
    "Maze grid (h×w, ~8-13 by ~9-15) with color-5 (gray) BORDER "
    "walls around the entire perimeter and 0 interior. EXACTLY "
    "ONE color-2 (red) marker and ONE color-3 (green) marker "
    "placed in the interior at distinct positions. Optionally, "
    "5-8 INTERIOR wall cells (color 5) scattered in the interior, "
    "creating asymmetric path obstacles (not blocking either "
    "marker from anything else). Rule: BFS from red and from "
    "green through 0-cells, avoiding 5-walls (4-conn). For each "
    "0-cell reachable from BOTH markers, if dist_red == dist_green, "
    "paint it color 8. Output: markers + walls preserved, plus "
    "a 'perpendicular bisector' of color 8 cells."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "color-5 border walls form a complete rectangular perimeter",
    "exactly one color-2 (red) marker, one color-3 (green) marker",
    "markers are interior cells (not on border), at distinct positions",
    "≥1 cell is equidistant from both markers (rule fires)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 9..15", "valid": "7..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
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
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 14, 20)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 10, 16)
    rng = ctx.draw_rng("placement")

    def _fresh():
        gg = full_grid(h, w, 0)
        for r in range(h):
            gg[r][0] = 5; gg[r][w - 1] = 5
        for c in range(w):
            gg[0][c] = 5; gg[h - 1][c] = 5
        return gg

    last = None
    for _attempt in range(40):
        g = _fresh()
        # red on the left half, green on the right half, SAME checkerboard
        # parity so equidistant cells are possible.
        r_red = rng.randint(1, h - 2)
        c_red = rng.randint(1, w // 2 - 1)
        par = (r_red + c_red) % 2
        c_green = rng.randint(w // 2 + 1, w - 2)
        # choose green row matching parity with c_green
        green_rows = [r for r in range(1, h - 1) if (r + c_green) % 2 == par]
        r_green = rng.choice(green_rows)
        g[r_red][c_red] = 2
        g[r_green][c_green] = 3
        # Sprinkle interior walls (scaled to grid), avoiding the markers
        n_walls = rng.randint(5, max(9, (h * w) // 12))
        placed = 0
        for _ in range(60):
            if placed >= n_walls:
                break
            wr = rng.randint(1, h - 2)
            wc = rng.randint(1, w - 2)
            if g[wr][wc] == 0:
                g[wr][wc] = 5
                placed += 1
        last = g
        if _bisector_cells(g):
            return g
    return last


def _bfs_dist(grid, sr, sc):
    """4-connected BFS distances over 0-cells, starting from marker (sr,sc)."""
    from collections import deque
    h = len(grid); w = len(grid[0])
    dist = {}
    dq = deque()
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0:
            dist[(nr, nc)] = 1
            dq.append((nr, nc))
    while dq:
        r, c = dq.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                dq.append((nr, nc))
    return dist


def _bisector_cells(grid):
    """0-cells equidistant from the red(2) and green(3) markers."""
    red = green = None
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 2:
                red = (r, c)
            elif v == 3:
                green = (r, c)
    if red is None or green is None:
        return []
    dr = _bfs_dist(grid, *red)
    dg = _bfs_dist(grid, *green)
    return [cell for cell in dr if cell in dg and dr[cell] == dg[cell]]


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly one red + one green marker, and >=1 equidistant cell so the
    cyan bisector is actually painted (non-identity)."""
    nred = sum(row.count(2) for row in grid)
    ngreen = sum(row.count(3) for row in grid)
    if nred != 1 or ngreen != 1:
        return [f"expected 1 red + 1 green marker, got {nred}/{ngreen}"]
    if not _bisector_cells(grid):
        return ["no equidistant cell -> rule paints nothing (identity demo)"]
    return []


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 11, 0)
    if name == "no_seeds":
        for r in range(10):
            g[r][0] = 5; g[r][10] = 5
        for c in range(11):
            g[0][c] = 5; g[9][c] = 5
        return g
    if name == "single_seed":
        for r in range(10):
            g[r][0] = 5; g[r][10] = 5
        for c in range(11):
            g[0][c] = 5; g[9][c] = 5
        g[5][5] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(11):
                g[r][c] = 5
        return g
    return g
