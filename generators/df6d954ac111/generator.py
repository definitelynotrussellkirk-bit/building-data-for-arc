"""Generator for arc_puzzle_bank_eighteenth21:E122.

Rule: keep only the unique largest 4-connected nonzero object.

Combinatorial axes (8): grid_h, grid_w, palette_kind, small_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest, single_object, only_distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df6d954ac111"
VERSION = "1.1.0"
TASK_ID = "df6d954ac111"
SUMMARY = "Keep only the unique largest 4-connected nonzero object."

INVARIANTS = [
    "background is 0",
    "objects are 4-connected monochrome components",
    "one object is uniquely largest",
    "all smaller objects are erased",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_object", "only_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "small_objects":  {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "scattered_with_one_large",
                       "valid": "scattered_with_one_large"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_LARGE = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
_SMALL = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0)],
]


def _free(g, cells, top, left):
    h, w = len(g), len(g[0])
    coords = [(top + r, left + c) for r, c in cells]
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in coords):
        return False
    for r, c in coords:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def _paint(g, cells, top, left, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        small = ctx.draw_int("small_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        small = ctx.draw_int("small_objects", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        small = ctx.draw_int("small_objects", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    _paint(g, _LARGE, rng.randint(0, h - 3), rng.randint(0, w - 3), rng.choice([2, 3, 4, 5, 6, 7, 8, 9]))
    placed = 0
    for _ in range(180):
        if placed >= small:
            break
        shape = rng.choice(_SMALL)
        top = rng.randint(0, h - 2)
        left = rng.randint(0, w - 2)
        if _free(g, shape, top, left):
            _paint(g, shape, top, left, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]))
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two objects share the maximum size → "uniquely largest" predicate fails, ambiguous
        _paint(g, _LARGE, 0, 0, 4)
        _paint(g, _LARGE, 4, 4, 6)  # same shape, same size
        return g
    if name == "single_object":
        # only one object → trivially largest, no comparison
        _paint(g, _LARGE, 2, 2, 4)
        return g
    if name == "only_distractors":
        # no large object, only small distractors → "largest" is among the distractors;
        # output keeps just one tiny piece (rule still fires but signal is weak)
        _paint(g, [(0, 0), (0, 1)], 1, 1, 4)
        _paint(g, [(0, 0)], 4, 4, 6)
        _paint(g, [(0, 0), (1, 0)], 5, 7, 3)
        return g
    return g



def _components_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    comps = _components_for_self_check(grid) if grid and grid[0] else []
    if len(comps) < 2:
        return ["expected one largest object plus at least one distractor"]
    sizes = sorted((len(c) for c in comps), reverse=True)
    if sizes[0] <= sizes[1]:
        return [f"largest object is not unique: sizes={sizes}"]
    if sizes[0] < 5:
        return [f"largest object too small to teach selection: sizes={sizes}"]
    return []
