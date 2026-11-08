"""Generator for arc_puzzle_bank_ninth21:E60.

Rule: keep the unique-largest connected component, erase others.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest, single_component, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9784a00e013"
VERSION = "2.1.1"
TASK_ID = "b9784a00e013"
SUMMARY = (
    "0-bg grid (h ∈ 8-10, w ∈ 8-11) "
    "with: 4 NON-OVERLAPPING "
    "COMPONENTS each in a DISTINCT "
    "non-bg color drawn from {1..9}: "
    "(a) ONE LARGE 6-CELL component "
    "(L-pentomino: (0,0),(0,1),(0,2),"
    "(1,0),(1,1),(2,0)) at fixed "
    "position (1, 1) in colors[0]; "
    "(b) ONE 2-CELL pair at (0, w-3..w-2) "
    "in colors[1]; (c) ONE 3-CELL "
    "L-tromino at (h-2..h-1, 0..1) in "
    "colors[2]; (d) ONE 2-CELL "
    "vertical at (h-2..h-1, w-2) in "
    "colors[3]. The 6-cell component "
    "is STRICTLY LARGER than any "
    "other (unique-largest). Rule "
    "(KEEP THE UNIQUE LARGEST "
    "CONNECTED COMPONENT, ERASE ALL "
    "OTHERS): EXTRACT every "
    "4-connected non-bg component "
    "with cell count. FIND the "
    "component with MAXIMUM cell "
    "count (unique). PRODUCE a "
    "fresh same-size grid of 0s. "
    "PAINT only the largest "
    "component's cells in its "
    "original color. ALL OTHER "
    "components erased to bg. Net: "
    "noisy multi-component input "
    "becomes a clean single-"
    "component output."
)

INVARIANTS = [
    "background is 0",
    "there is one unique largest connected component",
    "all smaller components are separated by background",
    "the largest component is preserved and all others are erased",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_component", "no_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "4", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g: list[list[int]], top: int, left: int, shape: list[tuple[int, int]], color: int) -> None:
    for dr, dc in shape:
        g[top + dr][left + dc] = color


def _poly(rng, size):
    """Random connected polyomino of `size` cells (BFS grow), normalized."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size:
        if not frontier:
            frontier = list(cells)
        base = rng.choice(frontier)
        nbrs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        rng.shuffle(nbrs)
        grew = False
        for dr, dc in nbrs:
            cand = (base[0] + dr, base[1] + dc)
            if cand not in cells:
                cells.add(cand)
                frontier.append(cand)
                grew = True
                break
        if not grew:
            frontier.remove(base)
    minr = min(r for r, c in cells)
    minc = min(c for r, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each nonzero color forms exactly 1 same-color 4-connected region."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    from collections import defaultdict
    by_color = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].append((r, c))
    errs = []
    for col, cells in by_color.items():
        cell_set = set(cells)
        visited = set()
        stack = [cells[0]]
        visited.add(cells[0])
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in cell_set and nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
        if len(visited) != len(cells):
            errs.append(f"color {col} forms multiple disconnected regions")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_objs = ctx.draw_int("n_components", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_objs = ctx.draw_int("n_components", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_objs = ctx.draw_int("n_components", 2, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_objs)
        # distinct sizes so the largest is strictly unique
        sizes = rng.sample(list(range(3, 10)), n_objs)
        ok = True
        for size, color in zip(sizes, colors):
            cells = _poly(rng, size)
            if not _place(g, rng, cells, color, occupied):
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not realize largest-object layout")


def _place(g, rng, cells, color, occupied):
    h, w = len(g), len(g[0])
    sh = max(r for r, c in cells) + 1
    sw = max(c for r, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _ in range(80):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cellset = {(r0 + r, c0 + c) for r, c in cells}
        clash = any((cr + dr, cc + dc) in occupied
                    for (cr, cc) in cellset
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1))
        if clash:
            continue
        for (cr, cc) in cellset:
            g[cr][cc] = color
            occupied.add((cr, cc))
        return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two components share the same maximum size → "unique largest" invariant violated, ambiguous
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 6), (6, 7)]:
            g[r][c] = 6
        return g
    if name == "single_component":
        # only one component → trivially the largest, rule is identity
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3), (4, 3)]:
            g[r][c] = 5
        return g
    if name == "no_components":
        # empty grid → no largest, rule output is empty/all-zero
        return g
    return g
