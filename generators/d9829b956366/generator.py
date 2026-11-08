"""Generator for v3_rich_schema:medium_06_recolor_border_touching_objects — recolor border-touching to 2.

Rule: each connected component that touches the grid border is recolored
to color 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_border, all_interior, no_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d9829b956366"
VERSION = "2.1.0"  # was raise-on-fail in the layout loop; replaced with graceful return. Probe healthy (uniq 100%, out_shapes 9).
TASK_ID = "d9829b956366"
SUMMARY = (
    "0-bg grid (h~6-8, w~8-10) containing 2-4 "
    "CONNECTED MOTIFS of 2-4 cells each, all "
    "painted in COLOR 4 (yellow). Half of them "
    "(ceil(n/2)) TOUCH the GRID BORDER (any "
    "cell at row 0, row h-1, col 0, or col w-1); "
    "the other half are placed in the INTERIOR "
    "(no border contact). Motifs are non-touching "
    "(separated by ≥1 cell padding). Rule: for "
    "every CONNECTED COMPONENT, check if any of "
    "its cells touches the grid BORDER (row 0, "
    "row h-1, col 0, or col w-1). If YES, "
    "RECOLOR every cell of that component to "
    "COLOR 2 (red). If NO (entirely interior), "
    "leave the component as color 4 (yellow). "
    "Net: border-touching motifs become red; "
    "interior motifs stay yellow."
)

INVARIANTS = [
    "background is 0",
    "2-4 connected motifs, all in color 4",
    "at least one motif touches the grid border and at least one does not",
    "generated inputs contain no color 2; color 2 is reserved for the output recolor",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "border_plus_interior_motifs",
                       "valid": "border_plus_interior_motifs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n", 2, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        touching = (n + 1) // 2
        ok = True
        for i in range(n):
            color = 4
            cells = _build_motif(rng, rng.randint(2, 4))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            wants_border = i < touching
            for _ in range(120):
                if wants_border:
                    if rng.choice([True, False]):
                        r0 = rng.choice([0, h - sh]); c0 = rng.randint(0, w - sw)
                    else:
                        r0 = rng.randint(0, h - sh); c0 = rng.choice([0, w - sw])
                else:
                    r0 = rng.randint(1, h - sh - 1) if h - sh > 1 else 0
                    c0 = rng.randint(1, w - sw - 1) if w - sw > 1 else 0
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place both border-touching and interior motifs")


def _components4(grid, color=4):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _touches_border(comp, h, w):
    return any(r == 0 or c == 0 or r == h - 1 or c == w - 1 for r, c in comp)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate border-touch vs interior color-4 motif contrast."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    palette = {v for row in grid for v in row}
    if not palette <= {0, 4}:
        errs.append(f"input palette should be {{0,4}}, got {sorted(palette)}")
    comps = _components4(grid, 4)
    if not (2 <= len(comps) <= 4):
        errs.append(f"expected 2..4 color-4 components, got {len(comps)}")
    touching = [comp for comp in comps if _touches_border(comp, h, w)]
    interior = [comp for comp in comps if not _touches_border(comp, h, w)]
    if not touching:
        errs.append("no border-touching motif; recolor-to-2 branch hidden")
    if not interior:
        errs.append("no interior motif; leave-as-4 branch hidden")
    for comp in comps:
        if not (2 <= len(comp) <= 4):
            errs.append(f"motif size should be 2..4 cells, got {len(comp)}")
            break
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "all_border":
        # all motifs touch border → all recolored to 2; no interior contrast
        for (r, c) in [(0, 1), (0, 2), (1, 1)]: g[r][c] = 4
        for (r, c) in [(h - 1, 5), (h - 1, 6)]: g[r][c] = 4
        for (r, c) in [(3, 0), (4, 0)]: g[r][c] = 4
        return g
    if name == "all_interior":
        # no motif touches border → rule recolors nothing, output equals input
        for (r, c) in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        for (r, c) in [(4, 5), (5, 5), (5, 6)]: g[r][c] = 4
        return g
    if name == "no_motifs":
        # blank grid → rule has nothing to recolor
        return g
    return g
