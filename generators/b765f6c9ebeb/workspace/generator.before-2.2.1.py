"""Generator for arc_puzzle_bank_nineteenth21:E130.

Rule: erase isolated single-cell components; keep multi-cell components.

Combinatorial axes (8): grid_h, grid_w, palette_kind, singletons, objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_singletons, no_objects, all_singletons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b765f6c9ebeb"
# 2.1.0: multi-cell objects can also be random polyominoes (2-5 cells), not just
# the 4 fixed templates -> richer surviving shapes (rule only needs size>1)
VERSION = "2.2.1"
TASK_ID = "b765f6c9ebeb"

SUMMARY = (
    "0-bg grid (h×w, ~6-9 by ~7-10) with a MIX of: (a) 2-3 multi-"
    "cell connected components (2-4 cells each, shapes like "
    "domino, L, square) in various non-zero colors; (b) 2-4 "
    "isolated SINGLETON cells (single 1-cell components). All "
    "components placed with cardinal separation (4-conn isolated; diagonal proximity is allowed). "
    "Rule: detect all connected components. Keep components "
    "with size > 1, preserving original color. Erase components "
    "with size == 1 (singletons → 0). Output preserves grid "
    "dimensions; multi-cell components survive."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 multi-cell components (each ≥2 cells)",
    "2-4 isolated singleton cells (each 1 cell)",
    "all components 4-conn isolated from each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_singletons", "no_objects", "all_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "singletons":     {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "objects":        {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "mixed_singletons_and_objects",
                       "valid": "mixed_singletons_and_objects"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_singletons|no_objects|all_singletons'},
}


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Require both erased singletons and surviving multi-cell components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            for dr, dc in ((0, 1), (1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, v):
                    errs.append(f"4-adjacent cells ({r},{c})={v} and ({nr},{nc})={grid[nr][nc]} differ")
    comps = _nonzero_components(grid)
    singles = [comp for comp in comps if len(comp) == 1]
    multis = [comp for comp in comps if len(comp) > 1]
    if not singles:
        errs.append("no singleton component present; erase rule would be identity")
    if not multis:
        errs.append("no multi-cell component present; keep branch not demonstrated")
    min_singletons = 3 if difficulty == "hard" else 2
    if len(singles) < min_singletons:
        errs.append(f"expected at least {min_singletons} singleton components, got {len(singles)}")
    if len(multis) < 2:
        errs.append(f"expected at least 2 multi-cell components, got {len(multis)}")
    return errs


_OBJECT_SHAPES = [
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _cells(top: int, left: int, shape: list[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _poly(rng, n):
    """Random connected polyomino of n cells normalized to origin."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < n and frontier:
        r, c = rng.choice(frontier)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nb = (r + dr, c + dc)
        if nb not in cells:
            cells.add(nb); frontier.append(nb)
    r0 = min(p[0] for p in cells); c0 = min(p[1] for p in cells)
    return [(r - r0, c - c0) for (r, c) in cells]


def _guard(cells: set[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    """Cells plus cardinal neighbors: enough to keep 4-connected objects distinct.

    The old 8-neighbor halo over-constrained tight 6x7/7x8 boards and could
    fail to place any singleton erasure. Diagonal proximity is safe for the
    canonical `objects` primitive, which is 4-connected/color-keyed.
    """
    out = set(cells)
    for r, c in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out.add((rr, cc))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        singleton_target = ctx.draw_int("singletons", 2, 2)
        object_target = ctx.draw_int("objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        singleton_target = ctx.draw_int("singletons", 3, 4)
        object_target = ctx.draw_int("objects", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        singleton_target = ctx.draw_int("singletons", 2, 4)
        object_target = ctx.draw_int("objects", 2, 3)
    rng = ctx.draw_rng("layout")
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    for _outer in range(60):
        g = full_grid(h, w, 0)
        reserved: set[tuple[int, int]] = set()

        objects_placed = 0
        for _ in range(300):
            if objects_placed >= object_target:
                break
            # mix fixed templates with random polyominoes (both size>1)
            if rng.random() < 0.5:
                shape = rng.choice(_OBJECT_SHAPES)
            else:
                shape = _poly(rng, rng.randint(2, 5))
            sh = max(r for r, _ in shape); sw = max(c for _, c in shape)
            if sh >= h or sw >= w:
                continue
            top = rng.randint(0, h - 1 - sh)
            left = rng.randint(0, w - 1 - sw)
            cells = _cells(top, left, shape)
            guard = _guard(cells, h, w)
            if guard & reserved:
                continue
            color = rng.choice(colors)
            for r, c in cells:
                g[r][c] = color
            reserved.update(guard)
            objects_placed += 1

        singletons_placed = 0
        for _ in range(400):
            if singletons_placed >= singleton_target:
                break
            r = rng.randrange(h)
            c = rng.randrange(w)
            cells = {(r, c)}
            guard = _guard(cells, h, w)
            if guard & reserved:
                continue
            g[r][c] = rng.choice(colors)
            reserved.update(guard)
            singletons_placed += 1
        if objects_placed >= object_target and singletons_placed >= singleton_target:
            return g
    raise ValueError("could not place both multi-cell objects and singleton erasures")


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_singletons":
        # only multi-cell objects → rule fires zero times, output identical
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6)]: g[r][c] = 6
        return g
    if name == "no_objects":
        # only singletons → all erased, output blank
        g[1][2] = 4; g[3][5] = 6; g[5][7] = 3; g[6][1] = 8
        return g
    if name == "all_singletons":
        # every cell is its own component → every cell erased, output blank
        g[1][2] = 4; g[3][5] = 6; g[5][7] = 3; g[6][1] = 8; g[2][6] = 7
        return g
    return g
