"""Generator for arc_additional_puzzle_bank_volume13:E89.

Rule: crop the smallest nonzero component to its bounding box.

Combinatorial axes (8): grid_h/w, palette_kind, num_objects, smallest_size,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: tied_smallest, only_one_component, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "61bc036fdab8"
VERSION = "2.0.1"
TASK_ID = "61bc036fdab8"
SUMMARY = "The smallest nonzero component is cropped to its bounding box."

INVARIANTS = [
    "background is 0",
    "one nonzero component is uniquely smallest",
    "larger components are separated from the target",
    "the target may include internal background inside its bounding box",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("tied_smallest", "only_one_component", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_objects":    {"type": "int", "default": "3", "valid": "3"},
    "smallest_size":  {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, size):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= size:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for r, c in cells]


def _free(g, cells, top, left):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        r, c = top + dr, left + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    ph = max(r for r, _ in cells) + 1; pw = max(c for _, c in cells) + 1
    for _ in range(80):
        top = rng.randint(0, h - ph); left = rng.randint(0, w - pw)
        if _free(g, cells, top, left):
            for dr, dc in cells:
                g[top + dr][left + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 8, 10); n_big = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 19); w = ctx.draw_int("grid_w", 13, 19); n_big = ctx.draw_int("n_big", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 14); w = ctx.draw_int("grid_w", 9, 14); n_big = ctx.draw_int("n_big", 2, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # the UNIQUELY-smallest component: a random small polyomino (varied shape,
    # incl. internal bg in its bbox, and varied colour) -> the cropped output
    small_size = rng.randint(2, 4)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_big + 1)
    _place(g, rng, _rand_poly(rng, small_size), colors[0])
    # larger decoy components, each STRICTLY bigger than the smallest
    for i in range(n_big):
        _place(g, rng, _rand_poly(rng, rng.randint(small_size + 1, small_size + 6)),
               colors[i + 1])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 components present; uniquely-smallest exists."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    visited = [[False] * w for _ in range(h)]
    sizes = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 and not visited[sr][sc]:
                q = [(sr, sc)]
                visited[sr][sc] = True
                sz = 0
                while q:
                    r, c = q.pop()
                    sz += 1
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                sizes.append(sz)
    if len(sizes) < 2:
        errors.append(f"need >=2 components (smallest + decoy), found {len(sizes)}")
        return errors
    min_sz = min(sizes)
    n_min = sizes.count(min_sz)
    if n_min != 1:
        errors.append(f"smallest component size {min_sz} is NOT unique ({n_min} components share it)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        g[2][2] = 6; g[2][3] = 6
        g[5][6] = 5; g[5][7] = 5
        draw_rect(g, h - 3, 0, 3, 3, 7)
        return g
    if name == "only_one_component":
        g[3][3] = 6; g[3][4] = 6; g[4][3] = 6
        return g
    if name == "all_same_size":
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4
        g[1][6] = 6; g[1][7] = 6; g[2][6] = 6
        g[7][1] = 7; g[7][2] = 7; g[8][1] = 7
        return g
    return g
