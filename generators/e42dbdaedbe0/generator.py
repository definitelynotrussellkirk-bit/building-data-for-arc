"""Generator for arc_puzzle_bank_eighteenth21:M123 — recolor 8-shapes by size legend.

Rule: row 0 holds a legend (e.g., [2, 4, 6] at cols 0-2). Each
8-color shape elsewhere is recolored according to its cell count:
1-cell → legend[0], 2-cell → legend[1], 3-cell → legend[2].

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend (row 0 is bg → rule's size→color lookup is
empty, all 8s stay 8), no_shapes (legend present, no 8-shapes →
rule has nothing to recolor), tied_sizes (all 8-shapes share same
size → rule maps every shape to one legend slot, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "e42dbdaedbe0"
VERSION = "2.2.0"  # guarantee all 3 distinct-size 8-components place; keep self_check gate
TASK_ID = "e42dbdaedbe0"
SUMMARY = "Row-0 legend (3 colors) + three 8-shapes of distinct sizes (1-5 cells) elsewhere; rule recolors each by its size-rank to the matching legend color."

INVARIANTS = [
    "background is 0",
    "row 0 cols 0-2 hold 3 distinct legend colors (none is 8)",
    "below row 0: exactly three 4-connected 8-shapes with distinct sizes",
    "8-shapes don't touch each other or row 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_shapes", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":            {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "row0_legend_plus_8shapes",
                          "valid": "row0_legend_plus_8shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_legend|no_shapes|tied_sizes"},
}

def _poly(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _compact_poly(k):
    """Deterministic compact fallback shape for sizes 1..5."""
    shapes = {
        1: [(0, 0)],
        2: [(0, 0), (0, 1)],
        3: [(0, 0), (0, 1), (1, 0)],
        4: [(0, 0), (0, 1), (1, 0), (1, 1)],
        5: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    }
    return shapes[k]


def _place_shapes(g, shapes, rng):
    """Place all shapes with a 1-cell moat; return False if any cannot fit."""
    h, w = len(g), len(g[0])
    placed: list[tuple[int, int, int, int]] = [(0, 0, 0, w - 1)]
    for shape in shapes:
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        positions = [(r0, c0) for r0 in range(2, h - sh + 1) for c0 in range(0, w - sw + 1)]
        rng.shuffle(positions)
        for r0, c0 in positions:
            bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb, p) for p in placed):
                continue
            paint_at(g, r0, c0, shape, 8)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            break
        else:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        size_pool = [1, 2, 3]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        size_pool = [1, 2, 3, 4, 5]
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        size_pool = [1, 2, 3, 4]
    rng = ctx.draw_rng("layout")
    legend = list(random_palette(rng, 3, exclude={8}))
    # Exactly 3 8-shapes with DISTINCT sizes (rule ranks by size -> legend slot).
    # Previous code gave each shape a bounded placement loop but silently returned
    # a partial instance when the last component failed to fit on a tight easy
    # grid. Retry the full layout, then use compact fallback polyominoes.
    sizes = rng.sample(size_pool, 3)
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        for i, c in enumerate(legend):
            g[0][i] = c
        shapes = [_poly(rng, k) for k in sizes]
        if _place_shapes(g, shapes, rng):
            return g

    g = full_grid(h, w, 0)
    for i, c in enumerate(legend):
        g[0][i] = c
    shapes = [_compact_poly(k) for k in sizes]
    if _place_shapes(g, shapes, rng):
        return g
    raise RuntimeError(f"could not place three distinct-size 8-components in {h}x{w}")


def _components4(grid, color):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the size-ranked legend task.

    The normal path must present the canonical rule with exactly three distinct
    8-components, because the output color is assigned by component-size rank.
    Missing/merged/tied-size components silently collapse the intended lesson.
    """
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs

    legend = grid[0][:3]
    if len(legend) != 3 or len(set(legend)) != 3 or any(c in (0, 8) for c in legend):
        errs.append(f"bad row-0 legend: {legend}")
    if any(grid[0][c] != 0 for c in range(3, w)):
        errs.append("row 0 has non-background cells outside legend cols 0..2")

    comps = _components4(grid, 8)
    if len(comps) != 3:
        errs.append(f"expected exactly 3 four-connected 8-components, found {len(comps)}")
    sizes = sorted(len(comp) for comp in comps)
    if len(sizes) != 3 or len(set(sizes)) != 3:
        errs.append(f"expected 3 distinct 8-component sizes, got {sizes}")
    if any(r == 0 for comp in comps for r, _ in comp):
        errs.append("8-component touches legend row")

    allowed = {0, 8, *legend}
    extra = sorted({v for row in grid for v in row if v not in allowed})
    if extra:
        errs.append(f"unexpected colors outside legend/8/background: {extra}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Row 0 is bg → rule's size→color map empty; 8s stay 8.
        g[3][2] = 8
        g[3][5] = 8; g[3][6] = 8
        g[5][2] = 8; g[6][2] = 8; g[6][3] = 8
        return g
    if name == "no_shapes":
        # Legend present but no 8-shapes → rule has nothing to recolor.
        g[0][0] = 2; g[0][1] = 4; g[0][2] = 6
        return g
    if name == "tied_sizes":
        # All 8-shapes are 1-cell → all map to legend[0]; no contrast.
        g[0][0] = 2; g[0][1] = 4; g[0][2] = 6
        g[3][2] = 8
        g[4][6] = 8
        g[6][4] = 8
        return g
    return g
