"""Generator for arc_puzzle_bank_21_set4_d:medium_d03 — border-touch recolor.

Rule (canonical): find every non-background 4-connected object. Objects that
TOUCH the outer border are recolored to 2; objects strictly inside the grid are
recolored to 8. Shape and position are preserved.

The old generator text described a stale "vertical gallery pack" task, and its
random placement often produced all-interior or all-border examples. Those are
valid inputs but poor teaching rows because one of the two recolor branches never
fires. This version deliberately includes both branch types in every default
sample.

Combinatorial axes: grid_h, grid_w, n_components, n_touching_border,
palette_kind, component_size, position_bias, texture.
Degenerates: identical_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e8324f40386"
VERSION = "2.1.0"  # branch coverage: force at least one border-touching and one interior component; fix stale docs.
TASK_ID = "6e8324f40386"
SUMMARY = (
    "0-bg grid with 3-4 small, isolated, monochrome connected components in "
    "distinct nonzero colors. At least one component touches the outer border "
    "and at least one component is strictly interior. Rule: recolor every "
    "border-touching component to 2 and every interior component to 8, preserving "
    "their shapes and positions."
)

INVARIANTS = [
    "background is 0",
    "3-4 isolated connected components in distinct non-zero colors",
    "at least one component touches the grid border (becomes 2)",
    "at least one component is strictly interior (becomes 8)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "n_touching_border": {"type": "int", "default": "rng 1..n-1", "valid": "1..n-1"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "border_and_interior",
                       "valid": "border_and_interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    # normalize so the bbox top-left is (0,0)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            q = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def _touches_border(cells, h, w):
    return any(r == 0 or c == 0 or r == h - 1 or c == w - 1 for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the two visible recolor branches: border->2 and interior->8."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    comps = _components(grid)
    if not (3 <= len(comps) <= 4):
        errs.append(f"expected 3-4 nonzero components, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        errs.append("components should have distinct colors before recoloring")
    touching = sum(1 for _, cells in comps if _touches_border(cells, h, w))
    interior = len(comps) - touching
    if touching < 1:
        errs.append("expected at least one border-touching component for the color-2 branch")
    if interior < 1:
        errs.append("expected at least one interior component for the color-8 branch")
    return errs


def _place_component(g, cells, color, rng, *, mode):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1

    def candidate():
        if mode == "border":
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                return 0, rng.randint(0, w - sw)
            if side == "bottom":
                return h - sh, rng.randint(0, w - sw)
            if side == "left":
                return rng.randint(0, h - sh), 0
            return rng.randint(0, h - sh), w - sw
        if mode == "interior":
            if h - sh <= 2 or w - sw <= 2:
                return None
            return rng.randint(1, h - sh - 1), rng.randint(1, w - sw - 1)
        return rng.randint(0, h - sh), rng.randint(0, w - sw)

    for _ in range(160):
        pos = candidate()
        if pos is None:
            return False
        r0, c0 = pos
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r][c0 + c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for _outer in range(80):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        n_touch = rng.randint(1, n - 1)
        modes = ["border"] * n_touch + ["interior"] * (n - n_touch)
        rng.shuffle(modes)
        ok = True
        for color, mode in zip(colors, modes):
            cells = _build_motif(rng, rng.randint(3, 5))
            if not _place_component(g, cells, color, rng, mode=mode):
                ok = False
                break
        if ok and not self_check(g):
            return g
    raise ValueError("could not realize a mixed border/interior component layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "identical_motifs":
        # All motifs are the same shape; weak structural contrast, retained only as an opt-in negative texture.
        for (r, c) in [(0, 1), (0, 2), (1, 1)]:
            g[r][c] = 4
        for (r, c) in [(1, 7), (1, 8), (2, 7)]:
            g[r][c] = 6
        for (r, c) in [(6, 3), (6, 4), (7, 3)]:
            g[r][c] = 8
        return g
    if name == "single_motif":
        # only one motif -> only one branch can fire
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5), (5, 5)]:
            g[r][c] = 4
        return g
    if name == "all_same_color":
        # multiple components share one color; legal but poor color-disambiguation pedagogy
        for (r, c) in [(0, 1), (0, 2), (1, 1)]:
            g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]:
            g[r][c] = 4
        for (r, c) in [(8, 8), (8, 9), (9, 8)]:
            g[r][c] = 4
        return g
    return g
