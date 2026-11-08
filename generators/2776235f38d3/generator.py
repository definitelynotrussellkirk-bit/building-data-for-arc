"""Generator for arc_additional_puzzle_bank_volume11:M76.

Rule: normalize the color-1 shape and the color-2 shape each to their own
bbox, take the XOR (symmetric difference) of the two cell sets, and
output it bbox-cropped, painted color 8.

Combinatorial axes: grid size, the two shapes (which set the XOR output),
their positions, and a color-7 noise cell.
Degenerates: no_shapes, identical_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "2776235f38d3"
VERSION = "3.0.2"
TASK_ID = "2776235f38d3"
SUMMARY = (
    "0-bg grid (size varies). ONE color-1 (blue) SHAPE and ONE color-2 "
    "(red) SHAPE (random polyominoes whose normalized forms differ), "
    "placed apart, plus a color-7 (orange) NOISE cell the rule ignores. "
    "Rule: normalize each shape to its own bbox top-left, take the XOR "
    "(symmetric difference) of the two cell sets, and output it "
    "bbox-cropped with the XOR cells painted COLOR 8 (cyan). The grid "
    "size, the two shapes (which set the XOR output), their positions "
    "and the noise cell all vary freely, so the output varies too (was "
    "2 fixed shapes + grid padding)."
)

INVARIANTS = [
    "exactly one color-1 blob and one color-2 blob",
    "their normalized cell sets differ (so the XOR is non-empty)",
    "a color-7 noise cell is ignored by the rule",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "identical_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_shapes|identical_shapes|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one connected color-1 shape, one connected color-2 shape, a
    non-empty normalized XOR, and exactly one ignored color-7 noise cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    comps_by_color = {1: [], 2: []}
    for color in (1, 2):
        cells_all = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
        seen = set()
        for cell in list(cells_all):
            if cell in seen:
                continue
            stack = [cell]; seen.add(cell); comp = []
            while stack:
                r, c = stack.pop(); comp.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (nr, nc) in cells_all and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps_by_color[color].append(comp)
    if len(comps_by_color[1]) != 1:
        errs.append(f"expected one color-1 component, found {len(comps_by_color[1])}")
    if len(comps_by_color[2]) != 1:
        errs.append(f"expected one color-2 component, found {len(comps_by_color[2])}")
    if len(comps_by_color[1]) == 1 and len(comps_by_color[2]) == 1:
        if _norm(comps_by_color[1][0]) == _norm(comps_by_color[2][0]):
            errs.append("normalized color-1 and color-2 shapes are identical; XOR output empty")
    n_noise = sum(1 for row in grid for v in row if v == 7)
    if n_noise != 1:
        errs.append(f"expected exactly one color-7 ignored noise cell, found {n_noise}")
    return errs


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _random_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        mr = max(r for r, c in n); mc = max(c for r, c in n)
        if mr < maxd and mc < maxd:
            return [(r, c) for r, c in n]
    return [(0, 0), (1, 0), (1, 1)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr = (8, 10), (10, 12), (3, 4)
    elif difficulty == "hard":
        hr, wr, szr = (11, 16), (12, 16), (4, 6)
    else:
        hr, wr, szr = (9, 12), (11, 14), (3, 5)

    for _attempt in range(40):
        s1 = _random_poly(rng, rng.randint(*szr), 4)
        s2 = _random_poly(rng, rng.randint(*szr), 4)
        if _norm(s1) == _norm(s2):                 # XOR must be non-empty
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = color; occ[top + r][left + c] = True
                    return True
            return False

        if not (_place(s1, 1) and _place(s2, 2)):
            continue
        # color-7 noise cell (rule ignores it).
        for _t in range(30):
            nr = rng.randint(0, h - 1); nc = rng.randint(0, w - 1)
            if not occ[nr][nc]:
                g[nr][nc] = 7; occ[nr][nc] = True
                break
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_shapes":
        return g
    if name == "identical_shapes":
        s = [(0, 0), (0, 1), (1, 0)]
        paint_at(g, 2, 1, s, 1); paint_at(g, 6, 8, s, 2)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 1
        return g
    return g
