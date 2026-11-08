"""Generator for arc_additional_puzzles_21_set5:H29.

Rule: convert the nonzero mask into connected components, ranked by
descending bbox area.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, size_spread, texture.
Degenerates: equal_bboxes, single_component, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "2d5acf84dd20"
VERSION = "2.0.1"  # distinct=16: FIXED shapes/positions, only masked-away colours varied. Rule masks nonzero->1 then ranks components by bbox AREA (painting rank i from 2); canonical input is BINARY [0,1]. Now random color-1 blobs, DISTINCT bbox areas, varied count/positions.
TASK_ID = "2d5acf84dd20"
SUMMARY = "Binary [0,1] grid with separated color-1 blobs; rule masks nonzero, ranks components by descending bbox area, recolors rank i (from 2)."

INVARIANTS = [
    "input is binary (0 bg, 1 fg) like canonical",
    "nonzero components are separated by background (>=1 gap)",
    "all component bounding-box areas are distinct (unambiguous ranking)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_bboxes", "single_component", "no_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "size_spread":    {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: binary grid (only 0 and 1), has >=2 color-1 components."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    bad = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if bad:
        return [f"non-binary values found: {set(grid[r][c] for r, c in bad)}"]
    ones = set((r, c) for r in range(h) for c in range(w) if grid[r][c] == 1)
    if not ones:
        return ["no foreground (color-1) cells found"]
    visited = set()
    n_comp = 0
    for start in ones:
        if start in visited:
            continue
        n_comp += 1
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in ones and nb not in visited:
                    queue.append(nb)
    if n_comp < 2:
        return [f"expected >=2 components, got {n_comp}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 11, 13)
        n = rng_n(ctx, 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 18); w = ctx.draw_int("grid_w", 15, 18)
        n = rng_n(ctx, 4, 6)
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n = rng_n(ctx, 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used_areas: set[int] = set()
    placed = 0
    for _attempt in range(400):
        if placed >= n:
            break
        # random blob (mix of solid/outline rects and grown polyominoes) in color 1
        kind = rng.random()
        if kind < 0.5:
            bh = rng.randint(2, min(6, h - 2)); bw = rng.randint(2, min(6, w - 2))
            area = bh * bw
            if area in used_areas:
                continue
            shape = _rect_cells(bh, bw, outline=(rng.random() < 0.5))
        else:
            k = rng.randint(3, 7)
            shape = _rand_poly(rng, k)
            bh = max(r for r, _ in shape) + 1; bw = max(c for _, c in shape) + 1
            area = bh * bw
            if area in used_areas:
                continue
        # place with a 1-cell separation gap
        if bh > h or bw > w:
            continue
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        if not _free(g, r0, c0, bh, bw):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 1
        used_areas.add(area)
        placed += 1
    return g


def rng_n(ctx, lo, hi):
    return ctx.draw_int("n_components", lo, hi)


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rect_cells(bh, bw, outline):
    if outline and bh >= 2 and bw >= 2:
        return [(r, c) for r in range(bh) for c in range(bw)
                if r in (0, bh - 1) or c in (0, bw - 1)]
    return [(r, c) for r in range(bh) for c in range(bw)]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r0, c0, bh, bw, pad=1):
    h, w = len(g), len(g[0])
    for r in range(r0 - pad, r0 + bh + pad):
        for c in range(c0 - pad, c0 + bw + pad):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "equal_bboxes":
        # all components share the same bbox area → ranking by area is ambiguous
        draw_rect_outline(g, 1, 1, 3, 3, 2)
        draw_rect_outline(g, 1, 7, 3, 3, 4)
        draw_rect_outline(g, 7, 1, 3, 3, 6)
        draw_rect_outline(g, 7, 7, 3, 3, 8)
        return g
    if name == "single_component":
        # only one component → ranking has one entry, ordering trivial
        draw_rect_outline(g, 3, 3, 5, 5, 5)
        return g
    if name == "no_components":
        # empty grid → nothing to rank
        return g
    return g


def _components1(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != 1:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 1:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal-path invariant: binary components have distinct bbox areas."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errors = []
    if any(v not in (0, 1) for row in grid for v in row):
        errors.append("input is not binary 0/1")
    comps = _components1(grid)
    if len(comps) < 2:
        errors.append(f"only {len(comps)} components")
    areas = []
    for cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        areas.append((max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1))
    if len(set(areas)) != len(areas):
        errors.append("component bbox areas are not distinct")
    return errors
