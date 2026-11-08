"""Generator for arc_additional_puzzle_bank_volume23:E159.

Rule: the smallest nonzero object is cropped to its bounding box.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "58236722e146"
VERSION = "3.1.0"  # fail closed instead of silently under-placing components  # FIX: FIXED colour-2 L-shape always the smallest -> crop output always the same (distinct=1). Now the smallest object is a VARIED random polyomino (size 2-4, varied form+colour) + 2 strictly-larger objects -> the cropped output varies. (Sibling of 20fa0e6e2e3b.)
TASK_ID = "58236722e146"
SUMMARY = (
    "0-bg grid (h, w~8-13) with EXACTLY 3 separated components: the "
    "SMALLEST is a VARIED random polyomino (2-4 cells, varied form and "
    "colour) and two strictly-larger random objects ensure it is "
    "uniquely smallest. Rule: find the smallest connected component by "
    "cell count, crop it to its bbox, output that crop (colour "
    "preserved). Varied smallest shapes+colours -> varied cropped output."
)

INVARIANTS = [
    "background is 0",
    "there are multiple nonzero components",
    "one component is uniquely smallest by size",
    "components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "equal_sizes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "true", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_components|equal_sizes|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def _poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, color, rng, occ):
    h, w = len(g), len(g[0])
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if bh > h or bw > w:
        return False
    for _ in range(150):
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        ac = [(r0 + r, c0 + c) for r, c in cells]
        if any((r + dr, c + dc) in occ
               for r, c in ac for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in ac:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13); w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("placement")

    ssize = rng.randint(2, 4)
    for _layout_try in range(120):
        small = _poly(rng, ssize)
        big1 = _poly(rng, ssize + rng.randint(2, 3))
        big2 = _poly(rng, ssize + rng.randint(4, 5))
        cs, c1, c2 = rng.sample(_NONBG, 3)
        g = full_grid(h, w, 0)
        occ = set()
        if (_place(g, small, cs, rng, occ)
                and _place(g, big1, c1, rng, occ)
                and _place(g, big2, c2, rng, occ)):
            return g
    raise ValueError("could not realize three separated components")


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "equal_sizes":
        draw_rect(g, 0, 0, 2, 2, 7)
        draw_rect(g, 7, 7, 2, 2, 8)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 3
        return g
    return g

def _components_same_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and grid[nx][ny] == v:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append((v, cells))
    return comps


def self_check(grid, *, seed=None, sample_index=None, difficulty=None, **kwargs):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular and nonempty"]
    comps = _components_same_color(grid)
    if len(comps) != 3:
        errs.append(f"expected exactly three separated components, got {len(comps)}")
        return errs
    sizes = sorted(len(cells) for _, cells in comps)
    if not (sizes[0] < sizes[1] and sizes[0] < sizes[2]):
        errs.append(f"expected one strictly smaller component, got sizes {sizes}")
    if len({color for color, _ in comps}) != 3:
        errs.append("the three components should have distinct colors")
    return errs
