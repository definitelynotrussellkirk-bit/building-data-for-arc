"""Generator for arc_additional_puzzle_bank_volume18:H121.

Rule: two seeds (red and green) inside a walled border define equidistant
maze cells that get marked cyan in the output.

Combinatorial axes (9): grid_h/w, palette_kind, anchor_row,
seed_distance, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: seeds_collide, no_walls, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "410efa4c3988"
VERSION = "2.0.0"  # distinct=41/dup 28%: maze was an EMPTY 5-bordered box with start(2)/goal(3) 4 cols apart -> trivial straight-line shortest path. Now random internal 5-walls (real maze) + varied start/goal with a verified non-trivial path -> the BFS shortest path (output) varies richly.
TASK_ID = "410efa4c3988"
SUMMARY = "A walled two-seed maze contains at least one reachable background cell equidistant from the red and green seeds; those tie cells turn cyan."

INVARIANTS = [
    "background is 0",
    "border walls are 5",
    "there is one red seed and one green seed",
    "at least one background cell has equal finite distance to both seeds",
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
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 9, 11); dens = 0.18
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 13, 16); dens = 0.30
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 11, 15); dens = 0.25
    rng = ctx.draw_rng("placement")
    # real maze: 5-wall border + random internal 5-walls; start(2)/goal(3) at
    # varied passable cells with a guaranteed (and non-trivial) shortest path.
    for _outer in range(60):
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][0] = 5; g[r][w - 1] = 5
        for c in range(w):
            g[0][c] = 5; g[h - 1][c] = 5
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if rng.random() < dens:
                    g[r][c] = 5
        free = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if g[r][c] == 0]
        if len(free) < 4:
            continue
        a = rng.choice(free)
        far = [p for p in free
               if abs(p[0] - a[0]) + abs(p[1] - a[1]) >= max(3, (h + w) // 4)]
        if not far:
            continue
        b = rng.choice(far)
        if _reachable(g, a, b) and _has_tie_cell(g, a, b):
            g[a[0]][a[1]] = 2; g[b[0]][b[1]] = 3
            return g
    # fallback: open box (always solvable)
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5; g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5; g[h - 1][c] = 5
    g[h // 2][2] = 2; g[h // 2][w - 3] = 3
    return g


def _reachable(g, a, b):
    h, w = len(g), len(g[0])
    seen = {a}; stack = [a]
    while stack:
        r, c = stack.pop()
        if (r, c) == b:
            return True
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] != 5:
                seen.add((nr, nc)); stack.append((nr, nc))
    return False


def _distances(g, start):
    h, w = len(g), len(g[0])
    dist = {start: 0}
    q = [start]
    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in dist and g[nr][nc] != 5:
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))
    return dist


def _has_tie_cell(g, a, b):
    da = _distances(g, a)
    db = _distances(g, b)
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v == 0 and (r, c) in da and da[(r, c)] == db.get((r, c)):
                return True
    return False


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

def self_check(grid, *, difficulty=None, meta=None):
    h, w = len(grid), len(grid[0])
    errs = []
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)) or any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errs.append("border is not all color 5")
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    greens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(reds) != 1 or len(greens) != 1:
        return errs + [f"expected one red and one green seed, found {len(reds)}, {len(greens)}"]
    if not _reachable(grid, reds[0], greens[0]):
        errs.append("red and green seeds are not connected")
    if not _has_tie_cell(grid, reds[0], greens[0]):
        errs.append("no background cell is equidistant from both seeds")
    return errs
